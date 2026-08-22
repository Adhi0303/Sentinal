# Sentinel — What Is Actually Implemented

> **Last Updated:** 2026-08-22 (v2 — Priority 2 backend fixes applied)
> This document is a ground-truth audit of every feature that is **fully coded and functional** in the repository. It describes what each piece does and how it connects to everything else.

---

## System Overview

Sentinel is a **Zero-Trust Governance Control Plane** that sits inline between autonomous AI agents and core banking / payment APIs. Every agent action is intercepted and evaluated through a sequential multi-gate pipeline before it reaches any financial API. The system is composed of four services that run simultaneously:

| Service | Port | Technology | Role |
|---|---|---|---|
| `safety-service` | 8001 | FastAPI + Python | The control plane brain |
| `mock-banking-api` | 8000 | FastAPI + Python | Simulated Razorpay + banking backend |
| `agents-fleet` | — | Python + LangChain + Groq | 7 autonomous LLM agents |
| `frontend` | 3000 | React + TanStack Router | Operator dashboard |

All services share a **Redis** instance (port 6379) as the real-time state store.

---

## Part 1: Agent Fleet (7 Agents)

All agents live in `agents-fleet/`. Every agent:
- **Self-registers** on startup via `register_on_startup()` — creates its record in the Sentinel registry with declared capabilities, financial limits, and autonomy tier.
- Calls the **Sentinel SDK** (`execute_governed_tool`) for every action — never calls the banking API directly.
- Uses **LangChain + Groq** for LLM reasoning and tool selection.
- Has a **hard-coded agent ID**, merchant association, and allowed tool list enforced by the registry.

| Agent File | Agent ID | Merchant | Capabilities |
|---|---|---|---|
| `refund_agent.py` | `refund-agent-001` | ZoopCart | GET_PAYMENT, GET_ORDER, REFUND, PAYMENT_CAPTURE |
| `settlement_agent.py` | `settlement-agent-001` | QuickPay | GET_BALANCE, GET_SETTLEMENT, PAYOUT |
| `fraud_analysis_agent.py` | `fraud-agent-001` | SaasHub | GET_PAYMENT, GET_TRANSACTIONS, PAYMENT_CAPTURE |
| `support_agent.py` | `support-agent-001` | FoodieApp | GET_ORDER, GET_PAYMENT |
| `customer_service_agent.py` | `cs-agent-001` | (legacy) | FEE_WAIVER, WIRE_TRANSFER |
| `treasury_agent.py` | `treasury-agent-001` | (legacy) | WIRE_TRANSFER |
| `underwriting_agent.py` | `underwriting-agent-001` | (legacy) | CREDIT_LIMIT_INCREASE |

---

## Part 2: The Sentinel SDK (`agents-fleet/sentinel_sdk.py`)

This is the **most critical file** — the inline interceptor that every agent imports. It implements the full 9-gate pipeline:

### Gate 0.1 — Registry Check
- Calls `GET /api/v1/agents/{agent_id}` on the safety-service.
- Denies agents that are not registered, `SUSPENDED`, or `RETIRED`.
- Fails **open** on network error (availability > security since 8 more gates follow).

### Gate 0.2 — Autonomy Tier Check
- Calls `GET /api/v1/autonomy/{agent_id}`.
- `QUARANTINE` → hard block (fails **closed**).
- `HITL` → sets `force_hitl` flag, all actions escalate to human approval.
- `BOUNDED` → attaches tighter velocity/amount `limits_override` for downstream gates.

### Gate 0.3 — Behavior Deviation Pre-Check
- Calls `POST /api/v1/behavior/{agent_id}/check`.
- If `deviation_score > 60` → applies `+20` risk boost to the risk scoring gate.
- Non-blocking: gate failure does not stop the action.

### Gate 0 — Quarantine State (Redis Direct Read)
- Reads `agent:state:{agent_id}` from Redis **directly** — no HTTP call, sub-millisecond.
- Hard blocks `QUARANTINED` agents with no network dependency.

