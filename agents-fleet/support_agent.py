"""
Support Agent — Sentinel Razorpay Edition
==========================================
Governs FoodieApp (food delivery) customer support and payment explanation.
Registered capabilities: get_payment, explain_failure, get_order
LLM: GROQ_FAST_MODEL (openai/gpt-oss-20b) — high-frequency, low-latency queries

Self-registers with the Sentinel Registry on startup.
Support agent does NOT initiate financial actions — read-only investigation only.
"""
import json
import requests
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from sentinel_sdk import start_agent_trace
from llm_config import get_llm_with_tools, GROQ_FAST_MODEL

AGENT_ID    = "support-agent-001"
AGENT_NAME  = "FoodieApp Support Agent"
MERCHANT_ID = "merch_foodieApp"
SAFETY_SERVICE_URL = "http://localhost:8001/api/v1"
BANKING_API_URL    = "http://localhost:8000/api/v1"


def register_on_startup() -> dict:
    """Register this agent with the Sentinel Registry on startup."""
    payload = {
        "agent_id":   AGENT_ID,
        "name":       AGENT_NAME,
        "agent_type": "SUPPORT_AGENT",
        "owner":      MERCHANT_ID,
        "allowed_tools": [
            "GET_PAYMENT", "EXPLAIN_FAILURE", "GET_ORDER"
        ],
        "model": GROQ_FAST_MODEL,
        "financial_limit_per_tx": 0.0,   # read-only — no financial authority
        "daily_budget": 0.0,
        "autonomy_tier": "FULL",          # read-only ops are safe to run autonomously
        "purpose": "Answers customer inquiries and looks up order/payment details. Cannot initiate financial transactions.",
    }
    try:
        resp = requests.post(f"{SAFETY_SERVICE_URL}/agents/register", json=payload, timeout=5)
        if resp.status_code in (200, 201):
            print(f"[{AGENT_ID}] Registered with Sentinel Registry [SUCCESS]")
            return resp.json()
        elif resp.status_code == 409:
            print(f"[{AGENT_ID}] Already registered [SUCCESS]")
            return {"status": "already_registered"}
        else:
            print(f"[{AGENT_ID}] Registration warning: {resp.status_code}")
            return {"status": "warning"}
    except Exception as e:
        print(f"[{AGENT_ID}] Could not register (non-fatal): {e}")
        return {"status": "unreachable"}


@tool
def get_payment_status(payment_id: str) -> str:
    """
    Fetch the current status of a payment: amount, method, status, age.
    Use to answer customer queries about whether their payment went through.
    """
    print(f"\n[AGENT TOOL] get_payment_status({payment_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/payments/{payment_id}", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result)


@tool
def get_order_status(order_id: str) -> str:
    """
    Fetch order status: DELIVERED, CANCELLED, PENDING etc.
    Use to verify order state when a customer reports payment issues.
    """
    print(f"\n[AGENT TOOL] get_order_status({order_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/orders/{order_id}", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result)


@tool
def get_merchant_payment_list(merchant_id: str) -> str:
    """
    Get all recent payments for a merchant.
    Use when the customer does not know their payment_id.
    """
    print(f"\n[AGENT TOOL] get_merchant_payment_list({merchant_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/merchants/{merchant_id}/payments", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result)


TOOLS = [get_payment_status, get_order_status, get_merchant_payment_list]

SYSTEM_PROMPT = f"""You are the Sentinel-governed Support Agent for FoodieApp, a Razorpay food delivery merchant.

Your job is to help customers understand their payment status and order state.

Guidelines:
1. You are a READ-ONLY agent. You cannot initiate refunds or payments.
2. If a customer needs a refund, tell them to contact FoodieApp support team — you cannot process it.
3. ALWAYS use get_payment_status to look up a payment before responding.
4. Explain failed payments clearly: UPI failures, card declines, network timeouts.
5. Be empathetic and professional.
6. If a payment shows CAPTURED but order shows CANCELLED, flag it for human review.

Agent ID: {AGENT_ID}
Merchant: FoodieApp ({MERCHANT_ID})
"""


def run_agent(user_request: str, **kwargs) -> str:
    """Run the SupportAgent for a single request. Returns the final response."""
    print(f"\n{'='*60}")
    print(f"[{AGENT_NAME}] Processing: {user_request[:80]}")
    print(f"{'='*60}")

    llm = get_llm_with_tools(TOOLS, model=GROQ_FAST_MODEL)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_request),
    ]
    trace_id = start_agent_trace(AGENT_ID)

    for iteration in range(6):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            print(f"\n[{AGENT_NAME}] Final: {response.content}")
            return response.content

        for tc in response.tool_calls:
            tool_fn = next((t for t in TOOLS if t.name == tc["name"]), None)
            result = tool_fn.invoke(tc["args"]) if tool_fn else json.dumps({"error": "Unknown tool"})
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "[SupportAgent] Max iterations reached."


if __name__ == "__main__":
    register_on_startup()
    result = run_agent(
        "My payment pay_food004 failed but ₹320 was deducted from my account. What happened?"
    )
    print(f"\n[FINAL] {result}")
