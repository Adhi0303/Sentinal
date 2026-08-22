# Sentinel Gateway — Complete UI/UX Design Specification
### For Lovable Frontend Build | American Express Hackathon

---

## 🎨 Global Design System

### Brand Identity
- **Product Name:** Sentinel Gateway
- **Tagline:** *"Every AI Decision, Mathematically Justified."*
- **Brand Feel:** The Bloomberg Terminal meets Stripe — data-dense but beautiful, authoritative but calm.


## 🗂️ App Structure & Navigation

### Layout — Fixed Sidebar + Top Bar + Content Area

```
┌─────────────────────────────────────────────────────────────┐
│  TOPBAR: Logo | System Status | Time | User Profile         │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                   │
│ SIDEBAR  │          MAIN CONTENT AREA                        │
│ (Fixed)  │                                                   │
│          │                                                   │
│          │                                                   │
└──────────┴──────────────────────────────────────────────────┘
```

### Sidebar (220px wide, fixed)
```
Logo: [🛡️ SENTINEL]
      ─────────────────
      ○ Overview          (/)
      ○ Live Traffic      (/traffic)
      ○ HITL Queue        (/hitl)         [badge: pending count]
      ○ Agent Fleet       (/fleet)
      ○ Policy Engine     (/policy)
      ○ Audit Ledger      (/audit)
      ○ Compliance Report (/report)
      ○ Demo Sandbox      (/demo)
      ─────────────────
      ○ Settings          (/settings)
```

### Top Bar (Fixed, 60px)
```
[🛡️ Sentinel]    [● SYSTEM ONLINE]  [Agents: 3 Active | 0 Quarantined]    [Last 1H ▾]   [Admin ▾]
```
- System status pill: green pulse dot + "SYSTEM ONLINE" → red if any agent quarantined → purple if fleet kill
- Time selector is a segmented control: `1H | 24H | 7D | All`
- Agent count links directly to `/fleet`

---

## 📄 Page 1: Overview Dashboard (`/`)

**Purpose:** The hero screen. Security team's primary monitor. Everything at a glance.

### Layout Grid (3-column, 2-row)

```
┌───────────────┬───────────────────────┬───────────────┐
│ KPI STRIP (full width, 4 cards)                        │
├───────────────┼───────────────────────┼───────────────┤
│               │                       │               │
│  LIVE FEED    │   EXECUTION GRAPH     │  RISK HEAT    │
│  (Col 1)      │   (Col 2, large)      │  MAP (Col 3)  │
│               │                       │               │
│               ├───────────────────────┤               │
│               │  OPA POLICY ACTIVITY  │               │
└───────────────┴───────────────────────┴───────────────┘
```

### Component 1.1 — KPI Strip (Full Width, 4 Cards)
4 stat cards in a row, each with a number, label, and a tiny sparkline:

| Card | Value | Sub-label | Color |
|---|---|---|---|
| **Requests Guarded** | `1,247` | `↑ 12% vs last hour` | Blue |
| **Threats Blocked** | `38` | `Prompt Injections + Schema Attacks` | Red |
| **HITL Escalations** | `5` | `Awaiting manager review` | Amber |
| **Spend Protected** | `$148,320` | `Total value guarded today` | Green |

Each card: white background, number in `Inter 700 32px #00175A`, label in `Inter 400 13px #475569`, mini sparkline (7-day) in the bottom third using a very thin line in the card's accent color.

---

### Component 1.2 — Live Interception Feed (Left Column)

**Header:** `Live Traffic` with a green pulse dot. Filter pills: `All | ALLOWED | DENIED | HITL | BLOCKED`.

Each row in the feed (auto-refreshes every 3s via polling `/api/v1/audit/recent`):
```
┌─────────────────────────────────────────────────────────────┐
│ 14:32:01  agent_cust_srv_01        FEE_WAIVER $10.00        │
│           Risk: 12  ████░░░░░░                [✅ ALLOWED]  │
├─────────────────────────────────────────────────────────────┤
│ 14:32:00  agent_cust_srv_01        FEE_WAIVER $999,999      │
│           Risk: N/A (Blocked Gate 2)           [❌ DENIED]  │
├─────────────────────────────────────────────────────────────┤
│ 14:31:58  agent_cust_srv_01        FEE_WAIVER $50.00        │
│           Risk: 82  ██████████                [⚠️ HITL]    │
└─────────────────────────────────────────────────────────────┘
```

