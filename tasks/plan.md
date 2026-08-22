# Implementation Plan: Sprint 3 — Sentinel Razorpay Edition

## Overview

We have fully built the observability layer (Modules A/B/C/D): agents are registered, trust is tracked, autonomy tiers are computed, and behavior deviations are detected. Sprint 3 wires all of this into the actual enforcement pipeline and pivots the entire system from AmEx to Razorpay-native context. It has three sub-sprints: 3A (core wiring — critical path), 3B (Razorpay pivot), and 3C (demo and submission).

The dependency graph is strict:
  3A must complete before 3B. 3B must complete before 3C.
  Within 3A: SDK (Task 1) must come before OPA policies (Task 2) and Kill Switch (Task 3).

---

## Architecture Decisions

- **Trust signals are fire-and-forget.** A signal emission failure never blocks a financial action. Always wrap in try/except.
- **Gate 0.1 runs before ALL existing gates.** An unregistered agent gets no further processing — this prevents any bypass of the registry.
- **policy_file_map drives OPA routing.** All three new Rego files slot into the existing evaluator — no changes to opa_evaluator.py itself.
- **Release resets trust to 50, not 100.** Agents must rebuild trust after a kill-switch event. This is deliberate and must not be changed.
- **Agents self-register on startup.** Each agent in agents-fleet/ calls POST /api/v1/agents/register on boot, so the registry always reflects the live fleet.
- **Unified /action endpoint wraps the SDK.** Module 13 makes it possible for the frontend demo sandbox to fire actions without importing Python directly.

---

## Dependency Graph

```
[Task 1] SDK Gates (M8)
    |
    +-- [Task 2] OPA Rego Policies (M4)   <- can start AFTER Task 1 Gate 0.1 done
    +-- [Task 3] Kill Switch Trust (M6)   <- can start in parallel with Task 2

[CHECKPOINT A] All gate wiring verified

    +-- [Task 4] Razorpay Banking API (M9)
    +-- [Task 5] Agent Fleet Rename (M10) <- parallel with Task 4

[CHECKPOINT B] Razorpay pivot complete

    +-- [Task 6] Unified /action Endpoint (M13)
    +-- [Task 7] Live-Feed Trust Delta Column (M11) <- parallel with Task 6

[CHECKPOINT C] Full system integration verified

    +-- [Task 8] 6-Scene Demo Script (M14)

[CHECKPOINT D] Demo verified working

    +-- [Task 9] README + SUBMISSION.md + DEMO_SCRIPT.md (M15)

[DONE]
```

---

## Sprint 3A — Core Wiring (Critical Path)

### Task 1: Sentinel SDK Gate Rewiring [Module 8]
File: agents-fleet/sentinel_sdk.py
Size: M (touches 1 file heavily, ~80 new lines)

Add a private helper _emit_trust_signal() at the top of the SDK.
Then add 3 new gates at the START of execute_governed_tool(), before all existing gates:
  Gate 0.1: GET /api/v1/agents/{agent_id} — registry existence + suspended check
  Gate 0.2: GET /api/v1/autonomy/{agent_id} — tier enforcement
  Gate 0.3: POST /api/v1/behavior/{agent_id}/check — deviation hook, boost risk_score

Then wrap ALL existing gate outcomes with _emit_trust_signal() calls:
  prompt blocked    -> PROMPT_INJECTION_DETECTED
  velocity denied   -> ACTION_DENIED_VELOCITY
  risk -> hitl      -> HIGH_RISK_ESCALATED
  OPA denied        -> ACTION_DENIED_POLICY
  hitl approved     -> HITL_APPROVED
  hitl rejected     -> HITL_REJECTED
  bank success      -> ACTION_ALLOWED

Acceptance criteria:
  - Calling SDK with a non-existent agent_id returns {"status":"DENY","reason":"Unregistered agent"}
  - Calling SDK with a SUSPENDED agent_id returns {"status":"DENY","reason":"Agent is SUSPENDED"}
  - After trust drops to HITL range, a low-risk action returns REQUIRE_HITL from Gate 0.2
  - A successful bank transaction creates a trust history entry ACTION_ALLOWED +0.5
  - Signal failure (safety-service down) does not crash the SDK pipeline

