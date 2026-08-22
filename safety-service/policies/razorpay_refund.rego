package sentinel.razorpay_refund

# ─────────────────────────────────────────────────────────────────────────────
# Sentinel Razorpay — Refund Policy
# Governs all REFUND action types in the Razorpay merchant context.
# ─────────────────────────────────────────────────────────────────────────────

default decision = "DENY"
default reason   = "Default deny: No matching refund policy rule."

# ── Hard DENY rules ───────────────────────────────────────────────────────────

deny_reasons[r] {
    input.amount > input.agent_limit
    r := sprintf("Refund amount (%.2f) exceeds agent per-transaction limit (%.2f).", [input.amount, input.agent_limit])
}

deny_reasons[r] {
    input.trust_score < 40
    r := sprintf("Agent trust score (%.1f) is below the minimum threshold (40) for autonomous refunds.", [input.trust_score])
}

deny_reasons[r] {
    input.refund_destination != input.original_payment_source
    r := "Refund destination does not match the original payment source. Possible fraud."
}

deny_reasons[r] {
    input.already_refunded == true
    r := "This payment has already been fully refunded. Duplicate refund blocked."
}

# ── Require HITL rules ────────────────────────────────────────────────────────

hitl_reasons[r] {
    input.amount > 10000
    count(deny_reasons) == 0
    r := sprintf("Refund amount (%.2f) exceeds ₹10,000 — human approval required.", [input.amount])
}

hitl_reasons[r] {
    input.trust_score < 60
    input.trust_score >= 40
    count(deny_reasons) == 0
    r := sprintf("Agent trust score (%.1f) is in the cautious zone (40–60) — human review required.", [input.trust_score])
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
reason = "Refund approved: all policy checks passed." {
    count(deny_reasons) == 0
    count(hitl_reasons) == 0
}
