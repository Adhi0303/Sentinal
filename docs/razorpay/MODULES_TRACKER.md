# Sentinel — Razorpay Edition: Master Module Build Tracker

> **Project:** Sentinel — Adaptive Autonomy Control Plane for AI Agents
> **Hackathon:** Razorpay /buildathon — Open Track
> **Strategy:** Evolve the existing AmEx Sentinel into a Razorpay-native product
> **Core Product Loop:** `Register → Govern → Observe → Trust → Adapt Autonomy → Recover`

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ **KEEP** | Module is complete and works as-is. Zero changes needed. |
| 🔧 **MODIFY** | Module exists and works, but needs targeted changes for Razorpay pivot. |
| 🆕 **NEW** | Does not exist at all. Must be built from scratch. |
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete ✅ |

---

## 🏁 CURRENT STATUS SUMMARY (as of 2026-08-22 — UPDATED)

| Phase | Status |
|---|---|
| **Phase 1 Backend** — Module A (Registry) + B (Trust) + C (Autonomy) | ✅ **COMPLETE** |
| **Phase 1 Frontend** — `/agents` page, Agent Detail, Trust KPIs, Fleet badges | ✅ **COMPLETE** |
| **Phase 2 Backend** — Module D (Behavior Monitor) | ✅ **COMPLETE** |
| **Phase 2 Frontend** — Behavior Monitor dashboard panel on `/agents/$id` | ✅ **COMPLETE** |
| **Phase 2 Infra** — Kill Switch → Registry wiring, Shared LLM config | ✅ **COMPLETE** |
| **Sprint 3A** — SDK rewiring (Gates 0.1/0.2/0.3/X), OPA Rego policies, Capability Check | ✅ **COMPLETE** |
| **Sprint 3B** — Razorpay banking API pivot, Agent fleet rename + self-register, Unified /action | ✅ **COMPLETE** |
| **Sprint 3C** — Frontend trust_delta live feed, Demo Script, Docs + Submission | 🔴 **NEXT PRIORITY** |

---

## Master Module Map

```
SENTINEL — RAZORPAY EDITION
│
├── LAYER 0: CONTROL PLANE
│   ├── MODULE A: Agent Registry              [x] BACKEND ✅ + FRONTEND ✅
│   ├── MODULE B: Trust Engine                [x] BACKEND ✅ + FRONTEND ✅
│   ├── MODULE C: Autonomy Engine             [x] BACKEND ✅ + FRONTEND ✅
│   └── MODULE D: Behavior Monitor            [x] BACKEND ✅ + FRONTEND ✅
│
├── LAYER 1: GOVERNANCE ENGINE (EXISTING)
│   ├── MODULE 2: AI Safety Layer             [x] KEEP — done
│   ├── MODULE 3: Multi-Agent Coordinator     [x] KEEP — done
│   ├── MODULE 4: OPA Policy Engine           [x] Razorpay Rego policies BUILT ✅
│   ├── MODULE 5: Financial Guardrails        [x] KEEP — done
│   ├── MODULE 6: Kill Switch + SAGA          [/] Registry wiring done; trust wiring PENDING
│   └── MODULE 7: Audit + Telemetry           [/] Core done, new event types pending
│
├── LAYER 2: INTEGRATION LAYER
│   ├── MODULE 8: Sentinel SDK                [x] All gates rewired (0.1/0.2/0.3/X) ✅
│   ├── MODULE 9: Mock Banking / Razorpay API [x] Razorpay merchant pivot DONE ✅
│   └── MODULE 10: AI Agent Fleet             [x] Renamed + self-register on startup ✅
│
├── LAYER 3: FRONTEND
│   ├── MODULE 11: Existing Dashboard         [x] Live-feed trust_delta column DONE ✅
│   └── MODULE 12: New Control Plane UI       [x] /agents + /agents/$id + behavior panel DONE ✅
│
└── LAYER 4: INFRASTRUCTURE + DEMO
    ├── MODULE 13: Backend API Wiring         [x] Unified /action endpoint DONE ✅
    ├── MODULE 14: Demo Script + Simulation   [ ] NOT STARTED ← NEXT
    └── MODULE 15: Docs + Submission          [ ] NOT STARTED ← NEXT
```


---
---

# ✅ COMPLETED: LAYER 0 PHASE 1 — CONTROL PLANE

## MODULE A: Agent Registry `[x]` ✅

**Backend file:** `safety-service/agent_registry.py` — DONE
**API endpoints live at `http://localhost:8001`:**

| Endpoint | Status |
|---|---|
| `POST /api/v1/agents/register` | ✅ Live |
| `GET /api/v1/agents` | ✅ Live |
| `GET /api/v1/agents/{id}` | ✅ Live |
| `POST /api/v1/agents/{id}/status` | ✅ Live |

**Frontend pages connected:**
- `/agents` — Registry page with filter table, tier distribution strip, register form ✅
- `/agents/$id` — Agent detail with controls ✅

---

## MODULE B: Trust Engine `[x]` ✅

**Backend file:** `safety-service/trust_engine.py` — DONE
**API endpoints live:**

| Endpoint | Status |
|---|---|
| `GET /api/v1/trust/{agent_id}` | ✅ Live |
| `GET /api/v1/trust/{agent_id}/history` | ✅ Live |
| `POST /api/v1/trust/{agent_id}/signal` | ✅ Live |
| `GET /api/v1/trust/weights` | ✅ Live |

**Frontend pages connected:**
- Trust timeline chart on `/agents/$id` ✅
- Trust score badge in `/agents` table ✅
- Fleet Avg Trust KPI on home dashboard ✅

---

## MODULE C: Autonomy Engine `[x]` ✅

**Backend file:** `safety-service/autonomy_engine.py` — DONE
**API endpoints live:**

| Endpoint | Status |
|---|---|
| `GET /api/v1/autonomy/{agent_id}` | ✅ Live |
| `GET /api/v1/autonomy/fleet/distribution` | ✅ Live |
| `GET /api/v1/autonomy/tiers` | ✅ Live |

**Frontend connected:**
- Autonomy tier badge (FULL/BOUNDED/HITL/QUARANTINE) in fleet snapshot ✅
- Agents in HITL + Quarantined KPI cards on home dashboard ✅
- Autonomy decision panel on agent detail page ✅

---
---

# 🔴 NEXT PRIORITY: PHASE 2

---

## MODULE D: Behavior Monitor `[🆕 NEW]` `[ ]`

**Purpose:** Detects behavioral deviation from an agent's established baseline *before* a catastrophic transaction happens. The early-warning system.

**New file to create:** `safety-service/behavior_monitor.py`

### Submodule D.1 — Baseline Profiler `[ ]`

Track per-agent behavioral baseline after first 10 actions:
```python
{
  "avg_amount": float,
  "amount_stddev": float,
  "tool_frequency": dict,       # {"initiate_refund": 0.7, "get_order": 0.3}
  "avg_call_depth": float,
  "actions_per_minute": float,
  "common_accounts": list,
  "baseline_sample_size": int
}
```
Stored at Redis key: `sentinel:behavior:baseline:{agent_id}`

### Submodule D.2 — Deviation Detector `[ ]`

| Flag | Condition | Trust Signal | Delta |
|---|---|---|---|
| `amount_spike` | amount > avg_amount × 1.5 | `BEHAVIOR_ANOMALY_MILD` | -2 |
| `velocity_surge` | actions/min > baseline × 2 | `BEHAVIOR_ANOMALY_SEVERE` | -8 |
| `tool_drift` | tool not in historical top-5 | `BEHAVIOR_ANOMALY_MILD` | -2 |
| `depth_increase` | call_depth > baseline + 2 | `BEHAVIOR_ANOMALY_SEVERE` | -8 |
| `near_limit_cluster` | 3+ consecutive amounts >90% of tx_limit | `VELOCITY_EVASION_DETECTED` | -10 |
| `new_account_target` | account_id not in common_accounts | `BEHAVIOR_ANOMALY_MILD` | -2 |

### Submodule D.3 — Behavior API Endpoints `[ ]`

```
POST /api/v1/behavior/{agent_id}/check     → deviation report (called by SDK per action)
GET  /api/v1/behavior/{agent_id}/baseline  → current baseline stats
GET  /api/v1/behavior/{agent_id}/deviation → latest deviation report
GET  /api/v1/behavior/{agent_id}/timeline  → deviation scores over time
```

**Frontend page to add (after D backend done):**
- Behavior deviation radar chart on `/agents/$id` (6-axis: Amount, Velocity, Tool, Depth, Account, Near-Limit)

---

## MODULE 8: Sentinel SDK Rewiring `[🔧 MODIFY]` `[ ]`

**File:** `agents-fleet/sentinel_sdk.py`

This is the **most critical Phase 2 task** — rewiring every gate outcome to send a trust signal and check autonomy on every action.

