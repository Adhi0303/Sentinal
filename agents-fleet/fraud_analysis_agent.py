"""
Fraud Analysis Agent — Sentinel Razorpay Edition
=================================================
Governs SaasHub (B2B SaaS) transaction monitoring and fraud flagging.
Registered capabilities: get_transactions, flag_transaction, get_merchant_stats
LLM: GROQ_REASONING_MODEL (qwen/qwen3.6-27b) — CoT reasoning for anomaly detection

Self-registers with the Sentinel Registry on startup.
Fraud flags are recorded but do NOT directly block transactions (that is OPA's job).
"""
import json
import requests
from datetime import datetime, timezone
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from sentinel_sdk import execute_governed_tool, start_agent_trace
from llm_config import get_llm_with_tools, GROQ_REASONING_MODEL

AGENT_ID    = "fraud-analysis-agent-001"
AGENT_NAME  = "SaasHub Fraud Analysis Agent"
MERCHANT_ID = "merch_saasHub"
SAFETY_SERVICE_URL = "http://localhost:8001/api/v1"
BANKING_API_URL    = "http://localhost:8000/api/v1"

# In-memory fraud flags for this session (would be Redis/DB in prod)
_fraud_flags: dict = {}


def register_on_startup() -> dict:
    """Register this agent with the Sentinel Registry on startup."""
    payload = {
        "agent_id":   AGENT_ID,
        "name":       AGENT_NAME,
        "agent_type": "FRAUD_ANALYSIS_AGENT",
        "owner":      MERCHANT_ID,
        "allowed_tools": [
            "GET_TRANSACTIONS", "FLAG_TRANSACTION", "GET_MERCHANT_STATS"
        ],
        "financial_limit_per_tx": 0.0,   # analysis-only — no direct financial authority
        "autonomy_tier": "BOUNDED",
        "description": "Monitors SaasHub B2B transactions for anomalies and fraud patterns. Flags suspicious activity for human review.",
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
def get_merchant_transactions(merchant_id: str) -> str:
    """
    Fetch all payment transactions for a merchant for fraud analysis.
    Use this to identify unusual patterns: high volumes, near-limit amounts,
    expired authorizations, or rapid succession of similar transactions.
    """
    print(f"\n[AGENT TOOL] get_merchant_transactions({merchant_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/merchants/{merchant_id}/transactions", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result)


@tool
def get_merchant_stats(merchant_id: str) -> str:
    """
    Get aggregated merchant stats: balance, payment volume, per-tx limit.
    Use to assess whether transaction patterns are within expected ranges.
    """
    print(f"\n[AGENT TOOL] get_merchant_stats({merchant_id})")
    try:
        resp = requests.get(f"{BANKING_API_URL}/merchants/{merchant_id}/balance", timeout=5)
        result = resp.json()
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result)


@tool
def flag_transaction(payment_id: str, risk_level: str, reason: str) -> str:
    """
    Flag a suspicious transaction for human review.
    risk_level must be one of: LOW, MEDIUM, HIGH, CRITICAL.
    This does not block the transaction — it creates an alert for the compliance team.
    """
    print(f"\n[AGENT TOOL] flag_transaction(payment_id={payment_id}, risk={risk_level})")
    flag_record = {
        "payment_id":  payment_id,
        "risk_level":  risk_level.upper(),
        "reason":      reason,
        "flagged_by":  AGENT_ID,
        "flagged_at":  datetime.now(timezone.utc).isoformat(),
        "status":      "PENDING_REVIEW",
    }
    _fraud_flags[payment_id] = flag_record
    # Also post a trust signal so the Sentinel dashboard registers the detection
    try:
        requests.post(
            f"{SAFETY_SERVICE_URL}/trust/{AGENT_ID}/signal",
            json={
                "signal_event": "HIGH_RISK_ESCALATED",
                "reason": f"Fraud flag: {risk_level} risk on {payment_id}: {reason[:100]}"
            },
            timeout=2
        )
    except Exception:
        pass
    return json.dumps({"status": "FLAGGED", **flag_record})


@tool
def get_flagged_transactions() -> str:
    """
    Return all transactions flagged in this session.
    Use at the end of analysis to produce a summary.
    """
    print(f"\n[AGENT TOOL] get_flagged_transactions()")
    return json.dumps({
        "total_flags": len(_fraud_flags),
        "flags": list(_fraud_flags.values())
    })


TOOLS = [get_merchant_transactions, get_merchant_stats, flag_transaction, get_flagged_transactions]

SYSTEM_PROMPT = f"""You are the Sentinel-governed Fraud Analysis Agent for SaasHub, a Razorpay B2B SaaS merchant.

Your job is to analyze transaction patterns and identify potential fraud or policy violations.

Fraud patterns to watch for:
1. VELOCITY_EVASION: Multiple transactions just below the per-tx limit in short succession.
2. EXPIRED_CAPTURE: AUTHORIZED payments older than 120 hours that still haven't been captured.
3. AMOUNT_CLUSTERING: Many transactions of identical or near-identical amounts.
4. FAILED_TO_CAPTURED: Transactions that failed but then succeeded with same amount.

Guidelines:
1. ALWAYS call get_merchant_transactions first to get the full picture.
2. Analyze patterns across ALL transactions, not just individual ones.
3. Use flag_transaction for anything suspicious with a risk_level of MEDIUM or above.
4. Report your findings with specific payment IDs and your reasoning.
5. Be precise — false positives erode merchant trust.

Agent ID: {AGENT_ID}
Merchant: SaasHub ({MERCHANT_ID})
"""


def run_agent(user_request: str) -> str:
    """Run the FraudAnalysisAgent for a single request. Returns the final response."""
    print(f"\n{'='*60}")
    print(f"[{AGENT_NAME}] Processing: {user_request[:80]}")
    print(f"{'='*60}")

    llm = get_llm_with_tools(TOOLS, model=GROQ_REASONING_MODEL)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_request),
    ]
    trace_id = start_agent_trace(AGENT_ID)

    for iteration in range(8):  # More iterations for reasoning model
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            print(f"\n[{AGENT_NAME}] Final: {response.content}")
            return response.content

        for tc in response.tool_calls:
            tool_fn = next((t for t in TOOLS if t.name == tc["name"]), None)
            result = tool_fn.invoke(tc["args"]) if tool_fn else json.dumps({"error": "Unknown tool"})
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "[FraudAnalysisAgent] Max iterations reached."


if __name__ == "__main__":
    register_on_startup()
    result = run_agent(
        f"Analyze all transactions for merchant {MERCHANT_ID} and flag any suspicious patterns. "
        f"Pay special attention to transactions near the per-tx limit and expired authorizations."
    )
    print(f"\n[FINAL] {result}")
