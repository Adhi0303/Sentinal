# Sentinel — What Is Still Pending

> **Last Updated:** 2026-08-22  
> This document lists every feature, fix, or integration that is **not yet coded, incomplete, or broken**. Items are grouped by priority and area.

---

## Priority 1 — Frontend Coding (Functional Gaps)

These are UI features where the **backend API already exists** and returns data, but the **frontend never renders it properly**.

---

### 1.1 Behavior Deviation Radar Chart (Missing Component)

**Where:** `frontend/src/routes/agents_.$id.tsx`

**What's broken:**  
The page already fetches `BehaviorDeviationReport` from `GET /api/v1/behavior/{id}/deviation` and `GET /api/v1/behavior/{id}/baseline`. The data arrives. But the 6-axis radar chart that should visualize the deviation flags (`amount_spike`, `velocity_surge`, `tool_drift`, `depth_increase`, `near_limit_cluster`, `new_account_target`) **was never built**. The page just shows a text message: *"No deviation history yet - fire actions via Demo Sandbox."*

**What needs to be built:**  
A new component `frontend/src/components/sentinel/behavior-deviation.tsx` that renders a **Recharts RadarChart** with 6 axes (one per behavioral flag), showing baseline vs. current action profile. The data model is already defined in `sentinel.ts` as `BehaviorDeviationReport`.

**Why it matters:**  
This is the visual showcase of Module D (Behavior Monitor). Without it, the per-agent detail page looks empty and Module D is invisible to any judge or demo viewer.

---

### 1.2 Demo Sandbox — Only Shows Legacy AmEx Actions

**Where:** `frontend/src/routes/demo.tsx` and `frontend/src/routes/policy.tsx`

**What's broken:**  
The demo sandbox chat page only triggers `FEE_WAIVER` through the `customer_service_agent`. The Policy Simulator (`/policy`) only has `FEE_WAIVER` as the default action type. There is **no way to fire `REFUND`, `PAYOUT`, or `PAYMENT_CAPTURE`** from the UI — so the entire Razorpay pivot (4 agents, 3 Rego policies, 3 new banking endpoints) is invisible in any live UI demo.

**What needs to be built:**  
1. In `policy.tsx`: add `REFUND`, `PAYOUT`, `PAYMENT_CAPTURE` to the action type dropdown, with pre-filled example parameters (e.g., `payment_id: "pay_zoo001"` for REFUND).
2. In `demo.tsx`: either add a "Razorpay Scenario" selector, or extend the chat agent to recognise Razorpay intents and route them to `refund_agent`, `settlement_agent`, or `fraud_analysis_agent` via the unified `/action` endpoint.

---

## Priority 2 — Backend Gaps (Logic Missing)

---

### 2.1 `trust_engine.py` — `HIGH_RISK_ESCALATED` Signal Not in Weight Table

**Where:** `safety-service/trust_engine.py` line 35–58

**What's broken:**  
The SDK calls `_send_trust_feedback(agent_id, "HIGH_RISK_ESCALATED", ...)` whenever an action is escalated to HITL. But `"HIGH_RISK_ESCALATED"` is **not in `DEFAULT_WEIGHTS`**. When `update_trust()` receives it, it logs `"Unknown signal — skipping"` and does nothing. HITL escalations have zero trust impact.

**Fix needed:**  
Add `"HIGH_RISK_ESCALATED": "-2.0"` (a mild negative — being escalated is a small trust cost) to `DEFAULT_WEIGHTS` in `trust_engine.py`.

---

### 2.2 Module 7 — New Razorpay Audit Event Types Never Added

**Where:** `safety-service/audit_ledger.py`, `safety-service/report_generator.py`

**What's missing:**  
The audit ledger writes generic `action_type` strings (e.g., `"REFUND"`, `"PAYOUT"`). But the report generator (`report_generator.py`) and the compliance report PDF template still only recognize the old AmEx event types (`FEE_WAIVER`, `WIRE_TRANSFER`, `CREDIT_LIMIT_INCREASE`) for categorization and statistics. Razorpay events appear as uncategorized in generated reports.

**Fix needed:**  
Update `report_generator.py` to include `REFUND`, `PAYOUT`, `PAYMENT_CAPTURE`, `GET_PAYMENT`, `GET_ORDER`, `GET_BALANCE` in its event-type category maps and summary statistics.

---

### 2.3 `agents_.$id.tsx` — HITL Approve/Reject Doesn't Update Trust

**Where:** `frontend/src/routes/hitl.tsx` and `safety-service/main.py` HITL endpoints

**What's missing:**  
When an operator approves or rejects an action in the HITL queue, the decision is recorded in the queue and forwarded to the banking API. But **no trust signal is emitted**. An `HITL_APPROVED` signal should add `+0.2` trust, and `HITL_REJECTED` should subtract `−8.0` — these signals are already defined in `trust_engine.py`'s `DEFAULT_WEIGHTS` but are never called from the HITL approval endpoint.