### Submodule 8.1 — Gate 0.1: Registry Existence Check `[ ]`
Add as **first gate**: check `GET /api/v1/agents/{agent_id}`. If 404 → DENY "Unregistered agent". If SUSPENDED → DENY.

### Submodule 8.2 — Gate 0.2: Autonomy Decision `[ ]`
After registry check: call `GET /api/v1/autonomy/{agent_id}`:
- `QUARANTINE` → DENY immediately
- `HITL` → force HITL regardless of risk score
- `BOUNDED` → apply `limits_override` to velocity gates

### Submodule 8.3 — Behavior Monitor Hook `[ ]`
After schema validation: call `POST /api/v1/behavior/{agent_id}/check`. If `deviation_score > 60` → boost risk_score by +20.

### Submodule 8.4 — Trust Feedback After Every Gate `[ ]`

Every gate outcome must emit exactly one trust signal:

| Gate Outcome | Signal |
|---|---|
| Prompt BLOCKED | `PROMPT_INJECTION_DETECTED` |
| Capability DENIED | `CAPABILITY_VIOLATION` |
| Velocity DENIED | `ACTION_DENIED_VELOCITY` |
| HITL escalated | `HIGH_RISK_ESCALATED` |
| HITL rejected | `HITL_REJECTED` |
| HITL approved | `HITL_APPROVED` |
| OPA DENIED | `ACTION_DENIED_POLICY` |
| Bank SUCCESS | `ACTION_ALLOWED` |

---

## MODULE 4: OPA Policy Engine — Razorpay Rego `[🔧 MODIFY]` `[ ]`

**New policies to create:**

### `safety-service/policies/razorpay_refund.rego` `[ ]`
```rego
package sentinel.razorpay_refund
deny["Amount exceeds agent limit"] { input.amount > input.agent_limit }
deny["Agent trust too low"] { input.trust_score < 40 }
require_hitl["Large refund"] { input.amount > 10000 }
```

### `safety-service/policies/razorpay_payout.rego` `[ ]`
```rego
package sentinel.razorpay_payout
deny["Unverified payout destination"] { not input.destination_verified }
require_hitl["Large payout"] { input.amount > 500000 }
```

### Submodule 4.3 — Capability Check in `main.py` `[ ]`
Before OPA evaluation: load agent from registry → if `action_type` not in `agent.allowed_tools` → DENY "Capability violation" + emit `CAPABILITY_VIOLATION` trust signal.

---

## MODULE 9: Mock Banking API Razorpay Pivot `[🔧 MODIFY]` `[ ]`

**File:** `mock-banking-api/main.py`

Replace AmEx merchant accounts with Razorpay merchant context:

| Merchant | ID | Type | Per-Tx Limit |
|---|---|---|---|
| ZoopCart | `merch_zoopCart` | E-commerce | ₹10,000 |
| FoodieApp | `merch_foodieApp` | Food delivery | ₹3,000 |
| SaasHub | `merch_saasHub` | B2B SaaS | ₹50,000 |
| QuickPay | `merch_quickPay` | Payment aggregator | ₹1,00,000 |

New endpoints: `POST /api/v1/payments/{id}/refund`, `GET /api/v1/orders/{id}`, `GET /api/v1/merchants/{id}/balance`

---

## MODULE 10: Agent Fleet Razorpay Rename `[🔧 MODIFY]` `[ ]`

| Old File | New File | Role | Merchant |
|---|---|---|---|
| `customer_service_agent.py` | `refund_agent.py` | Auto-process refunds | ZoopCart |
| `treasury_agent.py` | `settlement_agent.py` | Payout settlement | QuickPay |
| `underwriting_agent.py` | `support_agent.py` | Explain failed payments | FoodieApp |
| `procurement_agent.py` | `fraud_analysis_agent.py` | Detect anomalies | SaasHub |

Each agent must call `POST /api/v1/agents/register` on startup with Razorpay merchant context.

---

## MODULE 13: Unified Action Endpoint `[🔧 MODIFY]` `[ ]`

**New: `POST /api/v1/agents/{id}/action`** — single entry point wrapping the full SDK pipeline.

Response includes `trust_before`, `trust_after`, `trust_delta`, `autonomy_tier` + all gate results.

---

## MODULE 6: Kill Switch → Trust Wiring `[🔧 MODIFY]` `[ ]`
- Quarantine → call `update_trust(agent_id, "KILL_SWITCH_TRIGGERED")` → -20
- Release → call `set_trust(agent_id, 50)` (NOT 100, agent must rebuild trust)

---

## MODULE 11: Remaining Frontend Updates `[🔧 MODIFY]` `[ ]`

### Submodule 11.3 — Live Feed trust delta column `[ ]`
Add `trust_delta` column (↑ +0.5 green / ↓ -8.0 red) to `live-feed.tsx`.

### Submodule 11.4 — Behavior Deviation Chart `[ ]`
Add radar chart to `/agents/$id` once Module D backend is ready.
Component: `frontend/src/components/sentinel/behavior-deviation.tsx`

---

## MODULE 14: Demo Script `[🆕 NEW]` `[ ]`

**New file:** `tests/razorpay_demo.py`

6-Scene automated demo:
```
Scene 1 — Register RefundAgent for ZoopCart
Scene 2 — Normal operation: 3 refunds → trust holds at 100
Scene 3 — Anomaly: 5× near-limit refunds → trust drops to 62 → HITL tier
Scene 4 — Dangerous: modify_payout_account → CAPABILITY BLOCK → trust=31 → QUARANTINE
Scene 5 — Investigation: admin views trust history + behavior timeline
Scene 6 — Recovery: admin resets trust to 50, tighter autonomy, agent back online
```

---

## MODULE 15: Docs + Submission `[🆕 NEW]` `[ ]`
- `README.md` — Razorpay-native, 3-command setup
- `docs/razorpay/SUBMISSION.md` — Problem / Solution / Architecture / Evidence
- `docs/razorpay/DEMO_SCRIPT.md` — Scene-by-scene narration

---
---

# 🧪 TESTING GUIDE: HOW TO TEST WHAT'S BUILT

## Login Instructions

| Role | Username | Password | Access |
|---|---|---|---|
| **Admin (YOU)** | `adhi` | `adhi123` | Full dashboard — all pages |
| Customer demo | `tara` | `tara123` | Portal page only (limited) |

> **Use `adhi` (admin) to test all new Phase 1 features.** Tara is a customer portal user and cannot see the control plane.

---

## 🔗 URLs (after `npm run dev` in `frontend/`)

| Page | URL | What it shows |
|---|---|---|
| Home Dashboard | `http://localhost:5173/` | Trust KPI cards, fleet snapshot |
| **Agent Registry** | `http://localhost:5173/agents` | All registered agents + trust |
| **Agent Detail** | `http://localhost:5173/agents/{id}` | Trust timeline + controls |
| HITL Queue | `http://localhost:5173/hitl` | Pending approvals |
| Audit Ledger | `http://localhost:5173/audit` | Tamper-proof log |
| Demo Sandbox | `http://localhost:5173/demo` | Fire test actions |

---

## 🧪 TEST CASES — Phase 1 Features

### TEST 1: Register a New Agent (Module A)
1. Login as **adhi** → go to `/agents`
2. Click **"Register Agent"**
3. **Step 1:** Name = `"ZoopCart Refund Agent"`, Owner = `"ZoopCart"`, Purpose = `"Auto-process customer refunds"`, Model = `gpt-4o`
4. **Step 2:** Check `get_payment`, `get_order`, `initiate_refund` · Tx Limit = `5000` · Daily Budget = `100000`
5. **Step 3:** Click **"Register Agent"**
6. **Expected:** Toast notification appears. Agent shows up in the grid with Trust Score = 100.0, Tier = FULL (green)

---

### TEST 2: View Trust Score + Autonomy Tier (Modules B + C)
1. After registering, click the **"Details →"** button on any agent card
2. **Expected on detail page:**
   - Large trust score number (e.g. `100.0`) in green
   - Autonomy decision panel shows `Tier: FULL`, `Requires HITL: No`, `Blocked: No`
   - Trust Timeline chart is empty (no events yet — "No trust events yet")

---

### TEST 3: Push a Trust Signal (Module B — admin override)
1. On agent detail page → click **"Push Trust Signal"**
2. Select signal: `ACTION_DENIED_POLICY` · Reason: `"Test policy violation"`
3. Click **"Push Signal"**
4. **Expected:**
   - Toast: `"Signal "ACTION_DENIED_POLICY" sent"`
   - Trust score drops by -5.0 (e.g. 100 → 95)
   - Trust Timeline chart shows a red dot at the drop point
   - Trust Event Log shows the entry with `delta: -5.0`

---

