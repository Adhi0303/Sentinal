"""
Module D: Behavior Monitor
==========================
Detects behavioral deviation from an agent's established baseline.
This is Sentinel's "early warning system" — it catches subtle drift
*before* a catastrophic transaction happens.

Architecture:
  D.1 — Baseline Profiler: builds a statistical fingerprint from the
         agent's first 10+ actions (avg amount, velocity, tool mix, etc.)
  D.2 — Deviation Detector: scores every new action against the baseline
         across 7 flags, auto-emits trust signals on anomalies, and returns
         a risk_boost for the OPA gate.

Redis keys used:
  sentinel:behavior:baseline:{agent_id}   -> Hash (JSON blob) — baseline stats
  sentinel:behavior:window:{agent_id}     -> List (JSON) — rolling 50-action window
  sentinel:behavior:deviation:{agent_id}  -> String (JSON) — latest deviation report
  sentinel:behavior:timeline:{agent_id}   -> List (JSON) — deviation scores over time
"""

import json
import math
import redis
from datetime import datetime, timezone
from typing import Optional

# Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

BASELINE_KEY  = "sentinel:behavior:baseline:"
WINDOW_KEY    = "sentinel:behavior:window:"
DEVIATION_KEY = "sentinel:behavior:deviation:"
TIMELINE_KEY  = "sentinel:behavior:timeline:"

WINDOW_MAX    = 50    # rolling action window size
TIMELINE_MAX  = 200   # max deviation history entries per agent
BASELINE_MIN  = 10    # actions needed before baseline is locked

# Deviation flag weights — sum gives deviation_score (0-100)
FLAG_WEIGHTS = {
    "amount_spike":        15,   # amount > avg x 1.5
    "amount_extreme":      35,   # amount > avg x 3.0
    "velocity_surge":      30,   # actions/min > baseline x 2
    "tool_drift":          10,   # tool not in agent's historical top-5
    "depth_increase":      25,   # call_depth > baseline_avg + 2
    "near_limit_cluster":  40,   # 3+ consecutive amounts >= 90% of tx_limit
    "new_account_target":  10,   # account_id not in agent's common_accounts
}

# Score thresholds to severity label
SEVERITY_LEVELS = [
    (60, "SEVERE"),
    (25, "MODERATE"),
    (10, "MILD"),
    (0,  "NORMAL"),
]


# ── D.1: Baseline Profiler ────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_action(
    agent_id: str,
    amount: float,
    tool_name: str,
    account_id: str,
    call_depth: int = 1,
) -> None:
    """
    Record a single agent action into the rolling window.
    Triggers a baseline recompute every time sample_size >= BASELINE_MIN.
    """
    entry = json.dumps({
        "timestamp":  _now_iso(),
        "amount":     amount,
        "tool_name":  tool_name,
        "account_id": account_id,
        "call_depth": call_depth,
    })
    key = f"{WINDOW_KEY}{agent_id}"
    redis_client.lpush(key, entry)
    redis_client.ltrim(key, 0, WINDOW_MAX - 1)   # keep newest 50

    # Recompute baseline if we have enough samples
    window_len = redis_client.llen(key)
    if window_len >= BASELINE_MIN:
        compute_baseline(agent_id)


