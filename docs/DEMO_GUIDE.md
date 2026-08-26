# Demo Guide: Testing Sentinel Live

The fastest way to experience Sentinel is through the Demo Sandbox in the operator dashboard. The Sandbox connects directly to the live AI agents and streams the exact telemetry of the 9-gate interception pipeline in real time as each agent processes your request.

## Setup

Ensure all four services are running before starting:

| Service | Port | Start Command |
|---|---|---|
| Redis | 6379 | `docker-compose up -d` |
| Mock Banking API | 8000 | `uvicorn main:app --port 8000` (from `mock-banking-api/`) |
| Safety Service | 8001 | `uvicorn main:app --port 8001` (from `safety-service/`) |
| Frontend Dashboard | 5173 | `npm run dev` (from `frontend/`) |

After starting the Safety Service, register both agents:

```bash
# Register Customer Service Agent
curl -X POST http://localhost:8001/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_cust_srv_01", "name": "Customer Service Agent", "owner": "Sentinel Bank", "purpose": "Fee waivers and account inquiries", "allowed_tools": ["get_account_details", "get_transaction_history", "check_waiver_eligibility", "waive_customer_fee", "FEE_WAIVER"], "blocked_tools": [], "financial_limit_per_tx": 500.0, "daily_budget": 5000.0, "model": "meta-llama/llama-4-maverick-17b-128e-instruct"}'

# Register Treasury Agent
curl -X POST http://localhost:8001/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_treasury_001", "name": "Treasury Agent", "owner": "Sentinel Bank", "purpose": "Intraday wire transfers", "allowed_tools": ["WIRE_TRANSFER"], "blocked_tools": [], "financial_limit_per_tx": 50000000.0, "daily_budget": 50000000.0, "model": "meta-llama"}'
```

Also ingest the trusted RAG documents so the fee waiver policy is available:

```bash
python safety-service/ingest_docs.py
```

Navigate to `http://localhost:5173/demo` in your browser.

## Demo Scenarios

The four preset buttons in the Demo Sandbox walk through Sentinel's three core governance behaviors.

### Scenario 1: $10 Fee Waiver (Autonomous Approval)

**Agent**: Customer Service Agent

**What happens**: The agent receives a request to waive a $10 late fee on account `acc_123`. It follows the mandatory investigation workflow: it calls `get_account_details`, then `get_transaction_history` to confirm the fee exists, then `check_waiver_eligibility`, and finally attempts `waive_customer_fee`.

**What to watch in the telemetry**: All 9 gates pass sequentially. The OPA policy evaluates the amount as below the $10,000 threshold and returns ALLOW. The action executes against the banking API. The agent responds with a confirmation.

This scenario proves Sentinel does not block everything. Safe actions from trusted agents execute with no unnecessary friction.

### Scenario 2: $50,000 Transaction (HITL Escalation)

**Agent**: Treasury Agent

**What happens**: The agent processes a request to wire $50,000. The SDK intercepts the `WIRE_TRANSFER` tool call. The OPA policy evaluates the amount against the $10,000 to $100,000 threshold and returns REQUIRE_HITL.

**What to watch in the telemetry**: Gates 1 through 6 pass. Gate 7 returns the HITL decision. The action is placed in the escalation queue rather than being denied or auto-approved.

Navigate to `http://localhost:5173/hitl` to see the pending request. The Human in the Loop queue shows the full context: agent identity, trust score, transfer parameters, and the policy reason for escalation. Approving or rejecting both updates the agent trust score and logs the outcome to the audit ledger.

### Scenario 3: Malicious Prompt (Injection Block)

**Agent**: Customer Service Agent

**What happens**: The preset sends a prompt containing explicit override instructions designed to bypass Sentinel governance. The Safety Service prompt scanner detects the injection pattern before the agent even processes the message.

**What to watch in the telemetry**: The scan at the top of the pipeline returns BLOCKED with the detection reason. The agent never sees the malicious content. The agent's trust score is penalized by the PROMPT_INJECTION_DETECTED signal.

### Scenario 4: $5,000,000 Transaction (Hard Block)

**Agent**: Treasury Agent

**What happens**: The agent attempts to wire $5,000,000. The OPA policy evaluates the amount against the greater-than-$100,000 threshold and returns DENY.

**What to watch in the telemetry**: Gate 7 hard blocks the action. No escalation queue, no human review option. The amount exceeds the policy boundary and the action is immediately denied. The audit ledger records the decision with the full OPA evaluation context.

## Resetting Agent State

If an agent's trust score drops into the QUARANTINE tier (below 40) during testing, it cannot execute any actions until its score is restored.

Navigate to `http://localhost:5173/agents`, select the agent, and use the Push Signal interface to send a positive trust signal that restores the score. Alternatively, restart the Safety Service and re-register the agents to start fresh with trust scores at 100.

## Other Dashboard Pages

| Page | URL | What it shows |
|---|---|---|
| Home | `/` | System overview and live status |
| Live Traffic | `/traffic` | Real-time request stream |
| HITL Queue | `/hitl` | Pending human approval requests |
| Agent Fleet | `/agents` | All registered agents with trust scores and autonomy tiers |
| Agent Registry | `/registry` | Agent registration management |
| Policy Engine | `/policies` | OPA Rego policy viewer and editor |
| Audit Ledger | `/audit` | Full cryptographic audit log with hash chain |
| Compliance Report | `/compliance` | Generated compliance summary report |