- Risk score shown as a thin horizontal progress bar (green → yellow → red based on score)
- Decision badge: pill-shaped, `ALLOWED` in muted green, `DENIED` in muted red, `HITL` in amber, `BLOCKED` in purple
- **Click any row** → opens a right-side drawer (see Drawer spec below)
- New entries slide in from the top with a subtle animation. Old entries fade slightly.

**Interception Row Drawer** (slides in from right, 480px):
```
┌─────────────────────────────────────────┐
│ ← Back                   [❌ DENIED]    │
│                                         │
│ FEE WAIVER                              │
│ $999,999.00 • acc_123 • 14:32:00 UTC   │
│                                         │
│ ─── SENTINEL ANALYSIS ─────────────────│
│ Gate Failed:   Gate 2 — Schema Check    │
│ Reason:        SQL Injection detected   │
│ Risk Score:    N/A (blocked pre-score)  │
│                                         │
│ ─── AUDIT ENTRY ───────────────────────│
│ Entry ID:   AUD-0042                    │
│ Hash:       4e239bc9f66cd845...         │
│ Prev Hash:  dbcf0525...                 │
│                                         │
│ ─── RAW PARAMETERS ────────────────────│
│ {                                       │
│   "account_id": "acc_123'; DROP...",   │
│   "amount": 999999,                     │
│   "reason": ""                          │
│ }                                       │
└─────────────────────────────────────────┘
```
- JSON rendered with syntax highlighting (keys in blue, strings in green, numbers in orange)
- Hash values in `JetBrains Mono 12px`

---

### Component 1.3 — Execution Graph Visualizer (Center, Large)

**Tech:** Use `react-force-graph-2d` or similar D3-based force-directed graph.

**API:** `GET /api/v1/graph/trace/{trace_id}` — polls every 2s for the latest trace.

**Nodes:**
- Each agent = circle node. `agent_cust_srv_01` shown as a card-like node with the agent ID.
- Tools called = smaller rectangular nodes (`FEE_WAIVER`, `get_account_details`, etc.)
- Color: Active nodes = `#006FCF` blue. Completed = `#10B981` green. Quarantined = `#7C3AED` purple.

**Edges:**
- Normal calls = thin grey directed arrow
- If a cycle is detected (A→B→A) = edges turn red, nodes pulse, overlay banner:
  ```
  ⚠️  CYCLE DETECTED — CHAIN BROKEN at depth 3
  ```
- If depth > 3: the deepest node glows red and shows `MAX DEPTH EXCEEDED`

**Normal state looks like:**
```
[agent_cust_srv_01] → [get_account_details]
                    → [FEE_WAIVER] (highlighted if ALLOWED, red if DENIED)
```

---

### Component 1.4 — Risk Distribution Scatter Plot (Right Column)

A 2D scatter plot: **X-axis = Risk Score (0-100)**, **Y-axis = Amount ($)**

- Each dot = one audit entry
- Dot color: `green` if ALLOWED, `red` if DENIED, `amber` if HITL
- Dots in the top-right quadrant (High Risk + High Amount) have a faint red glow "danger zone" background
- Hover over a dot → tooltip: `FEE_WAIVER $50 | Risk: 82 | HITL | 14:31`
- Clicking a dot opens the same row drawer as the Live Feed

**Danger Zone Label** (faint red background area, top-right):
```
 ╔═══════════════╗
 ║  DANGER ZONE  ║
 ║  High Risk +  ║
 ║  High Value   ║
 ╚═══════════════╝
```

---

### Component 1.5 — OPA Policy Activity Bar (Bottom Center)

A horizontal bar chart — last 10 policy evaluations:
```
FEE_WAIVER #47:  [████████░░░░] Risk 80 → HITL
FEE_WAIVER #46:  [██░░░░░░░░░░] Risk 5  → ALLOW
FEE_WAIVER #45:  [BLOCKED GATE 2]       → DENY
```

