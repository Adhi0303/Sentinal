"""
Module B: Trust Engine
======================
Maintains a persistent, evolving trust score (0.0 – 100.0) per agent.

Score is updated by behavioral signals emitted from every governance gate
in the Sentinel pipeline. It is NOT AI-generated — it is a deterministic,
weighted calculation over measurable events.

Trust decay: Inactive agents slowly drift toward a floor of 60.0.
Trust history: Every update is stored for dashboard chart rendering.

Redis keys used:
  sentinel:trust:{agent_id}           → String (float) — current score
  sentinel:trust:history:{agent_id}   → List   (JSON)  — event log (newest-first)
  sentinel:trust:weights              → Hash            — signal → delta mapping
"""

import json
import redis
from datetime import datetime, timezone

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

TRUST_KEY_PREFIX   = "sentinel:trust:"
HISTORY_KEY_PREFIX = "sentinel:trust:history:"
WEIGHTS_KEY        = "sentinel:trust:weights"

HISTORY_MAX  = 500      # max events stored per agent (LTRIM enforced)
DEFAULT_TRUST = 100.0
TRUST_MIN     = 0.0
TRUST_MAX     = 100.0

# Default weight table — every signal that any pipeline gate can emit
DEFAULT_WEIGHTS: dict[str, str] = {
    # Positive signals
    "ACTION_ALLOWED":            "0.5",
    "POLICY_PASSED":             "0.3",
    "HITL_APPROVED":             "0.2",

    # Negative signals — governance violations
    "ACTION_DENIED_POLICY":      "-5.0",
    "ACTION_DENIED_VELOCITY":    "-4.0",
    "PROMPT_INJECTION_DETECTED": "-10.0",
    "CAPABILITY_VIOLATION":      "-15.0",
    "HITL_REJECTED":             "-8.0",
    "CYCLE_DETECTED":            "-12.0",
    "SAGA_ROLLBACK_TRIGGERED":   "-6.0",
    "DUPLICATE_ATTEMPT":         "-3.0",

    # Negative signals — behavioral anomalies (Module D)
    "BEHAVIOR_ANOMALY_MILD":     "-2.0",
    "BEHAVIOR_ANOMALY_SEVERE":   "-8.0",
    "VELOCITY_EVASION_DETECTED": "-10.0",

    # Emergency
    "KILL_SWITCH_TRIGGERED":     "-20.0",
}


def _ensure_weights():
    """Load defaults into Redis if not yet initialized (idempotent)."""
    if not redis_client.exists(WEIGHTS_KEY):
        redis_client.hset(WEIGHTS_KEY, mapping=DEFAULT_WEIGHTS)
        print("[TRUST] Default weight table initialized in Redis")


def initialize_trust(agent_id: str):
    """
    Set trust to 100.0 for a newly registered agent.
    Called immediately after agent_registry.register_agent().
    """
    _ensure_weights()
    redis_client.set(f"{TRUST_KEY_PREFIX}{agent_id}", DEFAULT_TRUST)
    print(f"[TRUST] Initialized trust=100.0 for agent '{agent_id}'")


def get_trust(agent_id: str) -> float:
    """
    Get current trust score.
    Returns DEFAULT_TRUST (100.0) if agent has not been tracked yet.
    """
    val = redis_client.get(f"{TRUST_KEY_PREFIX}{agent_id}")
    return float(val) if val is not None else DEFAULT_TRUST


def set_trust(agent_id: str, value: float):
    """
    Force-set trust to a specific value.
    Used by admin recovery flow (e.g. releasing a quarantined agent resets to 50).
    Always clamps value to [TRUST_MIN, TRUST_MAX].
    """
    clamped = max(TRUST_MIN, min(TRUST_MAX, value))
    redis_client.set(f"{TRUST_KEY_PREFIX}{agent_id}", clamped)
    print(f"[TRUST] Trust for '{agent_id}' manually set to {clamped:.1f}")