**Fix needed:**  
In `safety-service/main.py` at the `POST /api/v1/hitl/{id}/approve` and `POST /api/v1/hitl/{id}/reject` endpoints — call `update_trust(agent_id, "HITL_APPROVED", ...)` and `update_trust(agent_id, "HITL_REJECTED", ...)` respectively.

---

### 2.4 `/api/v1/agents/{id}/action` — `trust_before` Always Returns 100.0

**Where:** `safety-service/main.py` lines 1067–1073

**What's broken:**  
```python
tb = get_trust(agent_id)
trust_before = tb.get("trust_score", 100.0)  # BUG: get_trust() returns a float, not a dict
```
`get_trust()` in `trust_engine.py` returns a **`float`**, not a dict. Calling `.get()` on a float raises `AttributeError` which is silently caught by the `except Exception: pass` block — so `trust_before` always stays at the default `100.0`. The `trust_delta` calculation is therefore always wrong.

**Fix needed:**  
```python
trust_before = get_trust(agent_id)   # returns float directly
```
Same fix needed for `trust_after` at line 1105.

---

## Priority 3 — Demo / Submission Quality

These items are not strictly backend or frontend bugs, but they directly affect how the project is perceived during a live demo.

---

### 3.1 Demo Script (`tests/razorpay_demo.py`) — Not Created

**What's missing:**  
There is no automated end-to-end demo script. The `MODULES_TRACKER.md` specifies a 6-scene demo script:

| Scene | What to show |
|---|---|
| 1 | Agent self-registers, trust starts at 100 |
| 2 | Normal REFUND flows through all 9 gates — ALLOWED |
| 3 | Oversized refund → OPA DENY (razorpay_refund.rego) |
| 4 | Kill switch fired → trust drops, agent BLOCKED |
| 5 | Prompt injection attempt → Gate 2 DENIED |
| 6 | Release agent → trust resets to 50, normal ops resume |

Without this script, a live demo requires manual curl commands — high risk of fumbling during a hackathon presentation.

---

### 3.2 README.md — Still References AmEx Framing

**Where:** `README.md`

**What's outdated:**  
The README's architecture diagram, feature list, and service descriptions still reference AmEx-specific terminology (`fee waiver`, `credit limit`, `treasury agent`) as the primary use case. The Razorpay pivot (the actual demo) is nowhere in the README. Judges reading the README will be confused.

**Fix needed:**  
- Update the executive summary to lead with the Razorpay merchant governance use case.
- Replace/supplement the architecture diagram to show the 4 Razorpay merchants.
- Add a "Quick Start" section with the 4-service startup commands.
- Add a "Key Demo Scenarios" section referencing the 6 demo scenes.

---

### 3.3 Submission Document (`docs/razorpay/SUBMISSION.md`) — Not Created

**What's missing:**  
A structured Razorpay Buildathon submission document covering:
- Problem statement
- Solution architecture
- What Razorpay features/APIs are used
- Impact and business value
- Team details

---

## Summary Table

| # | Area | Severity | Status |
|---|---|---|---|
| 1.1 | Behavior Deviation Radar Chart (frontend component) | 🔴 High | Not built |
| 1.2 | Demo Sandbox Razorpay actions in UI | 🔴 High | Not built |
| 2.1 | `HIGH_RISK_ESCALATED` signal missing from trust weight table | 🟡 Medium | 1 line fix |
| 2.2 | Report generator doesn't categorize Razorpay events | 🟡 Medium | Small update |
| 2.3 | HITL approve/reject doesn't emit trust signals | 🟡 Medium | 2 endpoint patches |
| 2.4 | `trust_before` always 100.0 in `/action` endpoint (type bug) | 🔴 High | 2 line fix |
| 3.1 | Automated demo script (`tests/razorpay_demo.py`) | 🟠 Demo Risk | Not created |
| 3.2 | README.md outdated — AmEx framing, no Razorpay quickstart | 🟠 Demo Risk | Needs rewrite |
| 3.3 | `docs/razorpay/SUBMISSION.md` | 🟠 Submission | Not created |

---

## Quickest Wins (can be done in < 30 min each)

1. **Fix `trust_before` bug** (2 lines in `main.py`) — makes trust delta accurate across the entire system.
2. **Add `HIGH_RISK_ESCALATED` to trust weights** (1 line in `trust_engine.py`).
3. **Wire HITL trust signals** (2 lines in the HITL approve/reject endpoints).
4. **Add Razorpay actions to Policy Simulator dropdown** (`policy.tsx`) — immediately makes the Rego policies demoable from the UI.