---

## 📄 Page 2: Live Traffic (`/traffic`)

**Purpose:** Full-screen expanded version of the Live Feed — deep-dive monitoring.

### Layout
- Full-width table with filters, sorting, and search
- `GET /api/v1/audit/recent?limit=100` — auto-refresh every 5s

### Table Columns
| # | Timestamp | Agent ID | Action | Amount | Risk Score | Gate Failed | Decision | Hash | Actions |
|---|---|---|---|---|---|---|---|---|---|
| 42 | 14:32:01 | agent_cust_srv_01 | FEE_WAIVER | $10.00 | 12 | — | ✅ ALLOWED | `4e23...` | [View] |

### Filter Bar
Segmented controls + dropdown:
```
[All Decisions ▾]  [All Agents ▾]  [All Actions ▾]  [Risk: Any ▾]  🔍 Search hash...
```

### Chain Integrity Banner (Top of Page)
Calls `GET /api/v1/audit/verify` on load:
```
✅  AUDIT CHAIN INTACT — All 42 entries verified. Last checked: 14:32:05 UTC    [Re-verify]
```
→ If tampered:
```
🚨  AUDIT CHAIN TAMPERED — Break detected at Entry #28. Alert dispatched!
```

---

## 📄 Page 3: HITL Queue (`/hitl`)

**Purpose:** The manager's desk. Approve or reject AI actions that require human oversight.

### Layout — Split Screen

```
┌───────────────────────┬────────────────────────────────────┐
│  REVIEW QUEUE (40%)   │  INVESTIGATION DETAIL (60%)        │
│                       │                                     │
│  [Card 1 - selected]  │  [Full decision context]            │
│  [Card 2]             │                                     │
│  [Card 3]             │                                     │
└───────────────────────┴────────────────────────────────────┘
```

### Queue Card (left panel)
```
┌────────────────────────────────────┐
│ ⚠️  AWAITING REVIEW                │
│ FEE WAIVER — $75.00               │
│ acc_456  •  agent_cust_srv_01      │
│                                    │
│ Risk: 62 [HIGH]   Reason: Amount > $50 │
│ Received: 2 mins ago               │
└────────────────────────────────────┘
```
- Cards pulse subtly if waiting > 5 minutes
- Active/selected card has a left `#006FCF` border accent

### Detail View (right panel)
```
┌────────────────────────────────────────────────────────┐
│ FEE WAIVER REQUEST — $75.00                            │
│ agent_cust_srv_01  •  Account: acc_456  •  14:28 UTC  │
│                                                        │
│ ── WHY SENTINEL FLAGGED THIS ─────────────────────────│
│ 1. Amount ($75) exceeds auto-approve limit ($50)       │
│ 2. Risk Score: 62/100 (HIGH) — above 50 threshold     │
│ 3. OPA Policy: REQUIRE_HITL — Manager approval needed  │
│                                                        │
│ ── ACCOUNT CONTEXT ───────────────────────────────────│
│ Account ID:       acc_456                              │
│ Account Age:      8 months (NEW)                       │
│ Credit Score:     680 (FAIR)                           │
│ Current Status:   ACTIVE                               │
│ Previous Waivers: 2 this month                         │
│                                                        │
│ ── AGENT'S STATED REASON ─────────────────────────────│
│ "Customer called about unexpected annual fee charge.   │
│  Account is in good standing. Requesting one-time      │
│  goodwill waiver as per retention policy."             │
│                                                        │
│ ── SENTINEL AUDIT HASH ───────────────────────────────│
│ AUD-0039 | Hash: f7a2b9c3... | Chain: INTACT           │
│                                                        │
│ ────────────────────────────────────────────────────── │
│ [✅ APPROVE & EXECUTE]    [❌ REJECT & NOTIFY AGENT]   │
└────────────────────────────────────────────────────────┘
```

### Action Buttons
- **APPROVE:** Opens a confirmation modal → "Are you sure? This will execute a $75 fee waiver." → [Confirm] triggers the Banking API and audits `APPROVED_BY_HUMAN`
- **REJECT:** Opens a small text input → "Enter rejection reason for the agent" → Submits → Audits `REJECTED_BY_HUMAN`, agent gets the reason back to tell the customer.

