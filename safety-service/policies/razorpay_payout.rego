package sentinel.razorpay_payout

# ─────────────────────────────────────────────────────────────────────────────
# Sentinel Razorpay — Payout Policy
# Governs all PAYOUT action types (merchant settlements, vendor payouts).
# ─────────────────────────────────────────────────────────────────────────────

default decision = "DENY"
default reason   = "Default deny: No matching payout policy rule."

# ── Hard DENY rules ───────────────────────────────────────────────────────────

deny_reasons[r] {
    input.destination_verified != true
    r := "Payout destination has not been verified. Unverified payouts are blocked."
}

deny_reasons[r] {
    input.action == "modify_payout_account"
    r := "Payout account modification is a privileged action — blocked for autonomous agents."
}

deny_reasons[r] {
    input.trust_score < 40
    r := sprintf("Agent trust score (%.1f) is below the minimum threshold (40) for payout actions.", [input.trust_score])
}

deny_reasons[r] {
    input.amount > input.agent_limit
    r := sprintf("Payout amount (%.2f) exceeds agent per-transaction limit (%.2f).", [input.amount, input.agent_limit])
}

# ── Require HITL rules ────────────────────────────────────────────────────────

hitl_reasons[r] {
    input.amount > 500000
    input.dual_auth_provided != true
    count(deny_reasons) == 0
    r := sprintf("Payout amount (%.2f) exceeds ₹5,00,000 — dual authorisation required.", [input.amount])
}

hitl_reasons[r] {
    input.trust_score < 70
    input.trust_score >= 40
    count(deny_reasons) == 0
    r := sprintf("Agent trust score (%.1f) in HITL zone — payout requires human review.", [input.trust_score])
}

# ── Final decision ────────────────────────────────────────────────────────────

decision = "DENY" {
    count(deny_reasons) > 0
}
reason = r {
    count(deny_reasons) > 0
    r := concat("; ", deny_reasons)
}

decision = "REQUIRE_HITL" {
    count(deny_reasons) == 0
    count(hitl_reasons) > 0
}
reason = r {
    count(deny_reasons) == 0
    count(hitl_reasons) > 0
    r := concat("; ", hitl_reasons)
}

decision = "ALLOW" {
    count(deny_reasons) == 0
    count(hitl_reasons) == 0
}
reason = "Payout approved: all policy checks passed." {
    count(deny_reasons) == 0
    count(hitl_reasons) == 0
}
