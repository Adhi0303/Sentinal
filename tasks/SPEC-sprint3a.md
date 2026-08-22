# Spec: Sprint 3A — Sentinel SDK Rewiring + OPA Razorpay Policies + Kill Switch Trust Wiring

> **Modules covered:** 8, 4, 6
> **Priority:** CRITICAL PATH — every demo scene depends on these
> **Date:** 2026-08-22

---

## Objective

Right now, Sentinel has a world-class observability layer (Registry, Trust Engine, Autonomy Engine, Behavior Monitor). But the enforcement layer is disconnected: sentinel_sdk.py runs its 6-gate pipeline without knowing anything about trust scores, autonomy tiers, or behavior anomalies.

Sprint 3A closes this gap:
1. Every SDK action first checks the registry, autonomy tier, and behavior monitor, and emits a trust signal on every gate outcome.
2. Razorpay-specific OPA policies replace the AmEx-era Rego rules.
3. Kill switch and quarantine are wired to the trust engine.

---

## Assumptions

1. safety-service runs on port 8001; mock-banking-api on port 8000
2. Redis is running on localhost:6379
3. All 4 Layer 0 modules (A/B/C/D) are fully operational
4. OPA binary is installed at safety-service/bin/opa
5. agents-fleet/sentinel_sdk.py is the ONLY entry point for agent actions
6. GROQ_API_KEY is already set in agents-fleet/.env

---

## Files Touched

agents-fleet/
  sentinel_sdk.py          <- MODIFY: add 4 new gates

safety-service/
  main.py                  <- MODIFY: /killswitch/release + capability check
  kill_switch.py           <- MODIFY: wire quarantine/release to trust engine
  policies/
    razorpay_refund.rego   <- NEW
    razorpay_payout.rego   <- NEW
    razorpay_payments.rego <- NEW

tasks/
  SPEC-sprint3a.md         <- THIS FILE
  plan.md                  <- next step
  todo.md                  <- task checklist

---

## Module 8: SDK Gate Changes

### Gate 0.1 - Registry Existence Check (runs FIRST)
- GET /api/v1/agents/{agent_id}
- If 404 -> DENY + emit CAPABILITY_VIOLATION
- If status = SUSPENDED -> DENY
- If status = QUARANTINED -> DENY

### Gate 0.2 - Autonomy Decision
- GET /api/v1/autonomy/{agent_id}
- QUARANTINE tier -> DENY immediately
- HITL tier -> force REQUIRE_HITL regardless of OPA risk score
- BOUNDED tier -> apply limits_override to velocity gate

### Gate 0.3 - Behavior Deviation Hook
- POST /api/v1/behavior/{agent_id}/check
- If deviation_score > 60 -> add +20 to risk_score

### Gate X - Trust Signal on Every Outcome

| Gate Outcome          | Signal                    |
|-----------------------|---------------------------|
| Prompt BLOCKED        | PROMPT_INJECTION_DETECTED |
| Velocity DENIED       | ACTION_DENIED_VELOCITY    |
| Risk -> HITL          | HIGH_RISK_ESCALATED       |
| OPA DENIED            | ACTION_DENIED_POLICY      |
| Capability violation  | CAPABILITY_VIOLATION      |
| HITL approved         | HITL_APPROVED             |
| HITL rejected         | HITL_REJECTED             |
| Bank SUCCESS          | ACTION_ALLOWED            |

Trust signal emit pattern (fire-and-forget, never fatal):
    def _emit_trust_signal(agent_id, signal_event, reason):
        try:
            requests.post(f"{SAFETY_SERVICE_URL}/api/v1/trust/{agent_id}/signal",
                json={"signal_event": signal_event, "reason": reason}, timeout=2)
        except Exception:
            pass

---

## Module 4: Razorpay OPA Rego Policies

razorpay_refund.rego (action_type = REFUND):
  DENY if amount > agent_limit
  DENY if trust_score < 40
  DENY if refund_destination != original_payment_source
  REQUIRE_HITL if amount > 10000

razorpay_payout.rego (action_type = PAYOUT):
  DENY if destination_verified != true
  DENY if action == modify_payout_account
  REQUIRE_HITL if amount > 500000

razorpay_payments.rego (action_type = PAYMENT_CAPTURE):
  DENY if payment_age_hours > 120
  DENY if already_captured == true

Capability Check in main.py (before OPA):
  Load agent from registry
  If action_type not in agent[allowed_tools] -> DENY + emit CAPABILITY_VIOLATION

policy_file_map update:
  REFUND          -> razorpay_refund.rego
  PAYOUT          -> razorpay_payout.rego
  PAYMENT_CAPTURE -> razorpay_payments.rego
  WIRE_TRANSFER   -> trading_limits.rego (keep existing)

---

## Module 6: Kill Switch Trust Wiring

kill_switch.py - quarantine_agent():
  After quarantine state written to Redis:
  POST /api/v1/trust/{agent_id}/signal with KILL_SWITCH_TRIGGERED (-20)

main.py - /killswitch/release:
  After release:
  trust_engine.set_trust(agent_id, 50.0)  <- NOT 100, agent must rebuild trust
  Log AGENT_RECOVERED audit event

---

## Success Criteria

1. execute_governed_tool("fake_id", ...) returns DENY "Unregistered agent"
2. After trust drops to 55 (HITL zone), low-risk action still returns REQUIRE_HITL
3. 3x near-limit refunds trigger VELOCITY_EVASION_DETECTED behavior signal
4. REFUND with amount=12001 returns REQUIRE_HITL from razorpay_refund.rego
5. quarantine_agent("x") creates trust history entry KILL_SWITCH_TRIGGERED -20
6. /killswitch/release for agent with trust=22 -> trust becomes exactly 50.0
7. Frontend trust timeline updates live as tests run

---

## Boundaries

- Always: emit exactly ONE trust signal per gate outcome (never multiple)
- Always: trust signal failure is non-fatal (try/except, pipeline continues)
- Always: Gate 0.1 runs before ALL existing gates
- Ask first: any changes to existing gate logic beyond what is spec-d
- Never: remove or bypass existing gates (injection, velocity, OPA, 2PC)
- Never: hardcode agent_ids or trust scores
- Never: let a trust signal failure block a financial action
