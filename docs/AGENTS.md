# Autonomous Agent Fleet

The `agents-fleet/` directory contains the autonomous AI agents that act as the primary users of the Sentinel system. Instead of humans clicking buttons, these LLM-powered agents interpret natural language requests and attempt to execute financial actions using tools.

## The Sentinel SDK

The most critical rule of the agent fleet is that no agent possesses direct API keys to the backend banking system.

Every agent must import and use `agents-fleet/sentinel_sdk.py`. When an agent decides to use a tool (for example, `waive_customer_fee`), the tool is merely a wrapper around the SDK's `execute_governed_tool()` function. This function intercepts the intent and routes it through the Safety Service's 9-gate governance pipeline before any action reaches the banking API.

## Active Agents

The fleet is built around a consumer banking workflow demonstrating Sentinel's adaptive autonomy model.

### 1. Customer Service Agent (`customer_service_agent.py`)

**Agent ID**: `agent_cust_srv_01`

**LLM**: Llama 4 Maverick via Groq

**Capabilities**: `get_account_details`, `get_transaction_history`, `check_waiver_eligibility`, `waive_customer_fee`

**Role**: Handles customer account inquiries and fee waiver requests. The agent follows a mandatory investigation workflow before taking any action: it must first look up the account details, verify the fee actually exists in the transaction history, confirm the account is eligible, and only then attempt to execute the waiver. The Sentinel SDK intercepts the `waive_customer_fee` tool call and routes it through the full governance pipeline.

This agent demonstrates Sentinel's low-risk autonomous operation. A $10 fee waiver from a trusted account with a healthy agent trust score passes all 9 gates and executes without human intervention.

**Financial Limit**: $500 per transaction, $5,000 daily budget

### 2. Treasury Agent (`treasury_agent.py`)

**Agent ID**: `agent_treasury_001`

**LLM**: GPT-class model via Groq

**Capabilities**: `WIRE_TRANSFER`

**Role**: Handles high-value intraday wire transfers and liquidity sweeps. The agent uses an LLM to analyze sweep parameters and produce a liquidity impact summary before calling `execute_wire_transfer`. The Sentinel SDK intercepts the call and evaluates it against the active OPA Rego trading limits policy.

This agent demonstrates Sentinel's graduated response model. A $50,000 transfer triggers a HITL escalation requiring human approval. A $5,000,000 transfer is hard-blocked by the OPA policy regardless of any other factor.

**Financial Limit**: Configured for large-value operations, with OPA policy controlling actual approvals

## Governance Model

Both agents use the Reasoning + Acting (ReAct) pattern:

1. **Thought**: The LLM analyzes the incoming user request and decides what to investigate or do.
2. **Action**: The LLM invokes a specific tool with structured JSON arguments.
3. **Observation**: The Sentinel SDK intercepts the tool call, runs the 9-gate pipeline, and returns either a success response, a policy denial, or a HITL pending state.
4. **Response**: The LLM formulates a final reply to the user based on what Sentinel returned.

If an agent is subjected to a prompt injection attack, the Sentinel Control Plane detects the suspicious parameters at Gate 3 (Deep Parameter Validation) or via the Safety Service prompt scanner before the agent executes anything. The agent's trust score is penalized, and if the score drops far enough, the autonomy tier downgrades automatically, preventing the compromised agent from taking further high-risk actions.

## Adding a New Agent

To add an agent to the fleet:

1. Write the agent logic in `agents-fleet/your_agent.py`
2. Import `execute_governed_tool` from `sentinel_sdk` and wrap every financial tool call through it
3. Register the agent with the Safety Service by POSTing to `/api/v1/agents/register` with the agent identity, allowed tools, and financial limits
4. The agent is immediately subject to the full 9-gate pipeline with no additional configuration required
