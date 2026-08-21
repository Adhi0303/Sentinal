"""
Module C: Autonomy Engine
=========================
Maps a trust score + action risk level → an autonomy tier decision.

Evaluated dynamically on every single agent action — not just at registration.
This means an agent that has been behaving well can earn more autonomy,
and one that has been violating policies will automatically face tighter controls.

Tiers (configurable via Redis — defaults below):
  FULL       → trust >= 90   Normal pipeline. No extra friction.
  BOUNDED    → trust 70-89   Velocity limits tightened 50%. Tx limit capped at 80%.
  HITL       → trust 40-69   Every action escalated to human approval queue.
  QUARANTINE → trust < 40    All actions blocked. Agent status auto-set to QUARANTINED.

Redis key:
  sentinel:autonomy:tiers → Hash (tier_name → min_trust_score)
"""

import redis
from trust_engine import get_trust

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

TIERS_KEY = "sentinel:autonomy:tiers"

# Default thresholds — minimum trust score to be in each tier
DEFAULT_TIERS: dict[str, str] = {
    "FULL":       "90",
    "BOUNDED":    "70",
    "HITL":       "40",
    "QUARANTINE": "0",
}


def _ensure_tiers():
    """Load tier defaults into Redis if not yet initialized (idempotent)."""
    if not redis_client.exists(TIERS_KEY):
        redis_client.hset(TIERS_KEY, mapping=DEFAULT_TIERS)
        print("[AUTONOMY] Default tier thresholds initialized in Redis")


def get_tier_for_score(trust_score: float) -> str:
    """
    Pure function: maps a trust score to a tier name.
    Importable by trust_engine.py without causing circular imports.

    Args:
        trust_score: Float in range [0.0, 100.0]

    Returns:
        One of: "FULL" | "BOUNDED" | "HITL" | "QUARANTINE"
    """
    _ensure_tiers()
    thresholds = {k: float(v) for k, v in redis_client.hgetall(TIERS_KEY).items()}

    if trust_score >= thresholds.get("FULL", 90):
        return "FULL"
    if trust_score >= thresholds.get("BOUNDED", 70):
        return "BOUNDED"
    if trust_score >= thresholds.get("HITL", 40):
        return "HITL"
    return "QUARANTINE"


def get_autonomy_decision(agent_id: str, risk_score: int = 0) -> dict:
    """
    Main decision function. Called per-action by the Sentinel SDK.

    Combines trust score (persistent history) with the action's risk score
    (computed in-flight by risk_scorer.py) to produce a final autonomy decision.

    Args:
        agent_id:   Agent making the request.
        risk_score: 0–100 risk score from the risk scoring gate.

    Returns:
        {
            agent_id, trust_score, risk_score, tier,
            requires_hitl: bool,
            blocked: bool,
            limits_override: dict,
            reason: str
        }
    """
    _ensure_tiers()
    trust = get_trust(agent_id)
    tier  = get_tier_for_score(trust)

    decision = {
        "agent_id":        agent_id,
        "trust_score":     trust,
        "risk_score":      risk_score,
        "tier":            tier,
        "requires_hitl":   False,
        "blocked":         False,
        "limits_override": {},
        "reason":          "",
    }

    if tier == "QUARANTINE":
        # Hard block — agent must be recovered by admin before any actions
        decision["blocked"] = True
        decision["reason"]  = (
            f"Agent quarantined: trust score {trust:.1f} is below the "
            f"QUARANTINE threshold. All actions blocked pending admin review."
        )

    elif tier == "HITL":
        # Every action requires human approval regardless of risk score
        decision["requires_hitl"] = True
        decision["reason"]        = (
            f"Agent operating in HITL mode (trust={trust:.1f}). "
            f"Every action requires human approval."
        )

    elif tier == "BOUNDED":
        # Tighter limits applied. High-risk actions also escalate to HITL.
        decision["limits_override"] = {
            "amount_multiplier":   0.80,   # 80% of normal per-tx limit
            "velocity_multiplier": 0.50,   # 50% of normal velocity limit
        }
        if risk_score > 50:
            # Even a BOUNDED agent can't self-approve high-risk actions
            decision["requires_hitl"] = True
            decision["reason"]        = (
                f"BOUNDED agent (trust={trust:.1f}) + elevated action risk ({risk_score}/100). "
                f"Escalating to HITL."
            )
        else:
            decision["reason"] = (
                f"BOUNDED mode: trust={trust:.1f}. "
                f"Tighter velocity/amount limits applied."
            )

    else:  # FULL
        decision["reason"] = (
            f"Full autonomy: trust={trust:.1f}, risk={risk_score}/100. "
            f"Normal pipeline applies."
        )

    print(
        f"[AUTONOMY] '{agent_id}': tier={tier} | trust={trust:.1f} | "
        f"risk={risk_score} | hitl={decision['requires_hitl']} | blocked={decision['blocked']}"
    )
    return decision


def get_tiers_config() -> dict:
    """Return current tier threshold configuration."""
    _ensure_tiers()
    return {k: float(v) for k, v in redis_client.hgetall(TIERS_KEY).items()}


def update_tiers_config(updates: dict) -> dict:
    """
    Update tier thresholds (admin operation).
    Example: { "BOUNDED": 75, "HITL": 45 }
    """
    _ensure_tiers()
    redis_client.hset(TIERS_KEY, mapping={k: str(v) for k, v in updates.items()})
    print(f"[AUTONOMY] Tier thresholds updated: {updates}")
    return get_tiers_config()


def get_fleet_tier_distribution() -> dict:
    """
    Return count of active agents in each tier.
    Used by the dashboard overview KPI strip.
    """
    from agent_registry import list_agents

    agents = list_agents(status="ACTIVE")
    distribution = {"FULL": 0, "BOUNDED": 0, "HITL": 0, "QUARANTINE": 0}

    for agent in agents:
        tier = get_tier_for_score(get_trust(agent["agent_id"]))
        distribution[tier] = distribution.get(tier, 0) + 1

    return distribution