Verification:
  - Start safety-service + mock-banking-api
  - python agents-fleet/treasury_agent.py -> confirm trust signal appears in /api/v1/trust/{id}/history
  - Check frontend trust timeline chart updates after running the agent

Dependencies: None (first task)

---

### Task 2: Razorpay OPA Rego Policies [Module 4]
Files: safety-service/policies/razorpay_refund.rego (NEW)
       safety-service/policies/razorpay_payout.rego (NEW)
       safety-service/policies/razorpay_payments.rego (NEW)
       safety-service/main.py (MODIFY — policy_file_map + capability check)
Size: M (4 files, mostly config/Rego)

Create 3 new Rego policy files.
Add capability check in main.py BEFORE OPA evaluation:
  load agent from registry
  if action_type not in agent[allowed_tools] -> DENY + emit CAPABILITY_VIOLATION

Update policy_file_map in main.py:
  REFUND          -> razorpay_refund.rego
  PAYOUT          -> razorpay_payout.rego
  PAYMENT_CAPTURE -> razorpay_payments.rego
  WIRE_TRANSFER   -> trading_limits.rego (unchanged)

Acceptance criteria:
  - REFUND with amount=12001 (> 10000 threshold) -> REQUIRE_HITL
  - REFUND with trust_score=35 (< 40) -> DENY
  - PAYOUT with destination_verified=false -> DENY
  - RefundAgent firing PAYOUT action -> DENY at capability check + CAPABILITY_VIOLATION signal fired
  - WIRE_TRANSFER still governed by existing trading_limits.rego (no regression)

Verification:
  - ./safety-service/bin/opa eval --data ... (eval each policy file manually)
  - POST /api/v1/governed-action with REFUND amount=15000 -> REQUIRE_HITL in response

Dependencies: Task 1 (trust signal emission needed for capability check)

---

### Task 3: Kill Switch Trust Wiring [Module 6]
Files: safety-service/kill_switch.py (MODIFY)
       safety-service/main.py (MODIFY — /killswitch/release endpoint)
Size: S (2 files, ~15 new lines each)

In kill_switch.py quarantine_agent():
  After quarantine state written to Redis:
  -> call _emit_trust_or_set() to emit KILL_SWITCH_TRIGGERED signal (-20)

In main.py /killswitch/release:
  After releasing:
  -> trust_engine.set_trust(agent_id, 50.0)   <- NOT 100
  -> audit_ledger.append_audit_entry(AGENT_RECOVERED)

Acceptance criteria:
  - POST /killswitch/quarantine/{agent_id} -> trust history shows KILL_SWITCH_TRIGGERED entry with delta=-20
  - POST /killswitch/release/{agent_id} -> trust score becomes exactly 50.0
  - Released agent trust is NOT 100 (assert != 100)
  - AGENT_RECOVERED entry appears in audit log

Verification:
  - Quarantine an agent via API, check GET /api/v1/trust/{id}/history
  - Release agent, check GET /api/v1/trust/{id} -> score = 50.0

Dependencies: Task 1 (trust_engine.set_trust and signal emission pattern)

---

### CHECKPOINT A: Sprint 3A Complete
  - SDK: all 3 new gates active and tested
  - OPA: 3 Razorpay Rego policies live, capability check in place
  - Kill Switch: quarantine/release wired to trust engine
  - Frontend trust timeline shows live updates during all above tests
  -> REVIEW BEFORE PROCEEDING TO 3B

---

## Sprint 3B — Razorpay Pivot

### Task 4: Mock Banking API Razorpay Pivot [Module 9]
File: mock-banking-api/main.py (MODIFY)
Size: M (1 file, replace ~60 lines of account data)

Replace AmEx merchant accounts with Razorpay merchants:
  merch_zoopCart    -> E-commerce, limit 10000 INR
  merch_foodieApp   -> Food delivery, limit 3000 INR
  merch_saasHub     -> B2B SaaS, limit 50000 INR
  merch_quickPay    -> Payment aggregator, limit 100000 INR