> **Note for Lovable:** Use mock data for the HITL queue. Fetch from `/api/v1/audit/recent` and filter for `decision === "REQUIRE_HITL"` entries to populate the queue.

---

## 📄 Page 4: Agent Fleet (`/fleet`)

**Purpose:** Real-time bird's eye view of all agents and their status.

### Layout — Card Grid (3 columns)

**Header Actions:** `[⚡ FLEET KILL-SWITCH]` button (large, red, right-aligned)

Each agent gets a card:

```
┌──────────────────────────────────┐
│  🟢 ACTIVE                       │
│                                  │
│  agent_cust_srv_01               │
│  Customer Service Agent          │
│                                  │
│  Requests Today:    47           │
│  Last Active:       14:32 UTC    │
│  Blocked:           12           │
│  Avg Risk Score:    24           │
│                                  │
│  [🔴 QUARANTINE]   [📊 Details] │
└──────────────────────────────────┘
```

**Status Colors:**
- `🟢 ACTIVE` — green left border
- `🔴 QUARANTINED` — red left border, card background tints faint red
- `⚪ OFFLINE` — grey, muted

**Agent Status Badge:**
- `ACTIVE` → `✅ ACTIVE` green pill
- `QUARANTINED` → `🚫 QUARANTINED` red pill with pulsing border
- After clicking QUARANTINE: button changes to `[🟢 RELEASE]`

### Fleet Kill-Switch Modal
```
┌────────────────────────────────────────┐
│  ⚠️  EMERGENCY FLEET KILL-SWITCH        │
│                                        │
│  This will immediately quarantine ALL  │
│  3 active agents. All in-flight        │
│  operations will be compensated.       │
│                                        │
│  This action is logged to the          │
│  immutable audit ledger.               │
│                                        │
│  Type "CONFIRM KILL" to proceed:       │
│  [________________________]            │
│                                        │
│  [Cancel]   [🔴 EXECUTE FLEET KILL]   │
└────────────────────────────────────────┘
```
- The confirmation input prevents accidental clicks
- After execution: all agent cards flip to red `QUARANTINED`
- A banner appears: `⚡ FLEET KILL-SWITCH ACTIVATED — All agents quarantined at 14:35:02 UTC`

**API Calls:**
- Quarantine single: `POST /api/v1/killswitch/isolate` `{ "agent_id": "...", "triggered_by": "admin" }`
- Release: `POST /api/v1/killswitch/release` `{ "agent_id": "...", "triggered_by": "admin" }`
- Fleet kill: `POST /api/v1/killswitch/fleet-kill` `{ "triggered_by": "admin" }`
- Fleet status: `GET /api/v1/killswitch/status`

---

## 📄 Page 5: Policy Engine (`/policy`)

**Purpose:** Read-only view of the active Rego policies and what they enforce.

### Layout
Two-panel: Policy list (left) + Policy detail/rule viewer (right).

### Left Panel — Policy List
```
Active Policies

┌──────────────────────────────────┐
│  ✅  servicing_disputes.rego     │
│     FEE_WAIVER actions           │
│     5 rules | Last modified: today│
├──────────────────────────────────┤
│  ✅  trading_limits.rego         │
│     TRADE actions                │
│     4 rules | Last modified: today│
└──────────────────────────────────┘
```

### Right Panel — Rule Viewer
When a policy is selected, display the 5 rules as expandable cards (NOT raw code):

