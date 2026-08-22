# Sentinel — What Is Still Pending

> **Last Updated:** 2026-08-22 (v2 — Priority 2 backend fixes applied)  
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

### ~~2.1 `trust_engine.py` — `HIGH_RISK_ESCALATED` Signal Not in Weight Table~~ ✅ FIXED

**Where:** `safety-service/trust_engine.py`

**Fix applied:** Added `"HIGH_RISK_ESCALATED": "-2.0"` to `DEFAULT_WEIGHTS` with comment: *"HITL escalation — mild cost for needing human oversight"*.

---

### ~~2.2 Module 7 — New Razorpay Audit Event Types Never Added~~ ✅ FIXED

**Where:** `safety-service/report_generator.py`

**Fix applied:**
- Added `action_type = entry.get("action_type", "")` extraction in the report loop.
- Added INR (₹) currency formatting for Razorpay actions (`REFUND`, `PAYOUT`, `PAYMENT_CAPTURE`).
- Added plain-English translations for `REFUND`, `PAYOUT`, `PAYMENT_CAPTURE`, and all `GET_*` read-only operations.
- Added 6 new summary counters: `razorpay_refunds_processed`, `razorpay_payouts_processed`, `razorpay_captures_processed`, `razorpay_read_ops`, `razorpay_denied`, `razorpay_total_inr`.

---

### ~~2.3 HITL Approve/Reject Doesn't Emit Trust Signals~~ ✅ FIXED

**Where:** `frontend/src/lib/sentinel.ts` — `resolveHitl()`

**Fix applied:** `resolveHitl()` now calls `pushTrustSignal(e.agent_id, "HITL_APPROVED" | "HITL_REJECTED", reason)` after updating local state. The call is fire-and-forget (non-blocking). `HITL_APPROVED` = `+0.2`, `HITL_REJECTED` = `−8.0` (both already defined in `trust_engine.py` `DEFAULT_WEIGHTS`).

---

### ~~2.4 `/api/v1/agents/{id}/action` — `trust_before` Always Returns 100.0~~ ✅ FIXED

**Where:** `safety-service/main.py` lines 1067–1073 and 1105

**Fix applied:** Replaced both `tb.get("trust_score", 100.0)` and `ta.get("trust_score", trust_before)` with direct assignment: `trust_before = get_trust(agent_id)` and `trust_after = get_trust(agent_id)`. `get_trust()` returns a `float` — calling `.get()` on it raised a silent `AttributeError`, causing `trust_delta` on every live-feed card to always be `0.0`.

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
| 2.1 | `HIGH_RISK_ESCALATED` signal missing from trust weight table | 🟡 Medium | ✅ Fixed |
| 2.2 | Report generator doesn't categorize Razorpay events | 🟡 Medium | ✅ Fixed |
| 2.3 | HITL approve/reject doesn't emit trust signals | 🟡 Medium | ✅ Fixed |
| 2.4 | `trust_before` always 100.0 in `/action` endpoint (type bug) | 🔴 High | ✅ Fixed |
| 3.1 | Automated demo script (`tests/razorpay_demo.py`) | 🟠 Demo Risk | Not created |
| 3.2 | README.md outdated — AmEx framing, no Razorpay quickstart | 🟠 Demo Risk | Needs rewrite |
| 3.3 | `docs/razorpay/SUBMISSION.md` | 🟠 Submission | Not created |

---

## Quickest Wins (can be done in < 30 min each)

1. ~~**Fix `trust_before` bug** (2 lines in `main.py`)~~ ✅ Done.
2. ~~**Add `HIGH_RISK_ESCALATED` to trust weights** (1 line in `trust_engine.py`)~~ ✅ Done.
3. ~~**Wire HITL trust signals** (via `resolveHitl()` in `sentinel.ts`)~~ ✅ Done.
4. **Add Razorpay actions to Policy Simulator dropdown** (`policy.tsx`) — immediately makes the Rego policies demoable from the UI. **Still pending.**