Add new endpoints:
  POST /api/v1/payments/{id}/refund
  GET  /api/v1/orders/{id}
  GET  /api/v1/merchants/{id}/balance

Acceptance criteria:
  - GET /api/v1/merchants/merch_zoopCart/balance returns INR balance
  - POST /api/v1/payments/pay_123/refund with amount=500 returns success
  - GET /api/v1/orders/order_456 returns order metadata
  - Old AmEx endpoints removed (no regression test needed — they are replaced)

Verification:
  - curl http://localhost:8000/api/v1/merchants/merch_zoopCart/balance
  - curl -X POST http://localhost:8000/api/v1/payments/pay_test/refund -d {amount:1000}

Dependencies: None (can run parallel with Task 3)

---

### Task 5: Agent Fleet Rename + Self-Registration [Module 10]
Files: agents-fleet/refund_agent.py (NEW — rename of customer_service_agent.py)
       agents-fleet/settlement_agent.py (NEW — rename of treasury_agent.py)
       agents-fleet/support_agent.py (NEW — rename of underwriting_agent.py)
       agents-fleet/fraud_analysis_agent.py (NEW — rename of procurement_agent.py)
Size: M (4 files, mostly rename + add register_on_startup())

Each agent gets:
  1. New filename and AGENT_ID matching the Razorpay context
  2. register_on_startup() function that calls POST /api/v1/agents/register on __init__
  3. Updated SYSTEM_PROMPT / docstring to reflect Razorpay merchant context
  4. LLM model from llm_config.py (already done, just carry over)

Agent -> Merchant mapping:
  refund_agent.py        -> ZoopCart, tools: [get_payment, get_order, initiate_refund]
  settlement_agent.py    -> QuickPay, tools: [get_balance, initiate_payout, get_settlement]
  support_agent.py       -> FoodieApp, tools: [get_payment, explain_failure, get_order]
  fraud_analysis_agent.py -> SaasHub, tools: [get_transactions, flag_transaction, get_merchant_stats]

Acceptance criteria:
  - Running python refund_agent.py registers agent in registry automatically
  - GET /api/v1/agents shows 4 Razorpay agents with correct merchant owners
  - Each agent's allowed_tools match the Razorpay capability map
  - Old AmEx agent files kept but marked as deprecated (do not delete, keep for git history)

Verification:
  - python agents-fleet/refund_agent.py -> confirm registry shows agent
  - GET /api/v1/agents -> 4 agents listed, all ACTIVE

Dependencies: Task 1 (SDK gates check registry — agents must be registered to work)

---

### CHECKPOINT B: Razorpay Pivot Complete
  - Banking API: 4 Razorpay merchants, 3 new endpoints live
  - Agent Fleet: 4 renamed agents, self-register on startup
  - End-to-end: python refund_agent.py fires a refund -> trust updates -> autonomy tier visible in frontend
  -> REVIEW BEFORE PROCEEDING TO 3C

---

## Sprint 3C — Demo and Submission

### Task 6: Unified /action Endpoint [Module 13]
File: safety-service/main.py (MODIFY — add 1 new endpoint)
Size: S (1 file, ~40 lines)

New endpoint: POST /api/v1/agents/{id}/action
  Wraps the full SDK pipeline without needing to import Python SDK directly.
  Request body: { action_type, parameters }
  Response adds: trust_before, trust_after, trust_delta, autonomy_tier, deviation_flags

Acceptance criteria:
  - POST /api/v1/agents/refund-agent-001/action with REFUND 500 -> full gate pipeline runs
  - Response includes trust_before and trust_after values
  - Frontend demo sandbox can fire this endpoint

Verification:
  - curl -X POST http://localhost:8001/api/v1/agents/{id}/action -d {action_type:REFUND,parameters:{...}}
  - Check trust history updated after call

Dependencies: Tasks 1, 2, 3 (all gates must be in place)

---

