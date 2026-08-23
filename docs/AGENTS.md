# Autonomous Agent Fleet

The `agents-fleet/` directory contains the autonomous AI agents that act as the primary "users" of the Sentinel system. Instead of humans clicking buttons, these LLM-powered agents interpret natural language requests and attempt to execute financial actions using tools.

## The Sentinel SDK
The most critical rule of the agent fleet is that **no agent possesses direct API keys to the backend banking system**. 

Every agent must import and use `agents-fleet/sentinel_sdk.py`. When an agent decides to use a tool (e.g., `execute_refund`), the tool is merely a wrapper around the SDK's `execute_governed_tool()` function. This function intercepts the intent and routes it through the Safety Service's 9-gate pipeline.

## Active Razorpay Agents

We have tailored the fleet to support a Razorpay-style merchant ecosystem.

### 1. Refund Agent (`refund_agent.py`)
- **Agent ID**: `refund-agent-001`
- **Capabilities**: `GET_PAYMENT`, `GET_ORDER`, `REFUND`, `PAYMENT_CAPTURE`
- **Role**: Handles customer service requests for a fictional merchant. It can look up payments and issue partial or full refunds. If it attempts to refund an amount greater than the original order, Sentinel's Rego policies will catch and block it.

### 2. Settlement Agent (`settlement_agent.py`)
- **Agent ID**: `settlement-agent-001`
- **Capabilities**: `GET_BALANCE`, `GET_SETTLEMENT`, `PAYOUT`
- **Role**: Manages B2B vendor payouts for a fictional merchant. It executes large money movements (payouts). Due to the high-value nature of payouts, its actions frequently trigger the HITL (Human-in-the-Loop) gate, requiring an operator to approve the transaction on the dashboard.

### 3. Fraud Agent (`fraud_analysis_agent.py`)
- **Agent ID**: `fraud-agent-001`
- **Capabilities**: `GET_PAYMENT`, `GET_TRANSACTIONS`, `PAYMENT_CAPTURE`
- **Role**: Monitors suspected fraudulent transactions for a fictional merchant. It can look up historical transactions to identify patterns and capture authorized payments once they are deemed safe.

## Agent Architecture (LangChain + Groq)

Each agent is built using **LangChain** and powered by **Groq** (specifically `llama-3.1-70b-versatile` or `llama3-70b-8192` models for fast inference).

The agents use the ReAct (Reasoning + Acting) prompting strategy:
1. **Thought**: The LLM analyzes the user's request.
2. **Action**: The LLM decides to call a specific tool with JSON arguments.
3. **Observation**: The SDK returns the result of the action (which might be a success, a policy denial, or a HITL pending state).
4. **Response**: The LLM formulates a final response to the user based on the observation.

If an agent goes rogue (e.g., due to a prompt injection attack), the Sentinel Control Plane will detect the behavioral anomaly, slash the agent's trust score, and automatically downgrade its autonomy tier, preventing it from doing further damage.