def update_trust(agent_id: str, signal_event: str, reason: str = "") -> dict:
    """
    Apply a trust signal delta. Updates score and records history.

    Args:
        agent_id:     The agent whose trust to update.
        signal_event: One of the keys in the weight table (e.g. "ACTION_DENIED_POLICY").
        reason:       Human-readable explanation for the audit log.

    Returns:
        {
          agent_id, signal_event, delta, old_score, new_score,
          autonomy_changed, old_tier, new_tier
        }
    """
    _ensure_weights()

    raw_delta = redis_client.hget(WEIGHTS_KEY, signal_event)
    if raw_delta is None:
        print(f"[TRUST] Unknown signal '{signal_event}' — no delta applied, skipping")
        return {
            "agent_id":     agent_id,
            "signal_event": signal_event,
            "delta":        0,
            "skipped":      True,
            "reason":       f"Signal '{signal_event}' not found in weight table",
        }

    delta     = float(raw_delta)
    old_score = get_trust(agent_id)
    new_score = max(TRUST_MIN, min(TRUST_MAX, old_score + delta))

    # Persist updated score
    redis_client.set(f"{TRUST_KEY_PREFIX}{agent_id}", new_score)

    # Detect autonomy tier change (local import avoids circular at module level)
    from autonomy_engine import get_tier_for_score
    old_tier = get_tier_for_score(old_score)
    new_tier = get_tier_for_score(new_score)
    autonomy_changed = old_tier != new_tier

    # Record to history (newest-first list)
    event = {
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "signal_event": signal_event,
        "delta":        delta,
        "old_score":    old_score,
        "new_score":    new_score,
        "reason":       reason,
    }
    hist_key = f"{HISTORY_KEY_PREFIX}{agent_id}"
    redis_client.lpush(hist_key, json.dumps(event))
    redis_client.ltrim(hist_key, 0, HISTORY_MAX - 1)

    print(f"[TRUST] '{agent_id}': {old_score:.1f} -> {new_score:.1f} (signal={signal_event}, delta={delta:+.1f})")
    if autonomy_changed:
        print(f"[TRUST] ⚠️  Autonomy tier changed: {old_tier} → {new_tier} for '{agent_id}'")

    return {
        "agent_id":         agent_id,
        "signal_event":     signal_event,
        "delta":            delta,
        "old_score":        old_score,
        "new_score":        new_score,
        "autonomy_changed": autonomy_changed,
        "old_tier":         old_tier,
        "new_tier":         new_tier,
    }


def get_trust_history(agent_id: str, limit: int = 100) -> list:
    """
    Return trust event history for an agent.
    Returned newest-first (index 0 = most recent), suitable for chart rendering.
    """
    raw = redis_client.lrange(f"{HISTORY_KEY_PREFIX}{agent_id}", 0, limit - 1)
    return [json.loads(e) for e in raw]


def get_trust_summary(agent_id: str) -> dict:
    """
    Return a concise trust summary for dashboard display.
    Includes score, tier, trend (last 5 deltas), and violation count.
    """
    from autonomy_engine import get_tier_for_score

    score   = get_trust(agent_id)
    tier    = get_tier_for_score(score)
    history = get_trust_history(agent_id, limit=5)

    recent_deltas  = [h["delta"] for h in history]
    trend          = "STABLE"
    if recent_deltas:
        avg_delta = sum(recent_deltas) / len(recent_deltas)
        if avg_delta > 0.1:
            trend = "IMPROVING"
        elif avg_delta < -1.0:
            trend = "DECLINING"

    violation_events = {
        "ACTION_DENIED_POLICY", "ACTION_DENIED_VELOCITY", "PROMPT_INJECTION_DETECTED",
        "CAPABILITY_VIOLATION", "HITL_REJECTED", "CYCLE_DETECTED",
        "VELOCITY_EVASION_DETECTED", "KILL_SWITCH_TRIGGERED",
    }
    all_history    = get_trust_history(agent_id, limit=100)
    violation_count = sum(1 for h in all_history if h["signal_event"] in violation_events)

    return {
        "agent_id":        agent_id,
        "trust_score":     score,
        "autonomy_tier":   tier,
        "trend":           trend,
        "violation_count": violation_count,
        "recent_events":   history,
    }


def get_weights() -> dict:
    """Return the current signal weight table."""
    _ensure_weights()
    return {k: float(v) for k, v in redis_client.hgetall(WEIGHTS_KEY).items()}


def update_weights(updates: dict) -> dict:
    """Update signal weights in Redis (admin operation)."""
    _ensure_weights()
    redis_client.hset(WEIGHTS_KEY, mapping={k: str(v) for k, v in updates.items()})
    print(f"[TRUST] Weight table updated: {list(updates.keys())}")
    return get_weights()
