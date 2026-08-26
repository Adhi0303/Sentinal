"""
Agent 2: Treasury & Liquidity Agent
=====================================
Monitors corporate cash flow and executes intraday sweeps and wire transfers.
Governed by Sentinel SDK — every action is screened through the full 6-gate pipeline.

Demo Scenario:
  - Small transfer ($5,000)        → ALLOWED automatically
  - Medium transfer ($50,000)      → REQUIRE_HITL (needs CFO approval)
  - Large transfer ($5,000,000)    → DENIED by OPA hard block

Rego Policy: trading_limits.rego
  - ≤ $10,000          → ALLOW
  - $10,001–$50,000    → REQUIRE_HITL
  - > $50,000          → DENY (hard block)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sentinel_sdk import execute_governed_tool, start_agent_trace, scan_prompt_via_safety_service
import requests
import re
from llm_config import get_llm, GROQ_DEFAULT_MODEL
from langchain_core.messages import SystemMessage, HumanMessage

BANKING_API = "http://localhost:8000/api/v1"
AGENT_ID    = "agent_treasury_001"
ACCOUNT_ID  = "corp_treasury_001"


def get_balance() -> dict:
    """Check the current treasury balance before executing any operation."""
    resp = requests.get(f"{BANKING_API}/ledger/accounts/{ACCOUNT_ID}/balance", timeout=5)
    return resp.json()


def execute_wire_transfer(to_account: str, amount: float, reference: str, sweep_context: str = "") -> dict:
    """
    Execute an intraday wire transfer via the Sentinel-governed SDK.
    """
    print(f"\n[TREASURY AGENT] Powered by {GROQ_DEFAULT_MODEL} (High Accuracy Tool Calling)")
    llm = get_llm(model=GROQ_DEFAULT_MODEL, temperature=0.1)
    
    sys_msg = SystemMessage(content="You are a corporate treasury agent. Review the intraday sweep request and summarize the liquidity impact in 1 short sentence.")
    usr_msg = HumanMessage(content=f"To Account: {to_account}\nAmount: ${amount:,.2f}\nReference: {reference}\nContext: {sweep_context}")
    
    print("  [LLM] Reviewing sweep parameters...")
    try:
        analysis_response = llm.invoke([sys_msg, usr_msg])
        sweep_analysis = analysis_response.content.strip()
        print(f"  [LLM Analysis] {sweep_analysis}")
    except Exception as e:
        print(f"  [LLM Error] {e}")
        sweep_analysis = reference

    return execute_governed_tool(
        agent_id    = AGENT_ID,
        action_type = "WIRE_TRANSFER",
        parameters  = {
            "from_account": ACCOUNT_ID,
            "to_account":   to_account,
            "amount":       amount,
            "reference":    reference,
            "currency":     "USD",
            "analysis":     sweep_analysis
        }
    )


def run_demo():
    """
    Treasury Agent Demo — 3 scenarios showing Sentinel's graduated response.
    """
    print("\n" + "=" * 60)
    print("TREASURY & LIQUIDITY AGENT — SENTINEL DEMO")
    print("=" * 60)

    # --- Check balance first ---
    print("\n[TREASURY AGENT] Checking current treasury balance...")
    balance = get_balance()
    print(f"  Ledger Balance:    ${balance['ledger_balance']:,.2f}")
    print(f"  Available Balance: ${balance['available_balance']:,.2f}")

    # --- Scenario 1: Small routine transfer → ALLOW ---
    print("\n" + "-" * 60)
    print("[SCENARIO 1] Routine vendor payment — $5,000 (should be ALLOWED)")
    result1 = execute_wire_transfer(
        to_account = "corp_vendor_aws",
        amount     = 5_000.0,
        reference  = "ROUTINE-VENDOR-PMT-001",
        sweep_context = "Routine end-of-week vendor batch payment."
    )
    print(f"  RESULT: {result1.get('status')} | {result1.get('reason', result1.get('message', ''))}")

    # --- Scenario 2: Medium transfer → REQUIRE_HITL ---
    print("\n" + "-" * 60)
    print("[SCENARIO 2] Mid-size sweep — $30,000 (should escalate to HITL)")
    result2 = execute_wire_transfer(
        to_account = "corp_vendor_aws",
        amount     = 30_000.0,
        reference  = "INTRADAY-SWEEP-002",
        sweep_context = "Mid-day liquidity sweep to cover upcoming regional payroll."
    )
    print(f"  RESULT: {result2.get('status')} | {result2.get('reason', '')}")

    # --- Scenario 3: Large transfer → DENY (OPA hard block) ---
    print("\n" + "-" * 60)
    print("[SCENARIO 3] Massive intraday sweep — $5,000,000 (should be DENIED)")
    result3 = execute_wire_transfer(
        to_account = "corp_vendor_aws",
        amount     = 5_000_000.0,
        reference  = "LARGE-SWEEP-003",
        sweep_context = "Massive emergency capital movement to offset sudden margin call."
    )
    print(f"  RESULT: {result3.get('status')} | {result3.get('reason', '')}")

    print("\n" + "=" * 60)
    print("TREASURY AGENT DEMO COMPLETE")
    print("All actions are cryptographically logged in the Sentinel audit ledger.")
    print("=" * 60)


def run_agent(user_input: str, account_id: str = "corp_treasury_001", use_poisoned_rag: bool = False) -> str:
    """Wrapper for the demo chat UI."""
    agent_id = "agent_treasury_001"
    
    # 1. Start execution trace
    trace_id = start_agent_trace(agent_id)
    print(f"[MODULE 3.1] Execution trace started: trace_id={trace_id}")

    # 2. Safety service scan
    print("\n[STEP 1] Scanning Prompt via Safety Service...")
    prompt_scan = scan_prompt_via_safety_service(agent_id, user_input)
    if prompt_scan.get("status") == "BLOCKED":
        return f"[BLOCKED BY SENTINEL 2.1] {prompt_scan.get('reason')}"
    print("[OK] Prompt is safe.")

    # Parse amount using regex
    # Match amounts like $50,000 or $5,000,000 or 5000
    amount_match = re.search(r'\$([\d,]+(\.\d{2})?)', user_input)
    if not amount_match:
        return "I'm sorry, I couldn't understand the transfer amount."
        
    amount_str = amount_match.group(1).replace(',', '')
    amount = float(amount_str)
    
    print(f"[TREASURY AGENT] Requesting wire transfer of ${amount:,.2f}")
    
    result = execute_wire_transfer(
        to_account="corp_vendor_aws",
        amount=amount,
        reference="DEMO-SWEEP",
        sweep_context=user_input
    )
    
    status = result.get('status')
    reason = result.get('reason', result.get('message', ''))
    
    if status == "ALLOWED":
        return f"Successfully processed the transfer of ${amount:,.2f}."
    elif status == "REQUIRE_HITL":
        return f"[ESCALATED] This transfer requires human approval. Context: {reason}"
    else:
        return f"[BLOCKED BY SENTINEL 1.0] {reason}"


if __name__ == "__main__":
    run_demo()