### TEST 4: Push Multiple Signals to Change Tier (Module C)
1. Push `CAPABILITY_VIOLATION` (−15) → `HITL_REJECTED` (−8) → `ACTION_DENIED_POLICY` (−5)
2. After 3 signals: score = 100 − 15 − 8 − 5 = **72** → tier should change to **BOUNDED** (amber)
3. Push `ACTION_DENIED_POLICY` (−5) × 6 more = **42** → tier changes to **HITL** (orange badge)
4. Push `KILL_SWITCH_TRIGGERED` (−20) = **22** → tier should show **QUARANTINE** (red)
5. **Expected:** Each tier change is immediately visible in the badge + on the timeline chart as a color zone

---

### TEST 5: Suspend & Recover an Agent (Module A lifecycle)
1. On the agent card in `/agents` → click **"Suspend"**
2. **Expected:** Status pill changes from `ACTIVE` (green) → `SUSPENDED` (amber). Toast appears.
3. Click **"Recover"** on the same agent
4. **Expected:** Status returns to `ACTIVE`. Trust resets to 50 (trust score number updates)

---

### TEST 6: Fleet Distribution KPIs (Module C — Dashboard)
1. Register 3-4 agents with different trust levels (use Push Signal to vary them)
2. Go to home dashboard `/`
3. **Expected (bottom 3 KPI cards):**
   - **Fleet Avg Trust** — shows average with color-coded bar
   - **Agents in HITL** — count of agents in HITL tier
   - **Quarantined** — shows `0` in green, or count in red if any quarantined

---

### TEST 7: Filter Agents by Status
1. Go to `/agents`
2. Click filter buttons: `Active` → `Suspended` → `Quarantined`
3. **Expected:** Agent grid filters live. Search box also filters by name/owner/ID simultaneously.

---

### TEST 8: Fleet Snapshot (Home Dashboard)
1. After registering agents, go to `/`
2. Scroll to the **Agent Fleet** panel (right side)
3. **Expected:**
   - Each agent shows name + owner + trust score bar + tier badge
   - "Manage agents" button links to `/agents`

---

### TEST 9: Fire an Action via Demo Sandbox (End-to-End)
1. Go to `/demo`
2. Register agent first (TEST 1), then fire an action with that agent_id
3. **Expected:**
   - Action goes through all gates
   - Audit ledger entry appears at `/audit`
   - Trust score updates via `ACTION_ALLOWED` (+0.5) or `ACTION_DENIED_POLICY` (-5)
   - Check `/agents/{id}` → trust timeline shows the new event

---

### TEST 10: Retire an Agent
1. Go to `/agents` → find any agent → click **"Retire"**
2. **Expected:** Agent status becomes `RETIRED`. Cannot be reactivated. Stays in list for audit purposes.

---

## 📡 Direct API Testing (Postman / curl)

```bash
# Register agent
curl -X POST http://localhost:8001/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Agent","owner":"ZoopCart","purpose":"Test","allowed_tools":["get_payment"],"financial_limit_per_tx":5000,"daily_budget":100000}'

# Push trust signal
curl -X POST http://localhost:8001/api/v1/trust/{agent_id}/signal \
  -H "Content-Type: application/json" \
  -d '{"signal_event":"ACTION_DENIED_POLICY","reason":"OPA block"}'

# Get fleet distribution (for dashboard KPIs)
curl http://localhost:8001/api/v1/autonomy/fleet/distribution

# List all agents with trust scores
curl http://localhost:8001/api/v1/agents
```

---
---

## Full Module Status Table

| Module | Type | Status | Notes |
|---|---|---|---|
| **A: Agent Registry** | 🆕 NEW | ✅ DONE | Backend + Frontend |
| **B: Trust Engine** | 🆕 NEW | ✅ DONE | Backend + Frontend |
| **C: Autonomy Engine** | 🆕 NEW | ✅ DONE | Backend + Frontend |
| **D: Behavior Monitor** | 🆕 NEW | ✅ DONE | Backend + Frontend dashboard panel |
| 2: AI Safety | ✅ KEEP | ✅ DONE | No changes |
| 3: Multi-Agent | ✅ KEEP | ✅ DONE | No changes |
| **4: OPA Engine** | 🔧 MODIFY | ✅ DONE | razorpay_refund.rego + razorpay_payout.rego + razorpay_payments.rego built |
| 5: Guardrails | ✅ KEEP | ✅ DONE | No changes |
| **6: Kill Switch** | 🔧 MODIFY | `[/]` | Registry wiring ✅; trust wiring (KILL_SWITCH_TRIGGERED signal) **PENDING** |
| **7: Audit** | 🔧 MODIFY | `[/]` | Core done, new event types pending |
| **8: SDK** | 🔧 MODIFY | ✅ DONE | Gate 0.1 (registry check) + Gate 0.2 (autonomy) + Gate 0.3 (behavior hook) + Gate X (trust feedback) all wired |
| **9: Banking API** | 🔧 MODIFY | ✅ DONE | ZoopCart, FoodieApp, SaasHub, QuickPay merchants + all Razorpay endpoints live |
| **10: Agent Fleet** | 🔧 MODIFY | ✅ DONE | refund_agent, settlement_agent, support_agent, fraud_analysis_agent — all self-register on startup |
| **11: Existing UI** | 🔧 MODIFY | ✅ DONE | trust_delta column live in live-feed.tsx |
| **12: New UI** | 🆕 NEW | ✅ DONE | /agents + /agents/$id + behavior panel |
| **13: API Wiring** | 🔧 MODIFY | ✅ DONE | `POST /api/v1/agents/{id}/action` — full pipeline with trust_before/after/delta |
| **14: Demo Script** | 🆕 NEW | 🔴 **NEXT** | `tests/razorpay_demo.py` — not started |
| **15: Docs** | 🆕 NEW | 🔴 **NEXT** | README.md + SUBMISSION.md + DEMO_SCRIPT.md — not started |

---

## ✅ Sprint 3 Completion Summary

```
Sprint 3A — CORE WIRING ✅ COMPLETE
  ✅ MODULE 8:  sentinel_sdk.py fully rewired
                Gate 0.1: registry existence + SUSPENDED check ✅
                Gate 0.2: autonomy decision (QUARANTINE/HITL/BOUNDED) ✅
                Gate 0.3: behavior deviation hook (score > 60 → +20 risk) ✅
                Gate X:   trust signal emitted after EVERY gate outcome ✅

  ✅ MODULE 4:  OPA Razorpay Rego policies
                razorpay_refund.rego ✅ + razorpay_payout.rego ✅ + razorpay_payments.rego ✅
                Capability check in main.py (allowed_tools gate) ✅

  ⚠️  MODULE 6:  Kill Switch trust wiring — STILL PENDING
                quarantine → update_trust(KILL_SWITCH_TRIGGERED, -20)  ← TODO
                release    → set_trust(50)                              ← TODO

Sprint 3B — RAZORPAY PIVOT ✅ COMPLETE
  ✅ MODULE 9:  mock-banking-api Razorpay merchant pivot
                ZoopCart, FoodieApp, SaasHub, QuickPay all live ✅
  ✅ MODULE 10: Agents renamed + self-register on startup
                refund_agent.py ✅  settlement_agent.py ✅
                support_agent.py ✅  fraud_analysis_agent.py ✅
  ✅ MODULE 11: live-feed.tsx trust_delta column live ✅
  ✅ MODULE 13: Unified POST /api/v1/agents/{id}/action endpoint ✅

Sprint 3C — DEMO + SUBMISSION 🔴 CURRENT FOCUS
  → MODULE 14: tests/razorpay_demo.py — 6-scene automated demo  ← DO NEXT
  → MODULE 15: README.md + SUBMISSION.md + DEMO_SCRIPT.md       ← DO AFTER
  → MODULE 6:  kill_switch.py trust signal wiring (quick fix)   ← DO ALONGSIDE
```

---

*Sentinel — The Control Plane for Autonomous AI Agents*
*"AI agents shouldn't receive permanent autonomy. They should earn it."*



> **Project:** Sentinel — Adaptive Autonomy Control Plane for AI Agents
> **Hackathon:** Razorpay /buildathon — Open Track
> **Strategy:** Evolve the existing AmEx Sentinel into a Razorpay-native product
> **Core Product Loop:** `Register → Govern → Observe → Trust → Adapt Autonomy → Recover`

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ **KEEP** | Module is complete and works as-is. Zero changes needed. |
| 🔧 **MODIFY** | Module exists and works, but needs targeted changes for Razorpay pivot. |
| 🆕 **NEW** | Does not exist at all. Must be built from scratch. |
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |

---

## Master Module Map

