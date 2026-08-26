package sentinel.trading_limits

default decision = "DENY"
default reason = "Default deny: No matching policy rule found."

decision = "ALLOW" {
    input.trade_value <= 10000
}
reason = "Auto-approved trade (value <= $10,000)." {
    input.trade_value <= 10000
}

decision = "REQUIRE_HITL" {
    input.trade_value > 10000
    input.trade_value <= 100000
}
reason = "High-value action requires human-in-the-loop approval." {
    input.trade_value > 10000
    input.trade_value <= 100000
}

decision = "DENY" {
    input.trade_value > 100000
}
reason = "Action exceeds safe limits and baseline. Autonomy degraded; action blocked." {
    input.trade_value > 100000
}