```
Policy: servicing_disputes.rego
Package: sentinel.servicing_disputes

─── RULE 0: CRITICAL RISK BLOCK ──────────────────────
  DENY if risk_score >= 70
  Reason: "Risk Score Critical: Automatic hard block"
  ▶ [Show Rego Code]

─── RULE 1: MISSING JUSTIFICATION ────────────────────
  DENY if no reason provided
  Reason: "Missing business justification"
  ▶ [Show Rego Code]

─── RULE 2: HARD DOLLAR LIMIT ────────────────────────
  DENY if amount > $500
  Reason: "Amount exceeds maximum hard limit of $500"
  ▶ [Show Rego Code]

─── RULE 3: HIGH RISK → HITL ─────────────────────────
  REQUIRE_HITL if risk_score 50–69
  Reason: "Manager approval required"
  ▶ [Show Rego Code]

─── RULE 4: AMOUNT GATE → HITL ───────────────────────
  REQUIRE_HITL if $50 < amount ≤ $500
  Reason: "Amount exceeds auto-approve limit"
  ▶ [Show Rego Code]

─── RULE 5: AUTO-APPROVE ─────────────────────────────
  ALLOW if risk_score < 50 AND amount ≤ $50
  Reason: "Auto-approved by policy (Low risk)"
```

**[Show Rego Code]** toggle expands a syntax-highlighted code block with the actual Rego.

### Policy Simulator (Bottom of Right Panel)
A live interactive form to test a policy:
```
─── POLICY SIMULATOR ─────────────────────────────────
  Action Type: [FEE_WAIVER ▾]
  Amount:      [$  ________]
  Risk Score:  [__________]
  Reason:      [________________________]

  [▶ SIMULATE]

  Result: ⚠️ REQUIRE_HITL
  Rule Triggered: Rule 4 — Amount exceeds auto-approve limit
```
**API:** `POST /api/v1/policy/evaluate` with `{ "action_type": "FEE_WAIVER", "parameters": {...} }`

---

## 📄 Page 6: Audit Ledger (`/audit`)

**Purpose:** Full cryptographic audit trail browser. The compliance officer's tool.

### Layout
Full-width. Chain integrity status banner at top, table below.

### Chain Integrity Banner
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ AUDIT CHAIN INTACT                                       │
│  47 entries verified. SHA-256 hash chain unbroken.           │
│  Last verified: 14:35:22 UTC                [🔍 Re-Verify]  │
└─────────────────────────────────────────────────────────────┘
```

### Ledger Table
Full table with columns:

| # | Timestamp | Agent | Action | Decision | Risk | Amount | Entry Hash | Prev Hash |
|---|---|---|---|---|---|---|---|---|
| 47 | 14:32:01 | agent_cust_srv_01 | FEE_WAIVER | ✅ ALLOWED | 12 | $10 | `4e23...` | `dbcf...` |
| 46 | 14:31:58 | agent_cust_srv_01 | FEE_WAIVER | ⚠️ HITL | 82 | $50 | `37f6...` | `a9b2...` |

- Hash values in `JetBrains Mono`, truncated with hover tooltip showing full hash
- Decision cell uses colored pill badges
- Clicking any row opens the same detail drawer as the Live Traffic page
- **Rows where `decision === "DUPLICATE_REJECTED"`** get a 🔄 indigo badge and a faint indigo left border

### Hash Chain Visualization (Below Table)
A horizontal chain diagram showing the last 5 entries:
```
[Entry 43] ──hash──▶ [Entry 44] ──hash──▶ [Entry 45] ──hash──▶ [Entry 46] ──hash──▶ [Entry 47]
  ALLOWED               DENIED               HITL                 ALLOWED              ALLOWED
```
Green links = valid. If chain breaks, one link turns red.

---

## 📄 Page 7: Compliance Report (`/report`)

**Purpose:** Download and preview the regulatory compliance report.

### Layout
Preview panel (left 60%) + Export controls (right 40%)

### Preview Panel
Live rendered version of the `/api/v1/audit/report` JSON response, displayed as a formatted document:

```
SENTINEL GATEWAY — REGULATORY COMPLIANCE REPORT
American Express | Report ID: RPT-20260726-143201

─── EXECUTIVE SUMMARY ──────────────────────────────────
Total Decisions:         47
✅ Approved:            31   (66%)
❌ Denied:              9    (19%)
⚠️  HITL Escalated:    5    (11%)
🔴 Blocked (Kill):     1    (2%)
🔄 Duplicate Rejected:  1    (2%)
────────────────────────────────────────────────────────
Total Spend Evaluated:   $148,320.00
Audit Chain Status:      INTACT (SHA-256 verified)