def _stddev(values: list) -> float:
    """Population standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def compute_baseline(agent_id: str) -> dict:
    """
    Read the rolling action window and calculate statistical baseline.
    Stored at sentinel:behavior:baseline:{agent_id}.
    """
    raw_window = redis_client.lrange(f"{WINDOW_KEY}{agent_id}", 0, -1)
    actions = [json.loads(r) for r in raw_window]

    if not actions:
        return {}

    amounts    = [a["amount"]     for a in actions]
    depths     = [a["call_depth"] for a in actions]
    tools      = [a["tool_name"]  for a in actions]
    accounts   = [a["account_id"] for a in actions]
    timestamps = [a["timestamp"]  for a in actions]

    # Tool frequency map
    tool_counts: dict = {}
    for t in tools:
        tool_counts[t] = tool_counts.get(t, 0) + 1
    total = len(tools)
    tool_frequency = {t: round(c / total, 3) for t, c in tool_counts.items()}

    # Top-5 tools by frequency
    top_tools = sorted(tool_frequency, key=lambda k: tool_frequency[k], reverse=True)[:5]

    # Common accounts (top 10)
    acc_counts: dict = {}
    for a in accounts:
        acc_counts[a] = acc_counts.get(a, 0) + 1
    common_accounts = sorted(acc_counts, key=lambda k: acc_counts[k], reverse=True)[:10]

    # Actions per minute from timestamp spread
    try:
        sorted_ts = sorted(timestamps)
        first = datetime.fromisoformat(sorted_ts[-1])   # newest
        last  = datetime.fromisoformat(sorted_ts[0])    # oldest
        span_minutes = max((first - last).total_seconds() / 60.0, 1.0)
        actions_per_minute = round(len(actions) / span_minutes, 3)
    except Exception:
        actions_per_minute = 1.0

    baseline = {
        "avg_amount":             round(sum(amounts) / len(amounts), 2),
        "amount_stddev":          round(_stddev(amounts), 2),
        "tool_frequency":         tool_frequency,
        "top_tools":              top_tools,
        "avg_call_depth":         round(sum(depths) / len(depths), 2),
        "avg_actions_per_minute": actions_per_minute,
        "common_accounts":        common_accounts,
        "baseline_locked":        True,
        "baseline_sample_size":   len(actions),
        "last_computed":          _now_iso(),
    }

    redis_client.set(f"{BASELINE_KEY}{agent_id}", json.dumps(baseline))
    return baseline


def get_baseline(agent_id: str) -> Optional[dict]:
    """Return the current baseline, or None if not yet established."""
    raw = redis_client.get(f"{BASELINE_KEY}{agent_id}")
    if not raw:
        return None
    b = json.loads(raw)
    if not b.get("baseline_locked"):
        return None
    return b


def get_window_size(agent_id: str) -> int:
    """Return current rolling window size (number of recorded actions)."""
    return redis_client.llen(f"{WINDOW_KEY}{agent_id}")


# ── D.2: Deviation Detector ───────────────────────────────────────────────────

def _get_recent_amounts(agent_id: str, n: int = 3) -> list:
    """Get the n most recent transaction amounts from the action window."""
    raw = redis_client.lrange(f"{WINDOW_KEY}{agent_id}", 0, n - 1)
    return [json.loads(r)["amount"] for r in raw]


def _get_recent_velocity(agent_id: str, window_seconds: int = 60) -> float:
    """Count how many actions occurred in the last window_seconds seconds."""
    raw = redis_client.lrange(f"{WINDOW_KEY}{agent_id}", 0, -1)
    now = datetime.now(timezone.utc)
    count = 0
    for r in raw:
        action = json.loads(r)
        try:
            ts = datetime.fromisoformat(action["timestamp"])
            if (now - ts).total_seconds() <= window_seconds:
                count += 1
        except Exception:
            pass
    return count / (window_seconds / 60.0)   # actions per minute


def _severity_label(score: int) -> str:
    for threshold, label in SEVERITY_LEVELS:
        if score >= threshold:
            return label
    return "NORMAL"


def check_deviation(
    agent_id: str,
    amount: float,
    tool_name: str,
    account_id: str,
    call_depth: int = 1,
    tx_limit: float = 10000.0,
) -> dict:
    """
    Main entry point — called by the SDK on every agent action.

    Steps:
      1. Record action into rolling window (also recomputes baseline if ready)
      2. If baseline not locked, return early — no signals emitted
      3. Run all 7 deviation flag checks
      4. Sum deviation_score (cap at 100)
      5. Auto-emit trust signal if score >= 25
      6. Store latest deviation report in Redis
      7. Append score to timeline list
      8. Return full deviation report
    """
    # Step 1: Record action (triggers baseline recompute if window >= 10)
    record_action(agent_id, amount, tool_name, account_id, call_depth)

    # Step 2: Baseline check
    baseline = get_baseline(agent_id)
    if baseline is None:
        window_size = get_window_size(agent_id)
        return {
            "agent_id":              agent_id,
            "baseline_locked":       False,
            "samples_needed":        max(0, BASELINE_MIN - window_size),
            "window_size":           window_size,
            "deviation_score":       0,
            "severity":              "NORMAL",
            "flags":                 [],
            "trust_signal_emitted":  None,
            "trust_delta":           0.0,
            "risk_boost":            0,
        }

    avg_amount   = baseline["avg_amount"]
    avg_depth    = baseline["avg_call_depth"]
    top_tools    = baseline.get("top_tools", [])
    common_accs  = baseline.get("common_accounts", [])
    baseline_apm = baseline.get("avg_actions_per_minute", 1.0)

    # Step 3: Run all 7 flags
    flags:   list = []
    details: dict = {}
    score   = 0

    # Flag 1a: amount_extreme (takes priority over amount_spike)
    if avg_amount > 0:
        extreme_threshold = avg_amount * 3.0
        spike_threshold   = avg_amount * 1.5
        if amount > extreme_threshold:
            flags.append("amount_extreme")
            score += FLAG_WEIGHTS["amount_extreme"]
            details["amount_extreme"] = {
                "current":      amount,
                "baseline_avg": avg_amount,
                "threshold":    round(extreme_threshold, 2),
                "ratio":        f"{round(amount / avg_amount, 1)}x",
            }
        elif amount > spike_threshold:
            flags.append("amount_spike")
            score += FLAG_WEIGHTS["amount_spike"]
            details["amount_spike"] = {
                "current":      amount,
                "baseline_avg": avg_amount,
                "threshold":    round(spike_threshold, 2),
                "ratio":        f"{round(amount / avg_amount, 1)}x",
            }

    # Flag 2: velocity_surge
    current_apm = _get_recent_velocity(agent_id, window_seconds=60)
    velocity_threshold = baseline_apm * 2.0
    if baseline_apm > 0 and current_apm > velocity_threshold:
        flags.append("velocity_surge")
        score += FLAG_WEIGHTS["velocity_surge"]
        details["velocity_surge"] = {
            "current_apm":   round(current_apm, 2),
            "baseline_apm":  baseline_apm,
            "threshold_apm": round(velocity_threshold, 2),
        }

    # Flag 3: tool_drift
    if top_tools and tool_name not in top_tools:
        flags.append("tool_drift")
        score += FLAG_WEIGHTS["tool_drift"]
        details["tool_drift"] = {
            "current_tool":        tool_name,
            "historical_top_tools": top_tools,
        }

    # Flag 4: depth_increase
    depth_threshold = avg_depth + 2.0
    if call_depth > depth_threshold:
        flags.append("depth_increase")
        score += FLAG_WEIGHTS["depth_increase"]
        details["depth_increase"] = {
            "current_depth": call_depth,
            "baseline_avg":  avg_depth,
            "threshold":     depth_threshold,
        }

    # Flag 5: near_limit_cluster (3+ consecutive amounts >= 90% of tx_limit)
    near_limit_threshold = tx_limit * 0.90
    recent_amounts = _get_recent_amounts(agent_id, n=3)
    if len(recent_amounts) >= 3 and all(a >= near_limit_threshold for a in recent_amounts):
        flags.append("near_limit_cluster")
        score += FLAG_WEIGHTS["near_limit_cluster"]
        details["near_limit_cluster"] = {
            "tx_limit":             tx_limit,
            "near_limit_threshold": near_limit_threshold,
            "last_3_amounts":       recent_amounts,
        }

    # Flag 6: new_account_target
    if common_accs and account_id not in common_accs:
        flags.append("new_account_target")
        score += FLAG_WEIGHTS["new_account_target"]
        details["new_account_target"] = {
            "current_account": account_id,
            "common_accounts": common_accs,
        }

    # Step 4: Cap score
    score = min(score, 100)
    severity = _severity_label(score)

    # Step 5: Auto-emit trust signal
    trust_signal: Optional[str] = None
    trust_delta  = 0.0
    risk_boost   = 0

    if score >= 60:
        trust_signal = "BEHAVIOR_ANOMALY_SEVERE"
        risk_boost   = 20
    elif score >= 25:
        if "near_limit_cluster" in flags:
            trust_signal = "VELOCITY_EVASION_DETECTED"
        else:
            trust_signal = "BEHAVIOR_ANOMALY_MILD"

    if trust_signal:
        try:
            from trust_engine import update_trust
            result = update_trust(
                agent_id, trust_signal,
                f"Behavior deviation detected: {', '.join(flags)}"
            )
            trust_delta = result.get("delta", 0.0)
        except Exception as e:
            print(f"[BEHAVIOR MONITOR] Warning: could not emit trust signal: {e}")

    # Step 6: Store deviation report
    report = {
        "agent_id":             agent_id,
        "timestamp":            _now_iso(),
        "baseline_locked":      True,
        "deviation_score":      score,
        "severity":             severity,
        "flags":                flags,
        "details":              details,
        "trust_signal_emitted": trust_signal,
        "trust_delta":          trust_delta,
        "risk_boost":           risk_boost,
    }
    redis_client.set(f"{DEVIATION_KEY}{agent_id}", json.dumps(report))

    # Step 7: Append to timeline
    timeline_entry = json.dumps({
        "timestamp":       _now_iso(),
        "deviation_score": score,
        "severity":        severity,
        "flags":           flags,
    })
    redis_client.lpush(f"{TIMELINE_KEY}{agent_id}", timeline_entry)
    redis_client.ltrim(f"{TIMELINE_KEY}{agent_id}", 0, TIMELINE_MAX - 1)

    print(f"[BEHAVIOR MONITOR] agent={agent_id} | score={score} ({severity}) | flags={flags} | signal={trust_signal}")
    return report


# ── Helper getters (used by API endpoints) ────────────────────────────────────

def get_latest_deviation(agent_id: str) -> Optional[dict]:
    """Return the most recent deviation report for an agent."""
    raw = redis_client.get(f"{DEVIATION_KEY}{agent_id}")
    return json.loads(raw) if raw else None


def get_deviation_timeline(agent_id: str, limit: int = 100) -> list:
    """Return deviation score history (newest-first) for chart rendering."""
    raw = redis_client.lrange(f"{TIMELINE_KEY}{agent_id}", 0, limit - 1)
    return [json.loads(r) for r in raw]