### Task 7: Live-Feed Trust Delta Column [Module 11]
File: frontend/src/routes/live-feed.tsx (MODIFY)
Size: S (1 file, ~20 lines)

Add trust_delta column to the live feed table:
  +0.5 shown in green with up arrow
  -8.0 shown in red with down arrow
  0 shown in grey

Acceptance criteria:
  - trust_delta column visible in live feed table header
  - Positive deltas are green, negative are red
  - Column sorts correctly

Verification:
  - Fire an action via frontend demo sandbox
  - Live feed shows the entry with correct delta color

Dependencies: Task 6 (unified /action endpoint provides trust_delta in response)

---

### Task 8: 6-Scene Automated Demo Script [Module 14]
File: tests/razorpay_demo.py (NEW)
Size: L (1 file, ~200 lines, 6 scenes)

Scene 1: Register RefundAgent for ZoopCart
Scene 2: Normal operation — 3 refunds -> trust holds at ~101.5
Scene 3: Anomaly — 5x near-limit refunds -> VELOCITY_EVASION -> trust drops -> HITL tier
Scene 4: Dangerous — modify_payout_account -> CAPABILITY BLOCK -> trust < 40 -> QUARANTINE
Scene 5: Investigation — print trust history + behavior timeline for agent
Scene 6: Recovery — admin resets to trust=50, tighter autonomy, agent back online

Each scene:
  - Prints scene header banner
  - Makes API calls directly (no need to run agents)
  - Prints result with PASS/FAIL status
  - Pauses 1 second between scenes for readability

Acceptance criteria:
  - python tests/razorpay_demo.py runs completely without crashing
  - All 6 scenes print their expected outcome
  - Scene 4 shows trust dropping to QUARANTINE range
  - Scene 6 shows trust restored to 50.0

Verification:
  - python tests/razorpay_demo.py -> all PASS
  - Check frontend at localhost:5173/agents/{id} during/after script run

Dependencies: Tasks 1, 2, 3, 4, 5, 6

---

### CHECKPOINT C: Demo Ready
  - python tests/razorpay_demo.py runs all 6 scenes cleanly
  - Frontend shows live trust updates during demo
  -> REVIEW BEFORE WRITING SUBMISSION DOCS

---

### Task 9: README + Submission Docs [Module 15]
Files: README.md (MODIFY — full rewrite for Razorpay)
       docs/razorpay/SUBMISSION.md (NEW)
       docs/razorpay/DEMO_SCRIPT.md (NEW)
Size: M (3 files, documentation only)

README.md:
  - 3-command setup (clone, pip install, npm install)
  - Architecture diagram (ASCII)
  - What Sentinel does in 3 sentences
  - Link to demo script

SUBMISSION.md:
  - Problem statement (in Razorpay context)
  - Our solution and why it matters
  - Architecture overview
  - Evidence of working system (screenshots / API responses)
  - Module completion table

DEMO_SCRIPT.md:
  - Scene-by-scene narration for judges
  - Expected outputs for each scene
  - What each scene demonstrates about AI safety

Acceptance criteria:
  - README has working 3-command setup that a fresh machine can follow
  - SUBMISSION.md answers the hackathon judging criteria
  - DEMO_SCRIPT.md maps each scene to a safety concept

Dependencies: Task 8 (demo script must exist before documenting it)

---

### CHECKPOINT D: Submission Ready
  - All 9 tasks complete
  - python tests/razorpay_demo.py -> all 6 scenes PASS
  - README 3-command setup verified on clean state
  - git push to repo

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| OPA binary not in PATH during tests | High | Test with explicit path safety-service/bin/opa; add PATH check |
| Redis not running during SDK gate calls | High | SDK already has fallback dict; gates should degrade gracefully |
| Groq API rate limit during demo | Med | Cache LLM responses for demo scenes; use GROQ_FAST_MODEL |
| Trust signal API call adds latency to every action | Med | timeout=2 on all signal calls; fire-and-forget pattern |
| Renaming agents breaks existing demo flows | Low | Keep old files as deprecated, new files are additive |

---

## Open Questions

None. All tasks are fully specified. Ready to /build.