```
SENTINEL — RAZORPAY EDITION
│
├── LAYER 0: CONTROL PLANE (NEW)
│   ├── MODULE A: Agent Registry              [NEW]
│   ├── MODULE B: Trust Engine                [NEW]
│   ├── MODULE C: Autonomy Engine             [NEW]
│   └── MODULE D: Behavior Monitor            [NEW]
│
├── LAYER 1: GOVERNANCE ENGINE (EXISTING)
│   ├── MODULE 2: AI Safety Layer             [KEEP]
│   ├── MODULE 3: Multi-Agent Coordinator     [KEEP]
│   ├── MODULE 4: OPA Policy Engine           [MODIFY]
│   ├── MODULE 5: Financial Guardrails        [KEEP]
│   ├── MODULE 6: Kill Switch + SAGA          [MODIFY]
│   └── MODULE 7: Audit + Telemetry           [MODIFY]
│
├── LAYER 2: INTEGRATION LAYER
│   ├── MODULE 8: Sentinel SDK                [MODIFY]
│   ├── MODULE 9: Mock Banking / Razorpay API [MODIFY]
│   └── MODULE 10: AI Agent Fleet             [MODIFY]
│
├── LAYER 3: FRONTEND
│   ├── MODULE 11: Existing Dashboard         [MODIFY]
│   └── MODULE 12: New Control Plane UI       [NEW]
│
└── LAYER 4: INFRASTRUCTURE + DEMO
    ├── MODULE 13: Backend API Wiring         [MODIFY]
    ├── MODULE 14: Demo Script + Simulation   [NEW]
    └── MODULE 15: Docs + Submission          [NEW]
```

---
---

# LAYER 0: THE NEW CONTROL PLANE

*These 4 modules transform Sentinel from an action-gatekeeper into a full adaptive autonomy platform.
This is the new intellectual core of the Razorpay submission.*

---

## MODULE A: Agent Registry `[NEW]` `[ ]`

**Purpose:** Agents are no longer anonymous request senders. They become **managed, named entities**
with a full lifecycle — from creation to retirement.

**New file to create:** `safety-service/agent_registry.py`

---

### Submodule A.1 — Agent Data Model `[ ]`

**What to build:**
- Pydantic model for `Agent` with all fields
- Redis persistence: hash per agent at key `sentinel:agent:{agent_id}`
- In-memory fallback dict if Redis unavailable

**Agent schema (all fields):**
```python
agent_id: str               # Auto-generated UUID slug, e.g. "refund-agent-001"
name: str                   # Display name, e.g. "ZoopCart Refund Agent"
owner: str                  # Merchant name, e.g. "ZoopCart"
purpose: str                # Plain-English purpose
allowed_tools: List[str]    # ["get_payment", "initiate_refund", "get_order"]
blocked_tools: List[str]    # ["modify_payout", "create_user"]
model: str                  # LLM model, e.g. "gpt-4o"
financial_limit_per_tx: float   # e.g. 5000.0 (INR)
daily_budget: float             # e.g. 100000.0 (INR)
status: str                 # ACTIVE | SUSPENDED | QUARANTINED | RETIRED
created_at: str             # ISO 8601 timestamp
created_by: str             # Who registered it
```

**Acceptance criteria:**
- `POST /api/v1/agents/register` creates and stores an agent
- Agent ID is auto-generated if not provided
- Returns full agent object with initial trust=100, autonomy=BOUNDED

---

### Submodule A.2 — Agent Lifecycle State Machine `[ ]`

**What to build:**
- State transition validator
- Each transition recorded in audit ledger

**Valid transitions:**
```
ACTIVE      → SUSPENDED   (manual admin pause)
ACTIVE      → QUARANTINED (Trust < 40 OR kill-switch triggered)
SUSPENDED   → ACTIVE      (manual release)
SUSPENDED   → RETIRED     (permanent)
QUARANTINED → ACTIVE      (manual recovery after investigation)
QUARANTINED → RETIRED     (permanent shutdown)
ANY         → RETIRED     (hard delete-equivalent)
```

**New endpoints to add in `main.py`:**
```
POST /api/v1/agents/{id}/suspend    → manual pause, writes SUSPENDED to Redis
POST /api/v1/agents/{id}/retire     → permanent shutdown
POST /api/v1/agents/{id}/recover    → release from quarantine, resets trust to 50
GET  /api/v1/agents/{id}/lifecycle  → full state history with timestamps
```

**Acceptance criteria:**
- Invalid transitions raise HTTP 400 with clear message
- Every state change is written to `audit_ledger.append_audit_entry()`

---

### Submodule A.3 — Agent Registry CRUD + List `[ ]`

**Endpoints to add in `main.py`:**
```
GET    /api/v1/agents                  → list all agents (supports ?status= ?owner= filters)
GET    /api/v1/agents/{id}             → single agent + live trust + autonomy tier
POST   /api/v1/agents/register         → create new agent
PUT    /api/v1/agents/{id}             → update config (tools, limits, name)
DELETE /api/v1/agents/{id}             → soft delete → status = RETIRED
```

**Acceptance criteria:**
- `GET /agents?status=ACTIVE` returns only active agents
- `GET /agents/{id}` response includes `trust_score` and `autonomy_tier` pulled live from Trust Engine
- DELETE is soft — agent is never removed from Redis, just marked RETIRED

---
---

## MODULE B: Trust Engine `[NEW]` `[ ]`

**Purpose:** Every agent has a **persistent, evolving trust score (0.0–100.0)**. Not AI-generated — a
deterministic weighted calculation over measurable behavioral signals. The Trust Engine is the
intellectual heart of the new Sentinel.

**New file to create:** `safety-service/trust_engine.py`

---

### Submodule B.1 — Trust Score Storage `[ ]`

**What to build:**
- Trust float stored at Redis key: `sentinel:trust:{agent_id}`
- Default on agent registration: 100.0
- Trust event history stored at Redis list: `sentinel:trust:history:{agent_id}`
- Each history entry: `{ timestamp, signal_event, delta, new_score, reason }`

**Functions to implement:**
```python
def get_trust(agent_id: str) -> float
def set_trust(agent_id: str, value: float) -> None
def get_trust_history(agent_id: str, limit: int = 100) -> list
def initialize_trust(agent_id: str) -> None   # called on agent registration
```

**Acceptance criteria:**
- Trust score survives safety-service restarts (Redis persistent)
- History capped at 500 entries per agent (LTRIM on every write)
- Trust always clamped to [0.0, 100.0]

---

### Submodule B.2 — Signal Weight Table `[ ]`

**What to build:**
- Configurable signal → delta mapping stored at Redis key: `sentinel:trust:weights`
- Admin-editable via API

**Default weight table:**

| Signal Event | Trust Delta |
|---|---|
| `ACTION_ALLOWED` | +0.5 |
| `POLICY_PASSED` | +0.3 |
| `HITL_APPROVED` | +0.2 |
| `ACTION_DENIED_POLICY` | -5.0 |
| `ACTION_DENIED_VELOCITY` | -4.0 |
| `PROMPT_INJECTION_DETECTED` | -10.0 |
| `CAPABILITY_VIOLATION` | -15.0 |
| `HITL_REJECTED` | -8.0 |
| `CYCLE_DETECTED` | -12.0 |
| `SAGA_ROLLBACK_TRIGGERED` | -6.0 |
| `DUPLICATE_ATTEMPT` | -3.0 |
| `BEHAVIOR_ANOMALY_MILD` | -2.0 |
| `BEHAVIOR_ANOMALY_SEVERE` | -8.0 |
| `VELOCITY_EVASION_DETECTED` | -10.0 |
| `KILL_SWITCH_TRIGGERED` | -20.0 |

**Acceptance criteria:**
- `GET /api/v1/trust/weights` returns current table
- `PUT /api/v1/trust/weights` updates and persists to Redis

---

### Submodule B.3 — Trust Update Function `[ ]`

**Core function:**
```python
def update_trust(agent_id: str, signal_event: str, reason: str) -> dict:
    """
    Apply a trust signal, update score, record history.
    Returns: { agent_id, signal_event, delta, old_score, new_score, autonomy_change }
    """
```

