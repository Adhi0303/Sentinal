# The 9-Gate Interception Pipeline

Every time an AI agent attempts to execute an action (e.g., refunding an order), the Sentinel SDK intercepts the request and forwards it to the Safety Service. The Safety Service then processes the request through a strict, sequential 9-gate pipeline.

If a request fails *any* gate, the pipeline halts immediately, the action is denied, and the agent's trust score is penalized.

## 1. Registry Check
- **Purpose**: Verifies the agent's identity and operational status.
- **Logic**: Sentinel checks the central registry. Is this agent registered? Is it currently `ACTIVE`? If an agent has been `SUSPENDED` or `RETIRED`, all its requests are instantly dropped.

## 2. Authentication
- **Purpose**: Ensures the request is coming from a trusted source.
- **Logic**: Validates the cryptographic token or API key provided by the SDK to ensure the agent hasn't been spoofed.

## 3. Schema Validation
- **Purpose**: Prevents malformed or malicious payloads from reaching the core logic.
- **Logic**: Uses strict Pydantic schemas to validate the parameters. For example, if a refund request expects an `amount` as a float, and the agent sends a SQL injection string instead, the schema validation will fail and block the request.

## 4. Idempotency Lock
- **Purpose**: Prevents duplicate transactions and accidental infinite loops (a common issue with LLM agents).
- **Logic**: Sentinel hashes the `agent_id`, `action_type`, and `parameters` to create an idempotency key. It checks Redis to see if an identical action was executed within the last 5 minutes. If it was, the action is blocked as a duplicate.

## 5. Hard Limits Check
- **Purpose**: Enforces absolute maximum financial boundaries that cannot be overridden by any policy.
- **Logic**: Checks the agent's registry profile for `max_transaction_amount` and `daily_limit`. If a Payout agent attempts to send ₹10,000,000 but its hard limit is ₹1,000,000, the action is blocked.

## 6. Trust Autonomy Check
- **Purpose**: Determines if the agent is trustworthy enough to execute the action autonomously.
- **Logic**: Sentinel fetches the agent's real-time trust score (0.0 to 100.0) and compares it against dynamic Autonomy Tiers:
  - **FULL (90-100)**: Actions proceed automatically.
  - **BOUNDED (70-89)**: Standard actions proceed, but high-risk actions are escalated.
  - **HITL (40-69)**: *All* modifying actions are paused and sent to the Human-In-The-Loop queue for manual operator approval.
  - **QUARANTINE (<40)**: All actions are denied.

## 7. OPA Rego Policies
- **Purpose**: Evaluates complex, context-aware business logic.
- **Logic**: The request payload and the agent's context are sent to the Open Policy Agent (OPA). The active Rego policies evaluate the data. For example, a policy might dictate: "A refund cannot exceed the original capture amount" or "Payouts to unverified accounts require a trust score of 95+". If OPA returns `deny = true`, the action is blocked.

## 8. Behavior Monitor
- **Purpose**: Detects anomalies and prompt injection attacks by analyzing statistical deviations over time.
- **Logic**: Sentinel calculates a rolling baseline of the agent's normal behavior (average amount, action velocity, common tools). If the current action represents a massive spike (e.g., 5x the normal refund amount, or attempting to use a tool the agent has never used before), a behavioral anomaly is flagged and the agent's trust score is slashed.

## 9. Kill Switch Check
- **Purpose**: The final emergency brake.
- **Logic**: Checks Redis for a global or agent-specific kill switch. If an operator has hit the panic button on the dashboard, the action is halted just milliseconds before it would have been sent to the banking API.

## Execution and Logging
If (and only if) the request survives all 9 gates, Sentinel forwards the payload to the Mock Banking API (Razorpay backend). 

Once the API responds, the entire decision tree, the gate results, the trust score changes, and the final outcome are cryptographically hashed and appended to the `audit_log.jsonl` ledger.
