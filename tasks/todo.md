# Sprint 3 Task List — Sentinel Razorpay Edition

> Plan doc: tasks/plan.md
> Spec doc: tasks/SPEC-sprint3a.md

---

## Sprint 3A — Core Wiring (CRITICAL PATH — do these first)

- [x] Task 1: Sentinel SDK Gate Rewiring [Module 8]
  - Files: agents-fleet/sentinel_sdk.py
  - Size: M
  - DONE: Gate 0.3 (behavior hook) added; trust signals wired to ALL deny/HITL/allow paths;
           force_hitl_from_autonomy now returns early BEFORE OPA evaluation; behavior_flags
           propagated in responses; behavior risk boost applied to risk_score.

- [x] Task 2: Razorpay OPA Rego Policies [Module 4]
  - Files: safety-service/policies/razorpay_refund.rego (NEW)
           safety-service/policies/razorpay_payout.rego (NEW)
           safety-service/policies/razorpay_payments.rego (NEW)
           safety-service/main.py (MODIFIED — policy_file_map + capability check)
  - DONE: 3 new Rego policy files; capability check gate added before OPA eval;
           trust_score and agent_limit enriched into OPA input; CAPABILITY_VIOLATION
           signal fires on capability mismatch.

- [x] Task 3: Kill Switch Trust Wiring [Module 6]
  - Files: safety-service/main.py (killswitch_isolate + killswitch_release)
  - DONE: quarantine -> KILL_SWITCH_TRIGGERED (-20 trust); release -> set_trust(50);
           HITL_APPROVED recovery signal emitted on release; trust_reset_to: 50.0
           returned in release response.

## CHECKPOINT A — Sprint 3A complete
- [ ] Manually verify: non-registered agent -> DENY at Gate 0.1
- [ ] Manually verify: quarantine agent -> KILL_SWITCH_TRIGGERED in trust history
- [ ] Manually verify: release agent -> trust = 50.0
- [ ] Manually verify: REFUND > 10000 -> REQUIRE_HITL from OPA
- [ ] Manually verify: RefundAgent fires PAYOUT -> CAPABILITY_VIOLATION

---

## Sprint 3B — Razorpay Pivot

- [x] Task 4: Mock Banking API Razorpay Pivot [Module 9]
  - Files: mock-banking-api/main.py
  - DONE: 4 Razorpay merchants (ZoopCart, FoodieApp, SaasHub, QuickPay);
           GET /merchants/{id}/balance, POST /payments/{id}/refund, GET /orders/{id},
           GET /payments/{id}, GET /merchants/{id}/payments, GET /merchants/{id}/transactions;
           all AmEx endpoints kept intact.

- [x] Task 5: Agent Fleet Rename + Self-Registration [Module 10]
  - Files: agents-fleet/refund_agent.py (NEW)
           agents-fleet/settlement_agent.py (NEW)
           agents-fleet/support_agent.py (NEW)
           agents-fleet/fraud_analysis_agent.py (NEW)
  - DONE: 4 new Razorpay agents; each calls register_on_startup() on import;
           correct LLM model per agent (default/fast/reasoning); correct allowed_tools;
           Sentinel SDK gating on all financial actions.

## CHECKPOINT B — Sprint 3B complete
- [ ] Manually verify: GET /api/v1/merchants/merch_zoopCart/balance -> returns INR balance
- [ ] Manually verify: GET /api/v1/payments/pay_zoo001 -> payment details
- [ ] Manually verify: python refund_agent.py -> agent registered, action fired

---

## Sprint 3C — Integration + Frontend

- [x] Task 6: Unified /action Endpoint [Module 13]
  - Files: safety-service/main.py (POST /api/v1/agents/{id}/action)
  - DONE: Endpoint wraps SDK pipeline; returns trust_before, trust_after, trust_delta,
           autonomy_tier in every response; agent_id injected into parameters for OPA.

- [x] Task 7: Live-Feed Trust Delta Column [Module 11]
  - Files: frontend/src/components/sentinel/live-feed.tsx
           frontend/src/lib/sentinel.ts
  - DONE: TrustDeltaBadge component (green ▲ positive / red ▼ negative);
           autonomy_tier pill shown in agent name row;
           AuditEntry type extended with trust_delta, trust_before, trust_after,
           autonomy_tier, behavior_flags; Razorpay agents added to AGENT_NAMES map.

## CHECKPOINT C — Integration complete
- [ ] Manually verify: POST /api/v1/agents/{id}/action -> returns trust_delta
- [ ] Manually verify: live-feed cards show trust delta badges after actions

---

## Sprint 3D — Docs (deferred per user preference)

- [ ] Task 9: README + Submission Docs [Module 15]
  - Files: README.md, docs/razorpay/SUBMISSION.md, docs/razorpay/DEMO_SCRIPT.md
  - Deferred: User will decide when to write submission docs

## CHECKPOINT D — Submission Ready
- [ ] All tasks above manually verified by user
- [ ] git push -> repo up to date
- [ ] SUBMISSION READY