### Read-Only Fast-Path (NEW)
- Actions `GET_PAYMENT`, `GET_ORDER`, `GET_BALANCE`, `GET_SETTLEMENT`, `GET_TRANSACTIONS` bypass OPA, velocity, risk scoring, and idempotency (they don't mutate financial state).
- Still passes Gate 0.1 and Gate 0 (quarantine).

### Gate 0.5 — Idempotency (Redis Lua)
- Generates a deterministic SHA-256 hash key from `(agent_id, action_type, parameters)`.
- Duplicate requests within the window return the cached result — banking API is never double-called.
- Concurrent duplicates (same request mid-flight) are blocked.

### Gate 1 — JSON Schema Validation
- For `FEE_WAIVER` actions: validates parameters against a JSON Schema file at `api/schemas/fee_waiver_schema.json`.

### Gate 2 — Deep Parameter Validation (Injection Detection)
- Regex scan of all string parameters for SQL injection and shell injection patterns.
- On match: emits `PROMPT_INJECTION_DETECTED` trust signal and denies.

### Gate 3 — Redis Velocity / Rate Limiting (Lua Script)
- Uses a sliding-window Lua script on Redis sorted sets.
- Hard cap: `$10M INR / minute` across all Razorpay actions (`REFUND`, `PAYOUT`, `PAYMENT_CAPTURE`) and legacy actions.

### Gate 4 — Contextual Risk Scoring
- Calls `POST /api/v1/risk/score`.
- Factors: amount size, account flag, call depth, behavior boost from Gate 0.3.
- Returns score 0–100 + risk level + factors list.
- Behavior boost of +20 applied if Gate 0.3 detected high deviation.

### Gate 5 — OPA Policy Evaluation
- Calls `POST /api/v1/policy/evaluate`.
- Maps action type to the correct Rego policy file (see Part 4).
- Returns `ALLOW` / `DENY` / `REQUIRE_HITL` with reason.
- Fails **closed** — policy engine unreachable → `DENY`.

### Banking API Forwarding (after all gates pass)
Routed action types:
- `FEE_WAIVER` → `POST /api/v1/cards/fee-waiver`
- `WIRE_TRANSFER` → Two-Phase Commit protocol (see Part 6)
- `CREDIT_LIMIT_INCREASE` → `POST /api/v1/credit/limit-increase`
- `REFUND` → `POST /api/v1/payments/{payment_id}/refund`
- `PAYOUT` → `POST /api/v1/payouts`
- `PAYMENT_CAPTURE` → `POST /api/v1/payments/{payment_id}/capture`

---

## Part 3: Safety Service (`safety-service/main.py` + 15 modules)

The brain of Sentinel. 1,126 lines, 40+ REST endpoints.

### Module 2 — Prompt Safety
- **2.1 Prompt Injection Detector**: Multi-pattern regex + LlamaGuard classifier (`classifiers/injection_detector.py`). Returns `SAFE` or `BLOCKED`. Blocked prompts are written to the audit ledger.
- **2.3 RAG Firewall** (`rag_firewall.py`): SHA-256 hash integrity check on retrieved RAG documents. Detects context poisoning.

### Module 3 — Execution Graph + Risk Scoring
- **3.1/3.2 Graph Tracker** (`graph_tracker.py`): Records every tool call in a directed execution graph. Detects cyclic tool calls and depth violations. Returns `ALLOWED` or `BLOCKED`.
- **3.3 Risk Scorer** (`risk_scorer.py`): Contextual risk scoring (0–100) based on amount magnitude, account flags, call depth, and temporal factors.

### Module 4 — OPA Policy Engine
- **`opa_evaluator.py`**: Runs Open Policy Agent in embedded mode.
- **5 Rego policy files** (see Part 4).
- Capability check: validates the agent's `allowed_tools` list against the requested action before OPA evaluation.
- Live trust score injected into OPA input so policies can reference it.

### Module 5 — Cryptographic Audit Ledger
- **`audit_ledger.py`**: Hash-chained JSONL ledger. Every entry includes SHA-256 of the previous entry — tamper-evident.
- Endpoint: `GET /api/v1/audit/entries` — returns entries with chain integrity flag.
- Endpoint: `GET /api/v1/audit/verify` — verifies the entire chain.
- Every gate decision (ALLOW, DENY, HITL, BLOCKED, ERROR) is written here.
- Splunk HEC forwarder (`splunk_forwarder.py`) — streams audit events to Splunk SIEM (configurable).

### Module 6 — Kill Switch + Fleet Control
- **`kill_switch.py`**:
  - `quarantine_agent(agent_id)`: Sets `agent:state:{id} = QUARANTINED` in Redis, publishes to PubSub channel, now also calls `update_trust(KILL_SWITCH_TRIGGERED)` which drops trust by −20.
  - `quarantine_fleet()`: Atomic fleet-wide kill — iterates all registered agents.
  - `release_agent(agent_id)`: Restores state to `ACTIVE`, resets trust to **exactly 50.0** (agent must re-earn trust).
  - `get_fleet_status()`: Returns per-agent state + kill timestamps.
- Endpoints: `POST /api/v1/killswitch/isolate`, `POST /api/v1/killswitch/fleet-kill`, `POST /api/v1/killswitch/release/{id}`

### Module 6.3 — Saga Compensator
- **`saga_compensator.py`**: Every in-flight operation is registered in Redis before it starts.
- On failure/exception: the compensator reads in-flight records and can roll back.
- `compensate_fleet()`: Rolls back all in-flight operations across the entire fleet.

### Module 7.3 — Report Generation (`report_generator.py`)
- Reads the entire `audit_log.jsonl`.
- Verifies the cryptographic chain hash-by-hash before generating the report.
- Translates JSON into plain English paragraphs (e.g., "✅ REFUND ₹2000.00 PROCESSED...").
- Aggregates counters (Total spend evaluated, HITL escalations, Razorpay payouts processed).
- Supports dual output formats: JSON (`/api/v1/audit/report`) and PDF via ReportLab (`/api/v1/audit/report/pdf`).
- Now fully supports the Razorpay pivots, translating `REFUND`, `PAYOUT`, and `PAYMENT_CAPTURE` with correct ₹ (INR) symbols and specialized summaries.

### Module B — Trust Engine
- **`trust_engine.py`**: Persistent, deterministic trust score (0.0–100.0) per agent stored in Redis.
- **`main.py` -> `/api/v1/trust/{agent_id}/signal`**: The endpoint to ingest signals.
- Supports signals like `TRANSACTION_COMPLETED` (+5.0), `POLICY_VIOLATION` (-10.0), `BEHAVIOR_ANOMALY_SEVERE` (-8.0), `KILL_SWITCH_TRIGGERED` (-20.0), and `HIGH_RISK_ESCALATED` (-2.0).
- Full history kept (up to 500 events per agent) for chart rendering.
- `update_trust()`, `set_trust()`, `get_trust_history()`, `get_trust_summary()` all exposed as REST endpoints.

### Module C — Autonomy Engine
- **`autonomy_engine.py`**: Maps trust score → autonomy tier dynamically on every action.
- Tiers: `FULL (≥90)`, `BOUNDED (70–89)`, `HITL (40–69)`, `QUARANTINE (<40)`.
- `BOUNDED` applies 80% amount limit + 50% velocity limit + HITL on risk > 50.
- Tier thresholds are configurable via Redis (admin endpoint).
- `get_fleet_tier_distribution()` used by the dashboard KPI strip.

### Module D — Behavior Monitor
- **`behavior_monitor.py`**: 7-flag behavioral deviation detector.
- **D.1 Baseline Profiler**: After 10+ actions, locks a statistical baseline (avg amount, velocity, tool mix, accounts, call depth).
- **D.2 Deviation Detector**: Scores every new action across 7 weighted flags:
  - `amount_spike` (×1.5 avg) — weight 15
  - `amount_extreme` (×3.0 avg) — weight 35
  - `velocity_surge` — weight 30
  - `tool_drift` — weight 10
  - `depth_increase` — weight 25
  - `near_limit_cluster` — weight 40
  - `new_account_target` — weight 10
- Severity levels: `NORMAL / MILD / MODERATE / SEVERE`.
- Auto-emits `BEHAVIOR_ANOMALY_MILD` or `BEHAVIOR_ANOMALY_SEVERE` trust signals.
- REST endpoints: `/behavior/{id}/check`, `/baseline`, `/deviation`, `/timeline`.

### Module 13 — Unified Action Endpoint
- `POST /api/v1/agents/{agent_id}/action` — wraps the full SDK pipeline over HTTP.
- Any caller (UI, test, demo) can fire a governed action without importing Python.
- Returns `trust_before`, `trust_after`, `trust_delta` alongside the gate result.

### Demo Sandbox
- `POST /api/v1/demo/chat` — runs the real `customer_service_agent.py` in a background thread.
- **SSE streaming** — every `print()` from the agent and SDK is captured and streamed as Server-Sent Events to the UI in real-time, classified as `allow` / `deny` / `hitl` / `duplicate` for color coding.

---

## Part 4: OPA Rego Policies (`safety-service/policies/`)

| File | Action Type | Key Rules |
|---|---|---|
| `servicing_disputes.rego` | FEE_WAIVER, CREDIT_LIMIT_INCREASE | Amount < $500; risk < 70; trust ≥ 60 |
| `trading_limits.rego` | WIRE_TRANSFER, TRADE | Trade value limits; risk < 80 |
| `razorpay_refund.rego` | REFUND | Amount ≤ ₹10,000; payment captured; risk < 75; trust ≥ 50 |
| `razorpay_payout.rego` | PAYOUT | destination_verified = true; amount ≤ ₹1,00,000; trust ≥ 60 |
| `razorpay_payments.rego` | PAYMENT_CAPTURE | Payment must be AUTHORIZED; amount within tx limit |

---

## Part 5: Mock Banking API (`mock-banking-api/main.py`)

A fully functional Razorpay-style banking backend, 748 lines.

**Razorpay Merchant Data (4 merchants):**
- `merch_zoopCart` — E-commerce (₹2,50,000 balance, ₹10,000/tx limit)
- `merch_foodieApp` — Food Delivery (₹75,000 balance, ₹3,000/tx limit)
- `merch_saasHub` — B2B SaaS (₹18,00,000 balance, ₹50,000/tx limit)
- `merch_quickPay` — Payment Aggregator (₹50,00,000 balance, ₹1,00,000/tx limit)

**Implemented Endpoints:**

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/merchants` | List all merchants |
| GET | `/api/v1/merchants/{id}/balance` | Real-time balance |
| GET | `/api/v1/merchants/{id}/payments` | Payment list (filterable) |
| GET | `/api/v1/merchants/{id}/transactions` | Full transaction view |
| GET | `/api/v1/payments/{id}` | Payment details |
| GET | `/api/v1/orders/{id}` | Order lookup |
| GET | `/api/v1/refunds/{id}` | Refund status |
| POST | `/api/v1/payments/{id}/refund` | Process refund |
| POST | `/api/v1/payments/{id}/capture` | Capture AUTHORIZED payment |
| POST | `/api/v1/payouts` | Merchant settlement payout |
| POST | `/api/v1/cards/fee-waiver` | Legacy fee waiver |
| POST | `/api/v1/ledger/transfers/wire` | Legacy wire transfer |
| POST | `/api/v1/credit/limit-increase` | Legacy credit limit change |
| POST | `/api/v1/ledger/reserve` | 2PC Phase 1 – Reserve |
| POST | `/api/v1/ledger/commit` | 2PC Phase 2 – Commit/Rollback |
| GET | `/api/v1/ledger/reserves` | Active reservations |
| GET | `/api/v1/accounts/{id}` | Account details |

---

## Part 6: Two-Phase Commit (`safety-service/two_phase_commit.py`)

Prevents TOCTOU (Time-of-Check-Time-of-Use) race conditions in wire transfers.

Flow:
1. **Phase 1 (Reserve)**: `POST /api/v1/ledger/reserve` — locks funds atomically.
2. **Phase 2 (Commit)**: `POST /api/v1/ledger/commit` with `action: "COMMIT"` — deducts from real balance.
3. **Rollback**: If commit fails, `action: "ROLLBACK"` releases the reservation.

Result statuses: `2PC_COMMITTED`, `2PC_ABORTED`, `2PC_ROLLBACK`.

---

## Part 7: Frontend Dashboard (`frontend/src/routes/`)

A full React operator dashboard with 10+ pages, all connected to live APIs.

| Route | File | What it shows |
|---|---|---|
| `/` (Overview) | `index.tsx` | KPI strip, live feed, execution graph, OPA activity, fleet snapshot |
| `/agents` | `agents.tsx` | Registry table with status, tier, trust badge, and action sandbox |
| `/agents/:id` | `agents_.$id.tsx` | Per-agent: trust timeline chart, behavior deviation, audit history, HITL controls |
| `/audit` | `audit.tsx` | Full cryptographic audit ledger, chain integrity badge |
| `/hitl` | `hitl.tsx` | Human-In-The-Loop queue — pending actions with approve/reject |
| `/fleet` | `fleet.tsx` | Fleet kill-switch control panel with individual + fleet quarantine |
| `/policy` | `policy.tsx` | Live Rego policy viewer + action simulator (fire governed actions from UI) |
| `/traffic` | `traffic.tsx` | Audit log as traffic table, filterable by action type and decision |
| `/report` | `report.tsx` | PDF/JSON report generation |
| `/demo` | `demo.tsx` | Demo sandbox chat with live SSE telemetry stream |
| `/portal` | `portal.tsx` | Public Razorpay merchant portal |
| `/settings` | `settings.tsx` | Trust weight editor, autonomy tier config, Splunk settings |
| `/login` | `login.tsx` | Auth with role-based routing (admin / demo) |

**Key frontend components implemented:**
- `live-feed.tsx` — Real-time audit entries with `TrustDeltaBadge` (shows ▲/▼ per action)
- `autonomy-badge.tsx` — Color-coded tier pill + trust score display
- `execution-graph.tsx` — Visual agent call graph
- `opa-activity.tsx` — OPA decision stream
- `risk-scatter.tsx` — Risk score scatter plot
- `fleet-snapshot.tsx` — Fleet health overview
- `kpi-strip.tsx` — Live KPIs (fleet health, quarantined count, pending HITL)

---

## Part 8: Agent Registry (`safety-service/agent_registry.py`)

- Redis-backed registry of all agents.
- Fields per agent: `agent_id`, `name`, `agent_type`, `owner`, `allowed_tools`, `financial_limit_per_tx`, `autonomy_tier`, `status`, `registered_at`.
- Capability enforcement: `/policy/evaluate` checks `allowed_tools` before OPA runs.
- Lifecycle management: `ACTIVE → SUSPENDED → RETIRED`.

---

## Part 9: Infrastructure

- **Docker Compose** (`docker-compose.yml`): Redis container.
- **`.env` files**: Groq API key, service URLs, Redis config.
- **`idempotency.py`** (agents-fleet): Client-side idempotency key generation and Redis cache management.
- **`llm_config.py`**: Centralized LLM configuration — Groq model selection, tool binding helper.
- **`report_generator.py`**: Generates PDF and JSON compliance reports from audit ledger data.
- **`telemetry.py`**: Prometheus-compatible metrics export endpoint.
- **`splunk_forwarder.py`**: Configurable Splunk HEC forwarding for audit events.