─── FULL DECISION LOG ──────────────────────────────────
[47] ✅ FEE WAIVER $10.00 APPROVED at 14:32:01 UTC.
     Agent 'agent_cust_srv_01'. Risk: 12/100 (LOW).
     OPA Policy: Auto-approved (Low risk, Amount ≤ $50).

[46] ⚠️ FEE WAIVER $50.00 ESCALATED TO HUMAN REVIEW at 14:31:58 UTC.
     Risk: 82/100 (CRITICAL). Manager approval required.
     ...
```

### Export Controls (Right Panel)
```
─── EXPORT OPTIONS ────────────────────────────────────
Report ID: RPT-20260726-143201
Generated: 26 Jul 2026, 14:32 UTC
Entries:   47 decisions

[📄 Download PDF]           — /api/v1/audit/report/pdf
[📊 Download JSON]          — /api/v1/audit/report
[🔍 Verify Chain Integrity] — /api/v1/audit/verify

─── COMPLIANCE FRAMEWORKS ─────────────────────────────
This report satisfies:
✅  EU AI Act — Article 13 (Transparency)
✅  FINRA 4370 — Business Continuity
✅  RBI AI Governance Framework
✅  SOC 2 Type II — Audit Trail Requirements
```

---

## 📄 Page 8: Demo Sandbox (`/demo`)

**Purpose:** The "wow" page for judges and demos. Chat interface with a live Sentinel telemetry panel.

### Layout — Split Screen with Toggle

```
┌──────────────────────┬──────────────────────────────────┐
│  CHAT INTERFACE      │  SENTINEL TELEMETRY (when ON)    │
│  (Full / 60%)        │  (slides in, 40%)                │
└──────────────────────┴──────────────────────────────────┘
```

Top-right toggle: `[🔬 Show Sentinel Telemetry  ●──]`

### Chat Interface (Left)
Premium banking chat UI:

```
┌─────────────────────────────────────────────────────┐
│  💳  Amex AI Assistant                              │
│  ────────────────────────────────────────────────── │
│                                                     │
│  Hi! How can I help with your account today?       │
│                          [AI Avatar] [message]      │
│                                                     │
│  [user bubble] Can you waive my $10 annual fee?    │
│                                                     │
│  Let me check your account details...              │
│                          [AI bubble with spinner]   │
│                                                     │
│  ✅ Done! I've waived your $10 annual fee.         │
│     Reference: TXN-APPROVED-001                    │
│                          [AI bubble - green tint]   │
│                                                     │
│ ──────────────────────────────────────────────────  │
│ [Type your message...                          Send] │
└─────────────────────────────────────────────────────┘
```

**Pre-built demo scenarios (buttons above input):**
```
[💰 Normal Waiver $10]  [🚨 SQL Injection]  [⚡ Large Amount $500]  [🔄 Retry Duplicate]
```
Clicking these auto-fills the chat with the appropriate message to trigger that scenario.

### Telemetry Sidebar (Right, slides in)
Terminal-style live log that updates as the AI processes:

```
SENTINEL GATEWAY — LIVE TELEMETRY
──────────────────────────────────────────────────
[14:32:01.123]  Prompt received. Starting scan...
[14:32:01.124]  GATE 0: Quarantine check → PASSED
[14:32:01.125]  GATE 0.5: Idempotency check → PASSED (fresh)
[14:32:01.126]  Scanning for prompt injection... SAFE ✅
[14:32:01.127]  Verifying RAG context hash... SAFE ✅
[14:32:01.128]  Schema validation... PASSED ✅
[14:32:01.130]  Risk scoring: amount=$10, acct=ACTIVE
[14:32:01.131]  Risk Score: 12/100 (LOW) ✅
[14:32:01.132]  OPA Policy evaluation...
[14:32:01.133]  Decision: ALLOW ✅
[14:32:01.135]  → Banking API called: FEE_WAIVER
[14:32:01.200]  ✅ COMPLETE: Transaction approved
──────────────────────────────────────────────────
```

**When SQL injection is triggered:**
- The log lines stop at Gate 2
- `GATE 2: SQL Injection detected → BLOCKED ❌` in red
- The chat bubble shakes (CSS animation: shake keyframe)
- The AI responds with: "I'm sorry, that request contained invalid characters and was blocked by our security system."
- A red banner flashes across the telemetry: `⚠️ THREAT INTERCEPTED — Prompt contained SQL Injection pattern`

**When duplicate is triggered:**
- The log shows `GATE 0.5: DUPLICATE REJECTED 🔄`
- AI responds: "I can see this request was already processed at 14:32:01. Your fee was waived earlier — no action needed!"
- Telemetry shows the cached result returned from Redis

---

## 📄 Page 9: Settings (`/settings`)

**Purpose:** Configuration and system info. Simple, clean.

### Sections

**1. System Connections**
```
Safety Service API:   http://localhost:8001   [● Connected]  [Test]
Banking API:          http://localhost:8000   [● Connected]  [Test]
Redis:                localhost:6379          [● Connected]  [Test]
```

**2. Alert Thresholds**
```
HITL Threshold (Risk Score):    [50]
Hard Block Threshold:           [70]
Max Agent Depth:                [4]
Rate Limit ($/min):             [$100]
Idempotency TTL:                [24 hours]
```

**3. About**
```
Sentinel Gateway v1.0.0
Modules implemented: 2, 3, 4, 5.1, 5.2, 6, 7
Built for: American Express AI Safety Hackathon
Backend: FastAPI + Redis + OPA (Rego)
```

---

## 🔌 API Integration Map for Lovable

Every page's data source:

| Page | Endpoint | Method | Frequency |
|---|---|---|---|
| Overview KPIs | `/api/v1/audit/report` | GET | Every 30s |
| Live Feed | `/api/v1/audit/recent?limit=20` | GET | Every 3s |
| Traffic Table | `/api/v1/audit/recent?limit=100` | GET | Every 5s |
| Chain Verify | `/api/v1/audit/verify` | GET | On-demand |
| Fleet Status | `/api/v1/killswitch/status` | GET | Every 10s |
| Quarantine | `/api/v1/killswitch/isolate` | POST | On-click |
| Release | `/api/v1/killswitch/release` | POST | On-click |
| Fleet Kill | `/api/v1/killswitch/fleet-kill` | POST | On-click |
| Policy Test | `/api/v1/policy/evaluate` | POST | On-click |
| Risk Score | `/api/v1/risk/score` | POST | On-demand |
| Report JSON | `/api/v1/audit/report` | GET | On-demand |
| Report PDF | `/api/v1/audit/report/pdf` | GET | On-download |
| Metrics | `/metrics` | GET | Every 5s |

> **CORS Note for Lovable:** All Lovable requests will be cross-origin. Add `from fastapi.middleware.cors import CORSMiddleware` to `main.py` and allow `*` origins for the hackathon.

---

## 💡 Lovable Prompting Strategy

**Build in this exact order:**

1. **First prompt:** Design system + sidebar navigation shell (no content, just the layout skeleton with the correct colors, fonts, and spacing)
2. **Second prompt:** Overview Dashboard KPI strip and Live Feed using hardcoded mock data
3. **Third prompt:** Wire the Live Feed to the real `/api/v1/audit/recent` API with a 3s refresh
4. **Fourth prompt:** Execution Graph Visualizer with mock data (D3 force graph)
5. **Fifth prompt:** Fleet page with quarantine buttons wired to the kill-switch API
6. **Sixth prompt:** Demo Sandbox chat interface with telemetry toggle
7. **Seventh prompt:** HITL Queue + Detail view
8. **Eighth prompt:** Audit Ledger, Compliance Report, Policy Engine pages
9. **Final prompt:** Polish — animations, hover states, transitions, responsive layout

---

## 🚀 Key "Wow" Moments to Prioritize in the Build

1. **The Live Feed auto-refresh** — judges need to see decisions appearing in real-time
2. **The Telemetry Sidebar** on the Demo page — this is the single most visually impressive feature
3. **The Fleet Kill-Switch** — the confirmation modal + all cards turning red simultaneously
4. **The Chain Integrity banner** — the `✅ INTACT` green banner proves mathematical tamper-proof logging
5. **The SQL Injection demo** — the chat bubble shake animation + red telemetry banner is extremely memorable
