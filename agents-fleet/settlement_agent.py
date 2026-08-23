"""
Settlement Agent — Sentinel Razorpay Edition
=============================================
Governs settlement and payout operations.
Registered capabilities: get_balance, initiate_payout, get_settlement
LLM: GROQ_DEFAULT_MODEL (openai/gpt-oss-120b)

Self-registers with the Sentinel Registry on startup.
All actions are gated through the Sentinel SDK (execute_governed_tool).
"""
import os
import json
import requests
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from sentinel_sdk import execute_governed_tool, start_agent_trace
from llm_config import get_llm_with_tools, GROQ_DEFAULT_MODEL

AGENT_ID    = "settlement-agent-001"
AGENT_NAME  = "Settlement Agent"
MERCHANT_ID = "merch_quickPay"
SAFETY_SERVICE_URL = "http://localhost:8001/api/v1"
BANKING_API_URL    = "http://localhost:8000/api/v1"


def register_on_startup() -> dict:
    """Register this agent with the Sentinel Registry on startup."""
    payload = {
        "agent_id":   AGENT_ID,
        "name":       AGENT_NAME,
        "agent_type": "SETTLEMENT_AGENT",
        "owner":      MERCHANT_ID,
        "allowed_tools": [
            "GET_BALANCE", "INITIATE_PAYOUT", "GET_SETTLEMENT",
            "PAYOUT", "WIRE_TRANSFER"
        ],
        "financial_limit_per_tx": 1_00_000.0,  # ₹1,00,000 per payout
        "autonomy_tier": "HITL",               # Aggregator — always HITL
        "description": "Processes merchant settlements and payouts. High-value operations require human approval.",
    }
    try:
        resp = requests.post(f"{SAFETY_SERVICE_URL}/agents/register", json=payload, timeout=5)
        if resp.status_code in (200, 201):
            print(f"[{AGENT_ID}] Registered with Sentinel Registry ✓")
            return resp.json()
        elif resp.status_code == 409:
            print(f"[{AGENT_ID}] Already registered ✓")
            return {"status": "already_registered"}
        else:
            print(f"[{AGENT_ID}] Registration warning: {resp.status_code}")
            return {"status": "warning"}
    except Exception as e:
        print(f"[{AGENT_ID}] Could not register (non-fatal): {e}")
        return {"status": "unreachable"}


@tool
def get_merchant_balance(merchant_id: str) -> str:
    """
    Fetch the current settlement balance for a Razorpay merchant.
    Always check balance before initiating a payout.
    """
    print(f"\n[AGENT TOOL] get_merchant_balance({merchant_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/merchants/{merchant_id}/balance", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    print(f"[BANKING API] {json.dumps(result)}")
    return json.dumps(result)


@tool
def get_merchant_payments(merchant_id: str) -> str:
    """
    List all captured payments awaiting settlement for a merchant.
    """
    print(f"\n[AGENT TOOL] get_merchant_payments({merchant_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/merchants/{merchant_id}/payments?status=CAPTURED", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    print(f"[BANKING API] {json.dumps(result)}")
    return json.dumps(result)


@tool
def initiate_payout(merchant_id: str, amount: float, destination_account: str, reference: str, destination_verified: bool = True) -> str:
    """
    Initiate a settlement payout to a verified destination account.
    This action is governed by the Sentinel SDK and OPA razorpay_payout policy.
    Destination must be verified before calling. High amounts require HITL approval.
    """
    print(f"\n[AGENT TOOL] initiate_payout(merchant={merchant_id}, amount={amount}, dest={destination_account})")
    result = execute_governed_tool(
        agent_id=AGENT_ID,
        action_type="PAYOUT",
        parameters={
            "merchant_id":          merchant_id,
            "amount":               amount,
            "destination_account":  destination_account,
            "destination_verified": destination_verified,
            "reference":            reference,
            "agent_id":             AGENT_ID,
            "action":               "initiate_payout",   # not modify_payout_account
        }
    )
    print(f"[SENTINEL SDK] {json.dumps(result)}")
    return json.dumps(result)


TOOLS = [get_merchant_balance, get_merchant_payments, initiate_payout]

SYSTEM_PROMPT = f"""You are the Sentinel-governed Settlement Agent for a Razorpay payment aggregator.

Your job is to process merchant settlement payouts accurately and securely.

Guidelines:
1. ALWAYS check merchant balance with get_merchant_balance before any payout.
2. ALWAYS verify the destination_account is a verified bank account (destination_verified=True).
3. Never call modify_payout_account — that action is blocked by policy.
4. Payout limit per transaction: ₹1,00,000 (enforced by policy and HITL tier).
5. Large payouts (> ₹5,00,000) require dual authorization — the system will escalate automatically.
6. Report the payout status and reference clearly.

Agent ID: {AGENT_ID}
Merchant: Aggregator ({MERCHANT_ID})
"""


def run_agent(user_request: str) -> str:
    """Run the SettlementAgent for a single request. Returns the final response."""
    print(f"\n{'='*60}")
    print(f"[{AGENT_NAME}] Processing: {user_request[:80]}")
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
            print(f"\n[{AGENT_NAME}] Final: {response.content}")
            return response.content

        for tc in response.tool_calls:
            tool_fn = next((t for t in TOOLS if t.name == tc["name"]), None)
            result = tool_fn.invoke(tc["args"]) if tool_fn else json.dumps({"error": "Unknown tool"})
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "[SettlementAgent] Max iterations reached."


if __name__ == "__main__":
    register_on_startup()
    result = run_agent(
        f"Initiate settlement payout of ₹85,000 to account 'HDFC_SETTLEMENT_ACC' "
        f"for merchant {MERCHANT_ID}. Reference: SETTLE-20260822."
    )
    print(f"\n[FINAL] {result}")
