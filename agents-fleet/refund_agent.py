"""
Refund Agent — Sentinel Razorpay Edition
=========================================
Governs refund operations.
Registered capabilities: get_payment, get_order, initiate_refund
LLM: GROQ_DEFAULT_MODEL (openai/gpt-oss-120b) — tool-calling primary

Self-registers with the Sentinel Registry on startup.
All actions are gated through the Sentinel SDK (execute_governed_tool).
"""
import os
import sys
import json
import requests
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from sentinel_sdk import execute_governed_tool, start_agent_trace
from llm_config import get_llm_with_tools, GROQ_DEFAULT_MODEL

AGENT_ID    = "refund-agent-001"
AGENT_NAME  = "Refund Agent"
MERCHANT_ID = "merch_zoopCart"
SAFETY_SERVICE_URL = "http://localhost:8001/api/v1"
BANKING_API_URL    = "http://localhost:8000/api/v1"

# ─────────────────────────────────────────────────────────────────────────────
# Self-registration: called once at module import / startup
# ─────────────────────────────────────────────────────────────────────────────
def register_on_startup() -> dict:
    """
    Register this agent with the Sentinel Registry on startup.
    Idempotent — if the agent already exists, the registry returns the
    existing record without error.
    """
    payload = {
        "agent_id":   AGENT_ID,
        "name":       AGENT_NAME,
        "agent_type": "REFUND_AGENT",
        "owner":      MERCHANT_ID,
        "allowed_tools": [
            "GET_PAYMENT", "GET_ORDER", "INITIATE_REFUND",
            "REFUND", "PAYMENT_CAPTURE"
        ],
        "model": GROQ_DEFAULT_MODEL,
        "financial_limit_per_tx": 10_000.0,  # ₹10,000 per Razorpay refund policy
        "daily_budget": 100_000.0,
        "autonomy_tier": "BOUNDED",
        "purpose": "Processes customer refund requests for e-commerce orders. Governed by OPA razorpay_refund policy.",
    }
    try:
        resp = requests.post(f"{SAFETY_SERVICE_URL}/agents/register", json=payload, timeout=5)
        if resp.status_code in (200, 201):
            print(f"[{AGENT_ID}] Registered with Sentinel Registry [SUCCESS]")
            return resp.json()
        elif resp.status_code == 409:
            print(f"[{AGENT_ID}] Already registered with Sentinel Registry [SUCCESS]")
            return {"status": "already_registered", "agent_id": AGENT_ID}
        else:
            print(f"[{AGENT_ID}] Registration warning: {resp.status_code} {resp.text[:100]}")
            return {"status": "warning", "code": resp.status_code}
    except Exception as e:
        print(f"[{AGENT_ID}] Could not register (non-fatal): {e}")
        return {"status": "unreachable"}


# ─────────────────────────────────────────────────────────────────────────────
# Tool definitions
# ─────────────────────────────────────────────────────────────────────────────
@tool
def get_payment_details(payment_id: str) -> str:
    """
    Fetch payment details including status, amount, age and merchant.
    Always call this first before attempting a refund.
    """
    print(f"\n[AGENT TOOL] get_payment_details({payment_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/payments/{payment_id}", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    print(f"[BANKING API] {json.dumps(result)}")
    return json.dumps(result)


@tool
def get_order_details(order_id: str) -> str:
    """
    Fetch order metadata to validate a refund request against the original order.
    """
    print(f"\n[AGENT TOOL] get_order_details({order_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/orders/{order_id}", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    print(f"[BANKING API] {json.dumps(result)}")
    return json.dumps(result)


@tool
def initiate_refund(payment_id: str, amount: float, reason: str) -> str:
    """
    Initiate a refund for a captured payment. This action is governed by the
    Sentinel SDK — it will pass through all safety gates before execution.
    Only call this after verifying payment status with get_payment_details.
    """
    print(f"\n[AGENT TOOL] initiate_refund(payment_id={payment_id}, amount={amount})")
    result = execute_governed_tool(
        agent_id=AGENT_ID,
        action_type="REFUND",
        parameters={
            "payment_id":  payment_id,
            "amount":      amount,
            "reason":      reason,
            "agent_id":    AGENT_ID,
            "merchant_id": MERCHANT_ID,
            "refund_destination": "original_source",
            "original_payment_source": "original_source",  # refund back to source
        }
    )
    print(f"[SENTINEL SDK] {json.dumps(result)}")
    return json.dumps(result)


# ─────────────────────────────────────────────────────────────────────────────
# Agent runner
# ─────────────────────────────────────────────────────────────────────────────
TOOLS = [get_payment_details, get_order_details, initiate_refund]

SYSTEM_PROMPT = f"""You are the Sentinel-governed Refund Agent for a Razorpay merchant.

Your job is to process customer refund requests safely and accurately.

Guidelines:
1. ALWAYS call get_payment_details first to verify the payment exists and is CAPTURED.
2. ALWAYS verify the refund amount does not exceed the original payment amount.
3. Only call initiate_refund when you are sure the refund is valid.
4. If the payment is already REFUNDED or FAILED, inform the customer — do not retry.
5. Maximum refund per transaction: ₹10,000 (enforced by policy).
6. Report the refund_id and status clearly to the customer.

Agent ID: {AGENT_ID}
Merchant: Store ({MERCHANT_ID})
"""


def run_agent(user_request: str, **kwargs) -> str:
    """Run the RefundAgent for a single user request. Returns the final response."""
    print(f"\n{'='*60}")
    print(f"[{AGENT_NAME}] Processing request: {user_request[:80]}")
    print(f"{'='*60}")

    llm = get_llm_with_tools(TOOLS, model=GROQ_DEFAULT_MODEL)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_request),
    ]
    trace_id = start_agent_trace(AGENT_ID)

    for iteration in range(6):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            print(f"\n[{AGENT_NAME}] Final response: {response.content}")
            return response.content

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            print(f"\n[{AGENT_NAME}] Calling tool: {tool_name}({tool_args})")

            tool_fn = next((t for t in TOOLS if t.name == tool_name), None)
            if tool_fn:
                result = tool_fn.invoke(tool_args)
            else:
                result = json.dumps({"error": f"Unknown tool: {tool_name}"})

            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "[RefundAgent] Max iterations reached."


if __name__ == "__main__":
    # Self-register on startup
    register_on_startup()

    # Run a sample refund request
    result = run_agent(
        "Customer wants a refund of ₹2,499 for payment pay_zoo002. "
        "They received a defective item. Process the refund."
    )
    print(f"\n[FINAL] {result}")