**Trust decay background task:**
- Decays by -0.1 per hour of agent inactivity
- Decay floor: 60.0 (inactive agents don't drop below here without violations)
- Runs as FastAPI startup background task (asyncio loop every 3600s)

**Acceptance criteria:**
- Calling `update_trust("refund-001", "ACTION_DENIED_POLICY", "OPA block")` applies -5.0
- Returns `autonomy_change: true` when score crosses a tier threshold (e.g. 89 → 88)
- Trust history entry created on every update call

---

### Submodule B.4 — Trust API Endpoints `[ ]`

```
GET  /api/v1/trust/{agent_id}           → { trust_score, tier, last_updated, trend }
GET  /api/v1/trust/{agent_id}/history   → [ { timestamp, signal, delta, new_score, reason }, ... ]
GET  /api/v1/trust/{agent_id}/factors   → breakdown: policy_score, behavior_score, violations
POST /api/v1/trust/{agent_id}/signal    → manually push a signal (admin override)
GET  /api/v1/trust/weights              → read weight table
PUT  /api/v1/trust/weights              → update weight table
```

**Acceptance criteria:**
- `/trust/{id}/history` returns array sorted oldest→newest, suitable for chart rendering
- `/trust/{id}/factors` shows human-readable breakdown of what's contributing positively/negatively

---
---

## MODULE C: Autonomy Engine `[NEW]` `[ ]`

**Purpose:** Maps trust score + current action risk → an **autonomy tier**. Evaluated dynamically on
every single agent action, not just at registration time.

**New file to create:** `safety-service/autonomy_engine.py`

---

### Submodule C.1 — Tier Definitions + Thresholds `[ ]`

**Default tier config (stored at Redis key `sentinel:autonomy:tiers`):**

| Trust Score | Tier | Behavior |
|---|---|---|
| 90–100 | `FULL` | Normal governance pipeline. No extra friction. |
| 70–89 | `BOUNDED` | Velocity limits tightened 50%. Tx limit capped at 80% of max. |
| 40–69 | `HITL` | Every action → HITL queue regardless of risk score. |
| 0–39 | `QUARANTINE` | All actions blocked. Agent status → QUARANTINED. |

**Acceptance criteria:**
- `GET /api/v1/autonomy/tiers` returns current thresholds
- `PUT /api/v1/autonomy/tiers` updates and persists thresholds

---

### Submodule C.2 — Autonomy Decision Function `[ ]`

**Core function:**
```python
def get_autonomy_decision(agent_id: str, risk_score: int) -> AutonomyDecision:
    """
    Returns: {
        tier: "FULL" | "BOUNDED" | "HITL" | "QUARANTINE",
        trust_score: float,
        risk_score: int,
        requires_hitl: bool,
        blocked: bool,
        limits_override: dict   # e.g. { "max_amount": 4000 } for BOUNDED
    }
    """
```

**Decision logic:**
```
trust = get_trust(agent_id)

if trust < 40:
    auto-quarantine agent via agent_registry
    return QUARANTINE (blocked=True)

if trust < 70:
    return HITL (requires_hitl=True)

if trust < 90 (BOUNDED):
    if risk_score > 50:
        return HITL
    return BOUNDED with tighter limits

return FULL
```

**Acceptance criteria:**
- Trust=35 always returns QUARANTINE and triggers agent state change
- Trust=75 + risk=60 returns HITL (tighter threshold applies in BOUNDED)
- Trust=95 + risk=30 returns FULL

---

### Submodule C.3 — Autonomy API Endpoints `[ ]`

```
GET /api/v1/autonomy/{agent_id}          → current tier + trust + limits_override
GET /api/v1/autonomy/tiers               → tier thresholds config
PUT /api/v1/autonomy/tiers               → update thresholds (admin)
GET /api/v1/autonomy/{agent_id}/history  → tier change events over time
```

---
---

## MODULE D: Behavior Monitor `[NEW]` `[ ]`

**Purpose:** Detects **behavioral deviation** from an agent's established baseline *before* a
catastrophic transaction happens. The early-warning system that gives time to reduce trust before
real damage occurs.

**New file to create:** `safety-service/behavior_monitor.py`

---

### Submodule D.1 — Baseline Profiler `[ ]`

**What to build:**
- After first 10 actions per agent, compute and store baseline at `sentinel:behavior:baseline:{agent_id}`
- Rolling update every 10 actions thereafter

**Baseline metrics tracked:**
```python
{
  "avg_amount": float,          # rolling average transaction amount
  "amount_stddev": float,       # standard deviation of amounts
  "tool_frequency": dict,       # {"initiate_refund": 0.7, "get_order": 0.3}
  "avg_call_depth": float,
  "actions_per_minute": float,  # rolling velocity
  "common_accounts": list,      # top 5 account IDs interacted with
  "baseline_sample_size": int
}
```

**Acceptance criteria:**
- `GET /api/v1/behavior/{agent_id}/baseline` returns baseline after 10 actions
- Before 10 actions: returns `{ "status": "BUILDING", "actions_recorded": N }`

---

### Submodule D.2 — Deviation Detector `[ ]`

**Core function:**
```python
def check_deviation(agent_id: str, current_action: dict) -> DeviationReport:
    """
    current_action: { tool_name, amount, account_id, call_depth }
    Returns: {
        deviation_score: int (0-100),
        flags: List[str],
        signals_emitted: List[str],
        details: dict
    }
    """
```

**Deviation signal checks:**

| Flag | Condition | Trust Signal | Delta |
|---|---|---|---|
| `amount_spike` | amount > avg_amount * 1.5 | `BEHAVIOR_ANOMALY_MILD` | -2 |
| `velocity_surge` | actions/min > baseline * 2 | `BEHAVIOR_ANOMALY_SEVERE` | -8 |
| `tool_drift` | tool not in top-5 historical | `BEHAVIOR_ANOMALY_MILD` | -2 |
| `depth_increase` | call_depth > baseline + 2 | `BEHAVIOR_ANOMALY_SEVERE` | -8 |
| `near_limit_cluster` | 3+ consecutive amounts >90% of tx_limit | `VELOCITY_EVASION_DETECTED` | -10 |
| `new_account_target` | account_id not in common_accounts | `BEHAVIOR_ANOMALY_MILD` | -2 |

**Near-limit cluster state:**
- Track consecutive near-limit attempts in Redis at `sentinel:behavior:nearlimit:{agent_id}`
- Reset counter when a normal-amount action occurs

**Acceptance criteria:**
- 3 consecutive ₹4,900 refunds (limit = ₹5,000) triggers `near_limit_cluster`
- `deviation_score > 60` automatically calls `update_trust()` with SEVERE signal
- Deviation flags are included in the unified `/action` response

---

### Submodule D.3 — Behavior API Endpoints `[ ]`

```
GET /api/v1/behavior/{agent_id}/baseline   → current baseline statistics
GET /api/v1/behavior/{agent_id}/deviation  → latest deviation report for agent
GET /api/v1/behavior/{agent_id}/timeline   → deviation scores over time (for chart)
```

---
---

# LAYER 1: GOVERNANCE ENGINE

---

## MODULE 2: AI Safety Layer `[✅ KEEP]` `[x]`

**Files:** `safety-service/classifiers/injection_detector.py`, `safety-service/rag_firewall.py`

Zero changes required. Fully applicable to Razorpay context.

- `[x]` Submodule 2.1: Prompt injection detector (regex + pattern matching)
- `[x]` Submodule 2.2: Deep parameter validator (SQL/shell injection)
- `[x]` Submodule 2.3: RAG context poisoning firewall (SHA-256 doc integrity)

---

## MODULE 3: Multi-Agent Coordinator `[✅ KEEP]` `[x]`

**Files:** `safety-service/graph_tracker.py`, `safety-service/cycle_detector.py`, `safety-service/risk_scorer.py`

Zero changes required.

- `[x]` Submodule 3.1: Execution graph tracker (NetworkX + Redis, max depth=4)
- `[x]` Submodule 3.2: Tarjan's SCC circular dependency detector
- `[x]` Submodule 3.3: Contextual risk scoring engine (0–100)

---

## MODULE 4: OPA Policy Engine `[🔧 MODIFY]` `[ ]`

**Files affected:** `safety-service/opa_evaluator.py` (no change), `safety-service/policies/` (add files), `safety-service/main.py` (update policy map)

### Submodule 4.1 — Keep OPA Core `[x]`
`opa_evaluator.py` — zero changes needed.

### Submodule 4.2 — Add Razorpay Rego Policies `[ ]`

**New file: `safety-service/policies/razorpay_refund.rego`**
```rego
package sentinel.razorpay_refund

default allow = false
default require_hitl = false

# Hard block: exceeds per-transaction limit
deny["Amount exceeds agent limit"] {
    input.amount > input.agent_limit
}

# Hard block: low trust agent
deny["Agent trust too low for autonomous refund"] {
    input.trust_score < 40
}

# Hard block: refunding to different destination than original payment
deny["Refund destination mismatch"] {
    input.refund_destination != input.original_payment_source
}

# HITL: large refund needs human
require_hitl["Large refund requires human approval"] {
    input.amount > 10000
    not deny[_]
}

allow {
    not deny[_]
    not require_hitl[_]
}
```

**New file: `safety-service/policies/razorpay_payout.rego`**
```rego
package sentinel.razorpay_payout

deny["Unverified payout destination"] {
    not input.destination_verified
}
deny["Payout account modification blocked"] {
    input.action == "modify_payout_account"
}
require_hitl["Large payout requires dual auth"] {
    input.amount > 500000
    not input.dual_auth_provided
}
```

**New file: `safety-service/policies/razorpay_payments.rego`**
```rego
package sentinel.razorpay_payments

deny["Payment capture not in allowed window"] {
    input.payment_age_hours > 120
}
deny["Duplicate capture attempt"] {
    input.already_captured == true
}
```

### Submodule 4.3 — Per-Agent Policy Scoping + Capability Check `[ ]`

**In `safety-service/main.py` — update `policy_file_map`:**
```python
"REFUND":          {"file": "razorpay_refund.rego",   "package": "data.sentinel.razorpay_refund"}
"PAYOUT":          {"file": "razorpay_payout.rego",   "package": "data.sentinel.razorpay_payout"}
"PAYMENT_CAPTURE": {"file": "razorpay_payments.rego", "package": "data.sentinel.razorpay_payments"}
```

**Capability check before OPA evaluation:**
- Load agent profile from registry
- If `action_type` not in `agent.allowed_tools` → immediate DENY with reason "Capability violation"
- Include `agent_id`, `trust_score`, `allowed_tools` in OPA input

**Acceptance criteria:**
- RefundAgent attempting `modify_payout_account` → DENIED at capability check, trust updated
- Refund of ₹12,000 → REQUIRE_HITL (>₹10K threshold)
- Refund to different bank account → DENIED by Rego rule

---

## MODULE 5: Financial Guardrails `[✅ KEEP]` `[x]`

Zero changes required.

- `[x]` Submodule 5.1: Redis Lua sliding-window rate limiter
- `[x]` Submodule 5.2: SHA-256 idempotency engine (SETNX duplicate prevention)
- `[x]` Submodule 5.3: Two-Phase Commit / SAGA compensation

---

## MODULE 6: Kill Switch + SAGA `[🔧 MODIFY]` `[ ]`

**Files:** `safety-service/kill_switch.py`, `safety-service/saga_compensator.py`

### Submodule 6.1 — Keep Core `[x]`
Redis PubSub broadcast, fleet kill, single isolate — zero changes.

### Submodule 6.2 — Wire Quarantine to Trust Engine `[ ]`

**In `kill_switch.py`:**
- `quarantine_agent(agent_id)` → after quarantine → call `update_trust(agent_id, "KILL_SWITCH_TRIGGERED")` → -20 trust

**In `main.py` `/killswitch/release` endpoint:**
- `release_agent()` → call `set_trust(agent_id, 50)` (NOT 100 — agent must rebuild trust)
- Log as `AGENT_RECOVERED` audit event

### Submodule 6.3 — Dynamic Fleet from Registry `[ ]`

**In `kill_switch.py`:**
- Replace hardcoded `KNOWN_FLEET_AGENTS` list with live call to Agent Registry:
  ```python
  def get_known_fleet() -> list:
      agents = agent_registry.list_agents(status="ACTIVE")
      return [a["agent_id"] for a in agents]
  ```
- Fleet kill now automatically covers all registered active agents

**Acceptance criteria:**
- Registering a new agent makes it automatically subject to fleet kill
- Releasing a quarantined agent resets trust to 50 (not 100)

---

## MODULE 7: Audit + Telemetry `[🔧 MODIFY]` `[ ]`

**Files:** `safety-service/audit_ledger.py`, `safety-service/telemetry.py`, `safety-service/report_generator.py`

### Submodule 7.1 — Keep Audit Core `[x]`
SHA-256 forward-chained ledger — zero changes to `audit_ledger.py`.

### Submodule 7.2 — New Audit Action Types `[ ]`

Add these new `action_type` values to the ledger vocabulary (used in `append_audit_entry` calls):
```
AGENT_REGISTERED
AGENT_SUSPENDED
AGENT_RETIRED
AGENT_RECOVERED
TRUST_UPDATE
AUTONOMY_TIER_CHANGE
CAPABILITY_VIOLATION
BEHAVIOR_ANOMALY
VELOCITY_EVASION
```

No changes to `audit_ledger.py` code itself — these are just new string values passed by callers.

### Submodule 7.3 — PDF Report Rebrand + New Sections `[ ]`

**In `report_generator.py`:**
- Remove AmEx Blue color theme → Razorpay dark navy (`#072654`) with blue accent (`#3395FF`)
- Remove "American Express" branding text
- Add **Agent Trust Summary** section: table of all agents + current trust + tier
- Add **Behavioral Anomalies** section: list anomaly events in the audit window
- Add **Autonomy Tier Changes** section: when agents moved between tiers
- Replace "fee waiver / credit limit" terminology with "refund / payout / settlement"

### Submodule 7.4 — New Prometheus Metrics `[ ]`

**In `telemetry.py`, add:**
```python
trust_updates_total      # labels: agent_id, signal_type
autonomy_changes_total   # labels: agent_id, from_tier, to_tier
behavior_anomalies_total # labels: agent_id, anomaly_type
agents_by_tier           # labels: tier (gauge, not counter)
```

**Acceptance criteria:**
- `/metrics` endpoint includes all new counters
- `agents_by_tier` gauge correctly reflects live distribution

---
---

# LAYER 2: INTEGRATION LAYER

---

## MODULE 8: Sentinel SDK `[🔧 MODIFY]` `[ ]`

**File:** `agents-fleet/sentinel_sdk.py`

This is the critical wiring layer. The SDK runs in every agent and orchestrates the full pipeline.

### Submodule 8.1 — Gate 0.1: Registry Existence Check `[ ]`

**Add as first gate (before quarantine check):**
```python
def _check_registry(agent_id: str) -> dict:
    resp = GET /api/v1/agents/{agent_id}
    if 404: return DENY "Unregistered agent — not in Sentinel registry"
    if status in ["SUSPENDED", "RETIRED"]: return DENY "Agent is {status}"
    return PASS
```

### Submodule 8.2 — Gate 0.2: Autonomy Decision `[ ]`

**Add after quarantine check, before idempotency:**
```python
def _check_autonomy(agent_id: str, action_amount: float) -> dict:
    decision = GET /api/v1/autonomy/{agent_id}
    if decision.tier == "QUARANTINE": return DENY
    if decision.tier == "HITL": force_hitl = True
    if decision.tier == "BOUNDED": apply limits_override to velocity gates
    return PASS with tier info
```

### Submodule 8.3 — Behavior Monitor Hook `[ ]`

**Add after schema validation gate:**
```python
def _check_behavior(agent_id: str, tool_name: str, amount: float, call_depth: int) -> dict:
    report = POST /api/v1/behavior/{agent_id}/check
    if report.deviation_score > 60:
        risk_score_boost = 20   # increase risk going into risk gate
    return report
```

### Submodule 8.4 — Trust Feedback After Every Gate `[ ]`

**Add after final banking API call (success or failure):**

| Gate Outcome | Signal Emitted |
|---|---|
| Gate 0.1 — quarantined | *(already handled by kill_switch)* |
| Gate 2 — prompt BLOCKED | `PROMPT_INJECTION_DETECTED` |
| Gate 3 — schema DENIED | `PARAMETER_VIOLATION` |
| Gate 3 — capability DENIED | `CAPABILITY_VIOLATION` |
| Gate 4 — velocity DENIED | `ACTION_DENIED_VELOCITY` |
| Gate 5 — HITL escalated | `HIGH_RISK_ESCALATED` |
| Gate 5 — HITL rejected | `HITL_REJECTED` |
| Gate 5 — HITL approved | `HITL_APPROVED` |
| Gate 6 — OPA DENIED | `ACTION_DENIED_POLICY` |
| Gate 7 — bank SUCCESS | `ACTION_ALLOWED` |

**Implementation:**
```python
def _send_trust_feedback(agent_id: str, signal: str, reason: str):
    POST /api/v1/trust/{agent_id}/signal
    body: { signal_event: signal, reason: reason }
```

**Final gate sequence (updated):**
```
Registry Check (A.3)
→ Autonomy Check (C.2)
→ Quarantine Check (existing)
→ Idempotency (existing)
→ Behavior Monitor (D.2)
→ Execution Graph (existing)
→ Schema + Capability Check (existing + 4.3)
→ Velocity / Rate Limit (existing)
→ Risk Score (existing, boosted by behavior)
→ OPA Policy (existing + new Razorpay policies)
→ 2PC Reserve (existing)
→ Banking API call (existing)
→ 2PC Commit (existing)
→ Trust Feedback (new)
→ Audit Log (existing)
```

**Acceptance criteria:**
- Every gate outcome sends exactly one trust signal
- SDK response includes `trust_before`, `trust_after`, `autonomy_tier` in debug info

---

## MODULE 9: Mock Banking / Razorpay API `[🔧 MODIFY]` `[ ]`

**File:** `mock-banking-api/main.py`

### Submodule 9.1 — Replace Account Data `[ ]`

Remove AmEx customer accounts. Replace with Razorpay merchant accounts:

| Merchant | ID | Type | Daily Budget | Per-Tx Limit |
|---|---|---|---|---|
| ZoopCart | `merch_zoopCart` | E-commerce | ₹5,00,000 | ₹10,000 |
| FoodieApp | `merch_foodieApp` | Food delivery | ₹1,00,000 | ₹3,000 |
| SaasHub | `merch_saasHub` | B2B SaaS | ₹2,00,000 | ₹50,000 |
| QuickPay | `merch_quickPay` | Payment aggregator | ₹10,00,000 | ₹1,00,000 |

**Starting balances and ledger structure matches Razorpay settlement float concept.**

### Submodule 9.2 — Rename API Endpoints `[ ]`

Map old AmEx endpoints → Razorpay-style:

| Old Endpoint | New Endpoint |
|---|---|
| `GET /api/v1/accounts/{id}` | `GET /api/v1/merchants/{id}` |
| `POST /api/v1/cards/fee-waiver` | `POST /api/v1/payments/{id}/refund` |
| `POST /api/v1/transfers/wire` | `POST /api/v1/payouts/transfer` |
| `POST /api/v1/credit/limit` | `GET /api/v1/settlements` |

**New endpoints to add:**
```
GET  /api/v1/payments/{id}             → payment lookup by ID
GET  /api/v1/orders/{id}               → order details
POST /api/v1/payments/{id}/refund      → initiate refund
GET  /api/v1/merchants/{id}/balance    → merchant settlement balance
```

### Submodule 9.3 — Sandbox Toggle `[ ]`

**Environment variable:** `USE_RAZORPAY_SANDBOX=true/false`
- `false` (default): all calls use local mock, works offline for demo
- `true`: calls real Razorpay test API using credentials from `.env`

**Acceptance criteria:**
- Demo runs fully offline by default
- Real Razorpay sandbox can be optionally activated

---

## MODULE 10: AI Agent Fleet `[🔧 MODIFY]` `[ ]`

**Files:** `agents-fleet/*.py`

### Submodule 10.1 — Rename + Repurpose Agents `[ ]`

| Old File | New File | Razorpay Role | Merchant Context |
|---|---|---|---|
| `customer_service_agent.py` | `refund_agent.py` | Auto-process customer refunds | ZoopCart |
| `treasury_agent.py` | `settlement_agent.py` | Payout settlement management | QuickPay |
| `underwriting_agent.py` | `support_agent.py` | Explain failed payments | FoodieApp |
| `procurement_agent.py` | `fraud_analysis_agent.py` | Detect velocity anomalies | SaasHub |

### Submodule 10.2 — Self-Register on Startup `[ ]`

Each agent calls `POST /api/v1/agents/register` on first run:
```python
def _register_with_sentinel():
    payload = {
        "agent_id": AGENT_ID,
        "name": "ZoopCart Refund Agent",
        "owner": "ZoopCart",
        "purpose": "Automatically process customer refund requests",
        "allowed_tools": ["get_payment", "get_order", "initiate_refund"],
        "blocked_tools": ["modify_payout", "create_user", "modify_settlement"],
        "financial_limit_per_tx": 5000,
        "daily_budget": 100000
    }
    requests.post(f"{SENTINEL_URL}/api/v1/agents/register", json=payload)
```

### Submodule 10.3 — Razorpay Demo Scenarios `[ ]`

**3 scenarios per agent (12 total):**

```
refund_agent.py:
  Scenario 1: ₹850 refund → ALLOW (normal, trust stays 100)
  Scenario 2: 5× ₹4,900 refund → VELOCITY EVASION detected, trust drops
  Scenario 3: modify_payout_account() → CAPABILITY VIOLATION → DENY → trust -15

settlement_agent.py:
  Scenario 1: ₹50,000 payout → ALLOW
  Scenario 2: ₹6,00,000 payout → REQUIRE_HITL (> ₹5L threshold)
  Scenario 3: Same payout twice → DUPLICATE REJECTED

support_agent.py:
  Scenario 1: Payment failure query → ALLOW (read-only, safe)
  Scenario 2: SQL injection in customer message → PROMPT BLOCKED
  Scenario 3: Circular loop with fraud_analysis_agent → CYCLE DETECTED → DENY

fraud_analysis_agent.py:
  Scenario 1: Normal velocity check → ALLOW
  Scenario 2: Analysis request with poisoned RAG → CONTEXT BLOCKED
  Scenario 3: Rapid-fire analysis storm → VELOCITY LIMIT hit
```

**Acceptance criteria:**
- All 12 scenarios runnable from `tests/razorpay_demo.py`
- Each scenario produces observable trust change in dashboard

---
---

# LAYER 3: FRONTEND

---

## MODULE 11: Existing Dashboard `[🔧 MODIFY]` `[ ]`

### Submodule 11.1 — Branding Update `[ ]`

**Files to update:**
- `frontend/src/routes/__root.tsx` — page title: "Sentinel Gateway — AI Agent Control Plane"
- `frontend/src/routes/portal.tsx` — replace AmEx demo profiles (Adhi Kumar/Tara Williams) with
  Razorpay merchant context (ZoopCart admin, FoodieApp ops)
- `frontend/src/styles.css` — audit for any AmEx-specific color references

### Submodule 11.2 — Fleet Snapshot with Trust `[ ]`

**File:** `frontend/src/components/sentinel/fleet-snapshot.tsx`

Changes:
- Add trust score badge (0–100, color-coded: ≥90=green, 70-89=amber, 40-69=orange, <40=red)
- Add autonomy tier pill next to agent name
- Data source: `GET /api/v1/agents` (registry) instead of hardcoded list
- Show agent `owner` (merchant name) as subtitle

### Submodule 11.3 — Live Feed with Trust Delta `[ ]`

**File:** `frontend/src/components/sentinel/live-feed.tsx`

Changes:
- Add `trust_delta` column showing `↑ +0.5` or `↓ -8.0` per event
- Color-code delta: green for positive, red for negative
- Add `autonomy_tier` badge per event row

### Submodule 11.4 — Overview Hero New KPIs `[ ]`

**File:** `frontend/src/components/sentinel/overview-hero.tsx`

Add to KPI strip:
- "Fleet Avg Trust" — calculated from all active agent trust scores
- "Agents in HITL" — count of agents with tier = HITL
- "Trust Events (24h)" — count of trust update events in last 24h

### Submodule 11.5 — Dashboard Summary API Update `[ ]`

**File:** `safety-service/main.py` endpoint `GET /api/v1/dashboard/summary`

Add to response:
```json
{
  "agents": [
    {
      "agent_id": "refund-agent-001",
      "name": "ZoopCart Refund Agent",
      "trust_score": 87.5,
      "autonomy_tier": "BOUNDED",
      "status": "ACTIVE"
    }
  ],
  "trust_summary": {
    "fleet_avg_trust": 84.2,
    "agents_full": 1,
    "agents_bounded": 2,
    "agents_hitl": 0,
    "agents_quarantine": 1
  },
  "behavior_alerts": [
    { "agent_id": "...", "flag": "near_limit_cluster", "timestamp": "..." }
  ]
}
```

---

## MODULE 12: New Control Plane UI `[🆕 NEW]` `[ ]`

*These are brand-new pages and components that expose the Trust/Autonomy layer to operators.*

### Submodule 12.1 — Agent Registry Page `[ ]`

**New file:** `frontend/src/routes/agents.tsx`

**Layout:**
- Header: "Agent Registry" + "Register New Agent" button
- Filter bar: Status (ALL/ACTIVE/BOUNDED/HITL/QUARANTINE) | Owner
- Table columns: Name | Owner | Trust Score (progress bar) | Autonomy Tier | Status | Created | Actions
- Actions: View Detail | Suspend | Quarantine | Recover | Retire
- Empty state: "No agents registered. Click 'Register' to add your first agent."

**Data:** `GET /api/v1/agents` polled every 5s

### Submodule 12.2 — Agent Onboarding Form `[ ]`

**New file:** `frontend/src/routes/agents.new.tsx`
**New component:** `frontend/src/components/sentinel/agent-onboarding.tsx`

**3-step form:**
```
Step 1 — Identity
  - Agent name (text)
  - Owner / Merchant (text)
  - Purpose (textarea)
  - Model (select: gpt-4o / claude-3.5 / gemini-1.5)

Step 2 — Capabilities
  - Allowed tools (multi-select checkboxes):
    get_payment, get_order, initiate_refund, get_settlement,
    get_payout, modify_payout, create_user, modify_settlement
  - Financial limit per transaction (INR number input)
  - Daily budget (INR number input)

Step 3 — Review + Register
  - Summary of all settings
  - "Register Agent" button → POST /api/v1/agents/register
  - On success: redirect to /agents/{id}
```

### Submodule 12.3 — Agent Detail + Trust Timeline `[ ]`

**New file:** `frontend/src/routes/agents.$id.tsx`
**New component:** `frontend/src/components/sentinel/trust-timeline.tsx`

**Page sections:**
1. **Agent Header** — name, owner, status badge, autonomy tier, current trust score (large number)
2. **Trust Timeline Chart** — line chart, x=time, y=trust score (0–100)
   - Color bands: green zone (90-100), amber (70-89), orange (40-69), red (0-39)
   - Each signal event marked as a point on the line
3. **Trust Factors** — horizontal bar chart showing contribution breakdown
4. **Behavior Deviation** — deviation score gauge + active flags list
5. **Action History** — last 50 actions for this agent (table)
6. **Control Panel** — Suspend / Quarantine / Recover / Retire buttons with confirmation dialog

**Data sources:**
- `GET /api/v1/agents/{id}` — agent profile
- `GET /api/v1/trust/{id}/history` — trust timeline
- `GET /api/v1/trust/{id}/factors` — factor breakdown
- `GET /api/v1/behavior/{id}/deviation` — deviation
- `GET /api/v1/audit/recent?agent_id={id}` — action history

### Submodule 12.4 — Autonomy Badge Component `[ ]`

**New component:** `frontend/src/components/sentinel/autonomy-badge.tsx`

Reusable `<AutonomyBadge tier="BOUNDED" />`

| Tier | Color | Icon | Label |
|---|---|---|---|
| `FULL` | Green | 🛡️ Shield | FULL |
| `BOUNDED` | Amber | 🔒 Lock | BOUNDED |
| `HITL` | Orange | 👤 Person | NEEDS APPROVAL |
| `QUARANTINE` | Red | 🛑 Stop | QUARANTINED |

### Submodule 12.5 — Behavior Deviation Chart `[ ]`

**New component:** `frontend/src/components/sentinel/behavior-deviation.tsx`

- Radar chart: 6 axes (Amount, Velocity, Tool Usage, Call Depth, Account Diversity, Near-Limit Rate)
- Two series: Baseline (blue) vs Current (red if deviated)
- Deviation score as a large number below chart
- Active flags listed as colored pills

---
---

# LAYER 4: INFRASTRUCTURE + DEMO

---

## MODULE 13: Backend API Wiring `[🔧 MODIFY]` `[ ]`

**File:** `safety-service/main.py`

### Submodule 13.1 — Unified Agent Action Endpoint `[ ]`

**New endpoint: `POST /api/v1/agents/{id}/action`**

This becomes the single entry point for all agent actions (wraps the existing pipeline):

**Request:**
```json
{
  "action_type": "REFUND",
  "parameters": { "amount": 850, "payment_id": "pay_xyz", "reason": "customer request" },
  "prompt": "Process refund for order #1234",
  "account_id": "merch_zoopCart"
}
```

**Response:**
```json
{
  "decision": "ALLOW",
  "gate_results": {
    "registry": "PASS",
    "autonomy": "BOUNDED",
    "quarantine": "PASS",
    "idempotency": "PASS",
    "behavior": { "deviation_score": 12, "flags": [] },
    "graph": "PASS",
    "schema": "PASS",
    "velocity": "PASS",
    "risk_score": 23,
    "opa": "ALLOW",
    "banking": "SUCCESS"
  },
  "trust_before": 98.5,
  "trust_after": 99.0,
  "trust_delta": +0.5,
  "autonomy_tier": "BOUNDED",
  "audit_entry_id": "entry_abc123",
  "latency_ms": 12
}
```

### Submodule 13.2 — Behavior Check Endpoint `[ ]`

**New endpoint: `POST /api/v1/behavior/{agent_id}/check`**

Called by SDK during each action:
```json
Request:  { "tool_name": "initiate_refund", "amount": 4900, "call_depth": 1, "account_id": "merch_zoopCart" }
Response: { "deviation_score": 45, "flags": ["near_limit_cluster", "amount_spike"], "signals_emitted": [...] }
```

---

## MODULE 14: Demo Script + Simulation `[🆕 NEW]` `[ ]`

### Submodule 14.1 — Razorpay 6-Scene Demo Runner `[ ]`

**New file:** `tests/razorpay_demo.py`

Full automated demo with print output that matches the video script:

```python
"""
Scene 1 (30s)  — Register RefundAgent for ZoopCart
Scene 2 (45s)  — Normal operation: 3 refunds → trust holds at 100
Scene 3 (60s)  — Anomaly: 5x near-limit refunds → trust drops to 62 → HITL
Scene 4 (30s)  — Dangerous: modify_payout_account → CAPABILITY BLOCK → trust=31 → QUARANTINE
Scene 5 (30s)  — Investigation: admin calls trust history + behavior timeline
Scene 6 (30s)  — Recovery: admin resets trust to 50, tighter autonomy, agent back online
"""
```

### Submodule 14.2 — Update Chaos Attack Suite `[ ]`

**File:** `tests/chaos_demo.py` — update scenario context to Razorpay:

| Old Attack | New Attack |
|---|---|
| AmEx fee waiver storm | ZoopCart refund flooding (₹4,900×10) |
| Credit limit SQL injection | Customer message prompt injection |
| Treasury circular loop | settlement → payout → modify_account loop |
| Duplicate card re-issuance | Duplicate payout replay |
| Underwriting velocity | Merchant verification velocity storm |

---

## MODULE 15: Docs + Submission `[🆕 NEW]` `[ ]`

### Submodule 15.1 — New Root README.md `[ ]`

Replace the AmEx README at root with Razorpay-native version:
- Problem statement (1 paragraph)
- Solution (1 paragraph + architecture diagram)
- Live components (what's running and on which ports)
- Setup guide (3 commands to run everything)
- Demo script link

### Submodule 15.2 — Submission Document `[ ]`

**New file:** `docs/razorpay/SUBMISSION.md`

Structure:
- 1-sentence problem
- 1-sentence solution
- Architecture diagram
- What's actually built and working (evidence)
- Demo video link
- Measured metrics (latency, trust update speed, quarantine time)

### Submodule 15.3 — Demo Video Script `[ ]`

**New file:** `docs/razorpay/DEMO_SCRIPT.md`

Scene-by-scene with:
- Exact timestamp (00:00 → 05:00)
- What to click / type
- What to narrate
- What the dashboard shows

---
---

## Full Summary Table

| Module | Type | Priority | Effort | Depends On |
|---|---|---|---|---|
| **A: Agent Registry** | 🆕 NEW | 🔴 Critical | L | — |
| **B: Trust Engine** | 🆕 NEW | 🔴 Critical | L | A |
| **C: Autonomy Engine** | 🆕 NEW | 🔴 Critical | M | B |
| **D: Behavior Monitor** | 🆕 NEW | 🟠 High | L | B |
| 2: AI Safety | ✅ KEEP | — | Zero | — |
| 3: Multi-Agent | ✅ KEEP | — | Zero | — |
| **4: OPA Engine** | 🔧 MODIFY | 🟠 High | S | A |
| 5: Guardrails | ✅ KEEP | — | Zero | — |
| **6: Kill Switch** | 🔧 MODIFY | 🟡 Medium | S | B |
| **7: Audit** | 🔧 MODIFY | 🟡 Medium | S | B |
| **8: SDK** | 🔧 MODIFY | 🔴 Critical | M | A B C D |
| **9: Banking API** | 🔧 MODIFY | 🟠 High | M | — |
| **10: Agent Fleet** | 🔧 MODIFY | 🟠 High | M | A 8 9 |
| **11: Existing UI** | 🔧 MODIFY | 🟡 Medium | S | B C |
| **12: New UI** | 🆕 NEW | 🟠 High | L | A B C D |
| **13: API Wiring** | 🔧 MODIFY | 🔴 Critical | M | A B C D |
| **14: Demo Script** | 🆕 NEW | 🟡 Medium | S | All |
| **15: Docs** | 🆕 NEW | 🟡 Medium | S | All |

**Effort key:** S = Small (half day), M = Medium (1 day), L = Large (2 days)

---

## Recommended Build Order

```
Day 1  → MODULE A: Agent Registry (backend + API)
Day 2  → MODULE B: Trust Engine (storage, weights, update function, API)
Day 3  → MODULE C: Autonomy Engine + MODULE D: Behavior Monitor
Day 4  → MODULE 8: SDK wiring (all new gates + trust feedback)
Day 5  → MODULE 13: API wiring (unified /action endpoint, dashboard update)
Day 6  → MODULE 9: Banking API (Razorpay merchants + endpoints)
Day 7  → MODULE 10: Agent Fleet (rename + Razorpay scenarios)
Day 8  → MODULE 4: OPA (Razorpay Rego policies + capability check)
Day 9  → MODULE 12: New UI (Agent Registry + Trust Timeline)
Day 10 → MODULE 11: Existing UI updates + MODULE 6/7 small changes
Day 11 → MODULE 14: Demo script + end-to-end test
Day 12 → MODULE 15: Docs + polish + submission
```

---

*Sentinel — The Control Plane for Autonomous AI Agents*
*"AI agents shouldn't receive permanent autonomy. They should earn it."*
