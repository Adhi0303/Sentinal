package sentinel.razorpay_payments

# ─────────────────────────────────────────────────────────────────────────────
# Sentinel Razorpay — Payment Capture Policy
# Governs all PAYMENT_CAPTURE action types.
# Razorpay allows capture up to 5 days (120 hours) after authorization.
# ─────────────────────────────────────────────────────────────────────────────

default decision = "DENY"
default reason   = "Default deny: No matching payment capture policy rule."

# ── Hard DENY rules ───────────────────────────────────────────────────────────

deny_reasons[r] {
    input.payment_age_hours > 120
    r := sprintf("Payment authorization expired: %.1f hours old (max 120 hours / 5 days).", [input.payment_age_hours])
}

deny_reasons[r] {
    input.already_captured == true
    r := "This payment has already been captured. Duplicate capture blocked."
}

deny_reasons[r] {
    input.payment_status == "REFUNDED"
    r := "Cannot capture a payment that has already been refunded."
}

deny_reasons[r] {
    input.payment_status == "FAILED"
    r := "Cannot capture a failed payment."
}

deny_reasons[r] {
    input.amount > input.authorized_amount
    r := sprintf("Capture amount (%.2f) exceeds the authorized amount (%.2f).", [input.amount, input.authorized_amount])
}

# ── Require HITL rules ────────────────────────────────────────────────────────

hitl_reasons[r] {
    input.payment_age_hours > 96
    input.payment_age_hours <= 120
    count(deny_reasons) == 0
    r := sprintf("Payment is %.1f hours old — close to expiry. Human confirmation required.", [input.payment_age_hours])
}

hitl_reasons[r] {
    input.amount > 100000
    count(deny_reasons) == 0
    r := sprintf("Large capture amount (%.2f) requires human approval.", [input.amount])
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
reason = "Payment capture approved: all policy checks passed." {
    count(deny_reasons) == 0
    count(hitl_reasons) == 0
}
