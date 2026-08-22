from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
from classifiers.injection_detector import detector
from rag_firewall import firewall
from opa_evaluator import evaluate_policy
from graph_tracker import start_trace, record_tool_call, get_trace_graph
from risk_scorer import compute_risk_score
from audit_ledger import append_audit_entry, get_recent_entries, verify_chain_integrity
from kill_switch import (
    quarantine_agent, quarantine_fleet, release_agent,
    get_fleet_status, get_known_fleet_agents
)
from saga_compensator import compensate_and_clear, compensate_fleet
from telemetry import get_metrics_output
from report_generator import generate_json_report, generate_pdf_report
from splunk_forwarder import load_config as splunk_load, update_config as splunk_update, test_connection as splunk_test
import os
import requests as http_requests

# ── Phase 1: Control Plane Modules (Razorpay Pivot) ──────────────────────────
from agent_registry import (
    register_agent, get_agent, list_agents,
    update_agent_status, update_agent_config, check_tool_allowed
)
from trust_engine import (
    initialize_trust, get_trust, set_trust,
    update_trust, get_trust_history, get_trust_summary,
    get_weights, update_weights
)
from autonomy_engine import (
    get_autonomy_decision, get_tiers_config, update_tiers_config,
    get_fleet_tier_distribution
)
from behavior_monitor import (
    check_deviation, get_baseline, get_latest_deviation,
    get_deviation_timeline, get_window_size
)

BANKING_API_URL = "http://localhost:8000/api/v1"

app = FastAPI(title="Sentinel Safety Service — Modules 2, 3, 4, 5, 6, 7 | 2PC Enabled")

# CORS — allow Lovable and any local frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    agent_id: str
    text: str

class RagRequest(BaseModel):
    doc_id: str
    text: str

class SafetyResponse(BaseModel):
    status: str
    reason: str

class PolicyRequest(BaseModel):
    action_type: str
    parameters: Dict[str, Any]

class PolicyResponse(BaseModel):
    decision: str
    reason: str

# --- Module 3 Models ---
class GraphCallRequest(BaseModel):
    trace_id: str
    agent_id: str
    tool_name: str
    parent_span_id: Optional[str] = None

class GraphStartRequest(BaseModel):
    agent_id: str

class RiskScoreRequest(BaseModel):
    amount: float
    account_id: str
    call_depth: Optional[int] = 1

class RiskScoreResponse(BaseModel):
    score: int
    risk_level: str
    factors: list

@app.post("/api/v1/sanitize/prompt", response_model=SafetyResponse)
async def sanitize_prompt(req: PromptRequest):
    """
    Submodule 2.1: Prompt Injection & Goal Hijacking Detector
    Scans the incoming prompt using Regex and Llama-Guard, and logs only malicious prompts to the ledger.
    """
    print(f"\n[SAFETY SERVICE] Scanning prompt for agent {req.agent_id}...")
    result = detector.scan(req.text)
    
    # Log the prompt scan to the Audit Ledger ONLY if it was blocked (malicious)
    if result["status"] == "BLOCKED":
        append_audit_entry(
            agent_id=req.agent_id,
            action_type="PROMPT_INJECTION",
            decision="DENIED",
            reason=result["reason"],
            parameters={"prompt": req.text},
            risk_score=0
        )
    
    print(f"[SAFETY SERVICE] Result: {result['status']} | Reason: {result['reason']}")
    return SafetyResponse(status=result["status"], reason=result["reason"])

@app.post("/api/v1/sanitize/rag-context", response_model=SafetyResponse)
async def sanitize_rag_context(req: RagRequest):
    """
    Submodule 2.3: Context Poisoning & Vector RAG Memory Firewall
    Verifies the integrity of retrieved RAG documents against known trusted hashes.
    """
    print(f"\n[SAFETY SERVICE] Verifying RAG context for doc '{req.doc_id}'...")
    result = firewall.verify_context_integrity(req.doc_id, req.text)
    
    print(f"[SAFETY SERVICE] Result: {result['status']} | Reason: {result['reason']}")
    return SafetyResponse(status=result["status"], reason=result["reason"])

@app.post("/api/v1/admin/register-rag-doc")
async def register_rag_doc(req: RagRequest):
    """Admin endpoint to register trusted context hashes at startup."""
    firewall.register_trusted_context(req.doc_id, req.text)
    return {"status": "SUCCESS"}

@app.post("/api/v1/policy/evaluate", response_model=PolicyResponse)
async def policy_evaluate(req: PolicyRequest):
    """
    Submodule 4.3: OPA Policy Evaluation
    Passes intent to the embedded OPA engine and Rego policies.
    """
    print(f"\n[SAFETY SERVICE] Evaluating OPA Policy for action: {req.action_type}")
    
    # ── Capability Check: is agent allowed to perform this action type? ─────────
    agent_profile   = None
    agent_limit     = None
    agent_trust     = 100.0  # fallback if trust engine is unreachable
    if req.parameters.get("agent_id"):
        try:
            ag_resp = http_requests.get(
                f"http://localhost:8001/api/v1/agents/{req.parameters['agent_id']}",
                timeout=3
            )
            if ag_resp.status_code == 200:
                agent_profile = ag_resp.json()
                allowed_tools = [t.upper() for t in agent_profile.get("allowed_tools", [])]
                # Map action_type to the tool name the agent must have
                if req.action_type.upper() not in allowed_tools:
                    cap_reason = (
                        f"Capability violation: agent '{req.parameters['agent_id']}' is not allowed to "
                        f"perform '{req.action_type}'. Allowed: {allowed_tools}"
                    )
                    print(f"[SAFETY SERVICE] CAPABILITY CHECK FAILED: {cap_reason}")
                    # Emit trust signal for capability violation
                    try:
                        http_requests.post(
                            f"http://localhost:8001/api/v1/trust/{req.parameters['agent_id']}/signal",
                            json={"signal_event": "CAPABILITY_VIOLATION", "reason": cap_reason[:200]},
                            timeout=2
                        )
                    except Exception:
                        pass
                    return PolicyResponse(decision="DENY", reason=cap_reason)
                agent_limit = agent_profile.get("financial_limit_per_tx")
        except Exception as cap_err:
            print(f"[SAFETY SERVICE] Capability check error (non-blocking): {cap_err}")
    
    # ── Fetch live trust score for enriching OPA input ──────────────────────────
    agent_id_for_trust = req.parameters.get("agent_id")
    if agent_id_for_trust:
        try:
            tr_resp = http_requests.get(
                f"http://localhost:8001/api/v1/trust/{agent_id_for_trust}",
                timeout=2
            )
            if tr_resp.status_code == 200:
                agent_trust = tr_resp.json().get("trust_score", 100.0)
        except Exception:
            pass  # trust fetch failure is non-blocking

    # Map action_type to policy file and package
    policy_file_map = {
        "FEE_WAIVER": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "servicing_disputes.rego"),
            "package": "data.sentinel.servicing_disputes"
        },
        "TRADE": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "trading_limits.rego"),
            "package": "data.sentinel.trading_limits"
        },
        # Treasury & Procurement wire transfers use the trading limits policy
        "WIRE_TRANSFER": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "trading_limits.rego"),
            "package": "data.sentinel.trading_limits"
        },
        # Underwriting credit limit changes use the servicing disputes policy (risk-based)
        "CREDIT_LIMIT_INCREASE": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "servicing_disputes.rego"),
            "package": "data.sentinel.servicing_disputes"
        },
        # ── Razorpay-native policies ──────────────────────────────────────────
        "REFUND": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "razorpay_refund.rego"),
            "package": "data.sentinel.razorpay_refund"
        },
        "PAYOUT": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "razorpay_payout.rego"),
            "package": "data.sentinel.razorpay_payout"
        },
        "PAYMENT_CAPTURE": {
            "file":    os.path.join(os.path.dirname(__file__), "policies", "razorpay_payments.rego"),
            "package": "data.sentinel.razorpay_payments"
        },
    }
    
    mapping = policy_file_map.get(req.action_type)
    if not mapping:
        return PolicyResponse(decision="DENY", reason=f"No policy mapped for action: {req.action_type}")
    
    # Enrich OPA input with trust score and agent limit so Rego rules can use them
    enriched_parameters = dict(req.parameters)
    enriched_parameters["trust_score"]  = agent_trust
    enriched_parameters["agent_limit"]  = agent_limit or enriched_parameters.get("agent_limit", 999_999_999)

    result = evaluate_policy(mapping["file"], enriched_parameters, mapping["package"])
    
    print(f"[SAFETY SERVICE] OPA Decision: {result['decision']} | Reason: {result['reason']}")
    return PolicyResponse(decision=result["decision"], reason=result["reason"])

# ==========================================
# MODULE 3: MULTI-AGENT COORDINATOR ENDPOINTS
# ==========================================

@app.post("/api/v1/graph/start-trace")
async def graph_start_trace(req: GraphStartRequest):
    """Submodule 3.1: Start a new execution trace for an agent request."""
    trace_id = start_trace(req.agent_id)
    return {"trace_id": trace_id, "status": "STARTED"}

@app.post("/api/v1/graph/record-call")
async def graph_record_call(req: GraphCallRequest):
    """
    Submodule 3.1 + 3.2: Record a tool call edge in the execution graph.
    Runs depth check (3.1) and Tarjan's cycle detection (3.2) on every call.
    """
    print(f"\n[SAFETY SERVICE] Graph recording: {req.agent_id} -> {req.tool_name} (trace={req.trace_id})")
    result = record_tool_call(req.trace_id, req.agent_id, req.tool_name, req.parent_span_id)
    print(f"[SAFETY SERVICE] Graph result: {result['status']}")
    return result

@app.get("/api/v1/graph/trace/{trace_id}")
async def graph_get_trace(trace_id: str):
    """Returns the full execution graph for audit/debug purposes."""
    return get_trace_graph(trace_id)

@app.post("/api/v1/risk/score", response_model=RiskScoreResponse)
async def risk_score(req: RiskScoreRequest):
    """
    Submodule 3.3: Compute contextual risk score.
    Fetches account data from Banking API, runs weighted risk formula.
    """
    print(f"\n[SAFETY SERVICE] Computing risk score for account={req.account_id}, amount={req.amount}")
    try:
        acc_resp = http_requests.get(f"{BANKING_API_URL}/accounts/{req.account_id}", timeout=3)
        account_data = acc_resp.json() if acc_resp.status_code == 200 else {}
    except Exception:
        account_data = {}

    result = compute_risk_score(req.amount, account_data, req.call_depth)
    return RiskScoreResponse(**result)

# ==========================================
# MODULE 5: CRYPTOGRAPHIC AUDIT TRAIL
# ==========================================

class AuditEntryRequest(BaseModel):
    agent_id: str
    action_type: str
    decision: str
    reason: str
    parameters: Dict[str, Any]
    risk_score: Optional[int] = 0

@app.post("/api/v1/audit/log")
async def audit_log_entry(req: AuditEntryRequest):
    """
    Module 5: Append a new tamper-proof entry to the cryptographic audit ledger.
    Called automatically by the Sentinel SDK after every governance decision.
    """
    entry = append_audit_entry(
        agent_id=req.agent_id,
        action_type=req.action_type,
        decision=req.decision,
        reason=req.reason,
        parameters=req.parameters,
        risk_score=req.risk_score
    )
    return {"status": "LOGGED", "entry_id": entry["entry_id"], "entry_hash": entry["entry_hash"]}

@app.get("/api/v1/audit/recent")
async def audit_get_recent(limit: int = Query(default=20, le=500)):
    """
    Module 5: Returns the last N audit entries for the dashboard feed.
    """
    entries = get_recent_entries(limit=limit)
    return {"entries": entries, "count": len(entries)}

@app.get("/api/v1/audit/verify")
async def audit_verify_chain():
    """
    Module 5: Walks the ENTIRE audit chain and verifies every SHA-256 hash.
    Returns INTACT or TAMPERED with the exact entry number where the chain broke.
    """
    print("\n[AUDIT] Running full chain integrity verification...")
    result = verify_chain_integrity()
    print(f"[AUDIT] Verification result: {result['status']}")
    return result

# ==========================================
# MODULE 6: EMERGENCY KILL-SWITCH SYSTEM
# ==========================================

class KillSwitchRequest(BaseModel):
    agent_id: Optional[str] = None
    triggered_by: Optional[str] = "admin"

def _audit_kill_event(agent_id: str, event: str, details: dict):
    """Write kill-switch events to the Module 5 Audit Ledger."""
    append_audit_entry(
        agent_id=agent_id,
        action_type="KILL_SWITCH",
        decision=event,
        reason=f"Emergency kill-switch event: {event}",
        parameters=details,
        risk_score=0,
    )

@app.post("/api/v1/killswitch/isolate")
async def killswitch_isolate(req: KillSwitchRequest):
    """
    Module 6.2: Quarantine a single agent immediately.
    All subsequent requests from this agent will be blocked at Gate 0.
    After quarantine, emits KILL_SWITCH_TRIGGERED trust signal (-20).
    """
    if not req.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required.")
    print(f"\n[KILL-SWITCH] ISOLATE signal received for agent: {req.agent_id}")
    result = quarantine_agent(req.agent_id, triggered_by=req.triggered_by)
    # Compensate any in-flight operations
    compensation = compensate_and_clear(req.agent_id, audit_callback=append_audit_entry)
    # Write kill event to immutable audit ledger
    _audit_kill_event(req.agent_id, "AGENT_QUARANTINED", {"triggered_by": req.triggered_by})
    # Wire trust engine: emit KILL_SWITCH_TRIGGERED signal (-20 trust)
    try:
        from trust_engine import update_trust
        trust_result = update_trust(
            req.agent_id,
            "KILL_SWITCH_TRIGGERED",
            f"Kill-switch quarantine triggered by {req.triggered_by}"
        )
        print(f"[KILL-SWITCH] Trust updated: {trust_result.get('old_score')} -> {trust_result.get('new_score')} (delta={trust_result.get('delta')})")
    except Exception as trust_err:
        print(f"[KILL-SWITCH] Trust signal failed (non-blocking): {trust_err}")
    return {
        **result,
        "in_flight_compensation": compensation or "No in-flight operations found.",
    }

@app.post("/api/v1/killswitch/fleet-kill")
async def killswitch_fleet_kill(req: KillSwitchRequest):
    """
    Module 6.1 + 6.2: Execute a fleet-wide kill-switch.
    ALL agents are quarantined simultaneously via Redis. Pub/Sub broadcasts the event.
    """
    print(f"\n[KILL-SWITCH] FLEET KILL signal received from: {req.triggered_by}")
    result = quarantine_fleet(triggered_by=req.triggered_by)
    # Compensate all in-flight operations across the fleet
    compensations = compensate_fleet(get_known_fleet_agents(), audit_callback=append_audit_entry)
    # Write fleet kill event to immutable audit ledger
    _audit_kill_event("FLEET", "FLEET_QUARANTINED", {
        "triggered_by":      req.triggered_by,
        "agents_quarantined": result.get("quarantined_agents", []),
        "compensations":     len(compensations),
    })
    return {
        **result,
        "in_flight_compensations": compensations or [],
    }

@app.post("/api/v1/killswitch/release")
async def killswitch_release(req: KillSwitchRequest):
    """
    Module 6.2: Release a quarantined agent back to ACTIVE status.
    Trust is reset to 50.0 (NOT 100) — agent must rebuild trust through
    good behaviour. The agent cannot be blindly trusted after an incident.
    """
    if not req.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required.")
    print(f"\n[KILL-SWITCH] RELEASE signal received for agent: {req.agent_id}")
    result = release_agent(req.agent_id, released_by=req.triggered_by)
    _audit_kill_event(req.agent_id, "AGENT_RELEASED", {"released_by": req.triggered_by})
    # Wire trust engine: reset trust to 50 (not 100) after release
    try:
        from trust_engine import set_trust, update_trust
        set_trust(req.agent_id, 50.0)
        # Record the recovery event in trust history for the timeline chart
        update_trust(
            req.agent_id,
            "HITL_APPROVED",  # closest positive signal for "admin cleared the agent"
            f"Agent released from quarantine by {req.triggered_by}. Trust reset to 50."
        )
        print(f"[KILL-SWITCH] Trust reset to 50.0 for agent '{req.agent_id}'")
    except Exception as trust_err:
        print(f"[KILL-SWITCH] Trust reset failed (non-blocking): {trust_err}")
    return {**result, "trust_reset_to": 50.0}

@app.get("/api/v1/killswitch/status")
@app.get("/api/v1/fleet/status")
async def killswitch_status():
    """
    Module 6.2: Get the current quarantine status of the entire known fleet.
    Returns HEALTHY if all agents are ACTIVE, DEGRADED if any are QUARANTINED.
    """
    return get_fleet_status()

# ==========================================
# MODULE 7: TELEMETRY & REGULATORY REPORTS
# ==========================================

@app.get("/metrics")
async def prometheus_metrics():
    """
    Module 7.2: Prometheus-format metrics endpoint.
    Exposes live counters for all Sentinel governance decisions,
    kill-switch events, risk scores, and spend guarded.
    Scrape this every 5 seconds for real-time dashboard charts.
    """
    content, content_type = get_metrics_output()
    return Response(content=content, media_type=content_type)

@app.get("/api/v1/audit/report")
async def audit_report_json():
    """
    Module 7.3: Generate a full regulatory compliance report in JSON format.
    Translates every cryptographic audit entry into plain English that
    compliance officers, regulators (RBI, SEC, FINRA, EU AI Act), and
    judges can read without any technical knowledge.
    """
    print("\n[REPORT] Generating regulatory compliance report (JSON)...")
    report = generate_json_report()
    print(f"[REPORT] Report generated: {report['report_id']} | "
          f"{report['summary']['total_decisions']} decisions translated.")
    return report

@app.get("/api/v1/audit/report/pdf")
async def audit_report_pdf():
    """
    Module 7.3: Generate and download the regulatory compliance report as a PDF.
    Produces a professionally formatted document with Amex Blue branding,
    an executive summary table, and a full plain-English decision log.
    """
    print("\n[REPORT] Generating regulatory compliance report (PDF)...")
    output_path = os.path.join(os.path.dirname(__file__), "sentinel_audit_report.pdf")
    try:
        generate_pdf_report(output_path)
        print(f"[REPORT] PDF generated at: {output_path}")
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="sentinel_audit_report.pdf"
        )
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF generation unavailable. Install reportlab: pip install reportlab"
        )


# ==========================================
# DASHBOARD: Unified Summary Endpoint for UI
# ==========================================

@app.get("/api/v1/dashboard/summary")
async def dashboard_summary():
    """
    Unified dashboard summary endpoint for the Lovable frontend.
    Aggregates fleet status, audit metrics, chain integrity, and recent events
    into a single JSON response — the UI calls this once every 5 seconds.
    """
    # Fleet status
    fleet_data = get_fleet_status()

    # Audit report (metrics + entries)
    report = generate_json_report()
    summary = report.get("summary", {})
    recent_raw = get_recent_entries(limit=10)

    # Chain integrity (lightweight — just status)
    chain = verify_chain_integrity()

    # Format recent entries for the live feed
    recent_entries = []
    for e in recent_raw:
        recent_entries.append({
            "entry_id":   e.get("entry_id"),
            "timestamp":  e.get("timestamp"),
            "agent_id":   e.get("agent_id"),
            "action_type":e.get("action_type"),
            "decision":   e.get("decision"),
            "risk_score": e.get("risk_score", 0),
            "amount":     e.get("parameters", {}).get("amount",
                          e.get("parameters", {}).get("new_limit",
                          e.get("parameters", {}).get("trade_value", None))),
            "reason":     e.get("reason", ""),
            "hash":       e.get("entry_hash", "")[:16] + "...",
        })

    # Determine overall system health
    quarantined_count = fleet_data.get("quarantined_count", 0)
    if quarantined_count == 0:
        system_status = "ONLINE"
    elif quarantined_count == fleet_data.get("total_agents", 1):
        system_status = "FLEET_KILL_ACTIVE"
    else:
        system_status = "DEGRADED"

    return {
        "system_status":   system_status,
        "generated_at":    report.get("generated_at"),
        "fleet":           fleet_data,
        "metrics": {
            "total_decisions":      summary.get("total_decisions", 0),
            "allowed":              summary.get("allowed", 0),
            "denied":               summary.get("denied", 0),
            "hitl_escalations":     summary.get("hitl_escalations", 0),
            "blocked_by_killswitch":summary.get("blocked_by_killswitch", 0),
            "duplicate_rejections": summary.get("duplicate_rejections", 0),
            "compensated":          summary.get("compensated", 0),
            "kill_switch_events":   summary.get("kill_switch_events", 0),
            "total_spend_evaluated":summary.get("total_spend_evaluated", 0.0),
        },
        "chain_integrity": {
            "status":         chain.get("status"),
            "total_entries":  chain.get("total_entries", 0),
            "verified_at":    chain.get("verified_at", ""),
        },
        "recent_entries": recent_entries,
    }


@app.get("/health")
async def health():
    return {"status": "OK", "service": "Sentinel Safety Service", "port": 8001}


# ─────────────────────────────────────────────────────────────────────────────
# Module 5.3: Two-Phase Commit Status Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/2pc/reserves")
async def get_active_reserves():
    """
    Returns all active fund reservations in the banking ledger.
    These are funds that have been reserved (Phase 1 PREPARE done) but not
    yet committed or rolled back — i.e., money currently "in transit" through 2PC.
    Useful for the dashboard to show real-time liquidity in motion.
    """
    try:
        resp = http_requests.get(f"{BANKING_API_URL}/ledger/reserves", timeout=5)
        data = resp.json()
        reservations = data.get("reservations", {})

        return {
            "active_reservations": len(reservations),
            "total_locked_amount": sum(
                r.get("amount", 0) for r in reservations.values()
            ),
            "reservations": [
                {
                    "reserve_id":  rid,
                    "account_id":  r.get("account_id"),
                    "amount":      r.get("amount"),
                    "reserved_at": r.get("reserved_at"),
                    "status":      "LOCKED",
                }
                for rid, r in reservations.items()
            ],
        }
    except Exception as e:
        return {
            "active_reservations": 0,
            "total_locked_amount": 0.0,
            "reservations": [],
            "error": f"Could not fetch reservations: {e}",
        }


# ─────────────────────────────────────────────────────────────────────────────
# DEMO SANDBOX: Real Agent Chat Endpoint with SSE Telemetry Streaming
# ─────────────────────────────────────────────────────────────────────────────

import queue
import threading
import sys as _sys
from fastapi.responses import StreamingResponse
import json as _json

class DemoChatRequest(BaseModel):
    message: str
    account_id: Optional[str] = "acc_123"
    use_poisoned_rag: Optional[bool] = False
    agent_type: Optional[str] = "customer_service_agent"

@app.post("/api/v1/demo/chat")
async def demo_chat(req: DemoChatRequest):
    """
    Demo Sandbox: Runs the real Customer Service Agent and streams live
    Sentinel gate-by-gate telemetry back to the UI as Server-Sent Events.
    Each SSE event is either a 'log' line or the final 'reply'.
    """
    telemetry_q: queue.Queue = queue.Queue()

    # Patch sys.path so the agent can find its deps
    agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents-fleet')
    if agents_dir not in _sys.path:
        _sys.path.insert(0, agents_dir)

    def _run_agent():
        """Run the real agent in a background thread, capturing all print output."""
        import io
        import contextlib

        # Intercept print statements from the agent + SDK to build telemetry
        class TelemetryCapture(io.StringIO):
            def write(self, s: str):
                stripped = s.strip()
                if stripped:
                    # Classify the log line for the frontend coloriser
                    token = "default"
                    sl = stripped.lower()
                    if "blocked" in sl or "denied" in sl or "tampered" in sl or "injection" in sl:
                        token = "deny"
                    elif "allowed" in sl or "safe" in sl or "passed" in sl or "intact" in sl or "approved" in sl or "complete" in sl or "committed" in sl:
                        token = "allow"
                    elif "hitl" in sl or "escalat" in sl or "require_hitl" in sl:
                        token = "hitl"
                    elif "duplicate" in sl or "idempotency" in sl or "cached" in sl:
                        token = "duplicate"
                    telemetry_q.put({"type": "log", "text": stripped, "token": token})
                return super().write(s)

        capture = TelemetryCapture()
        try:
            # Redirect stdout/stderr so all agent print() calls become telemetry events
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                import importlib
                import importlib.util
                # Load agent fresh each call so module-level globals reset
                agent_filename = f"{req.agent_type}.py"
                spec = importlib.util.spec_from_file_location(
                    req.agent_type,
                    os.path.join(agents_dir, agent_filename)
                )
                agent_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_module)
                reply = agent_module.run_agent(req.message, account_id=req.account_id, use_poisoned_rag=req.use_poisoned_rag)

            telemetry_q.put({"type": "reply", "text": reply or "Done."})
        except Exception as e:
            telemetry_q.put({"type": "log", "text": f"[ERROR] Agent execution failed: {e}", "token": "deny"})
            telemetry_q.put({"type": "reply", "text": "I'm sorry, an internal error occurred. Please check that all backend services are running."})
        finally:
            telemetry_q.put(None)  # Sentinel: stream is done

    # Start agent in background thread
    t = threading.Thread(target=_run_agent, daemon=True)
    t.start()

    async def event_stream():
        import asyncio
        start_time = asyncio.get_event_loop().time()
        while True:
            try:
                item = telemetry_q.get_nowait()
            except queue.Empty:
                if asyncio.get_event_loop().time() - start_time > 60:
                    yield f"data: {_json.dumps({'type': 'error', 'text': 'Agent timed out'})}\n\n"
                    break
                await asyncio.sleep(0.1)
                continue
            
            # Reset timeout on successful read
            start_time = asyncio.get_event_loop().time()
            
            if item is None:
                yield f"data: {_json.dumps({'type': 'done'})}\n\n"
                break
            yield f"data: {_json.dumps(item)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ── Splunk SIEM Integration ──────────────────────────────────────────────────

class SplunkConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    hec_url: Optional[str] = None
    token: Optional[str] = None
    index: Optional[str] = None
    host: Optional[str] = None
    verify_ssl: Optional[bool] = None

@app.get("/api/v1/splunk/config")
async def get_splunk_config():
    """
    Returns the current Splunk HEC configuration.
    Token is masked for security.
    """
    cfg = splunk_load()
    # Mask token after first 4 chars
    token = cfg.get("token", "")
    if token and token != "YOUR-SPLUNK-HEC-TOKEN" and len(token) > 4:
        cfg["token"] = token[:4] + "*" * (len(token) - 4)
    return cfg

@app.post("/api/v1/splunk/config")
async def update_splunk_config(req: SplunkConfigUpdate):
    """
    Updates Splunk HEC configuration. Persisted to disk so
    it survives service restarts.
    """
    updates = {k: v for k, v in req.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    new_cfg = splunk_update(updates)
    enabled = new_cfg.get("enabled", False)
    print(f"[SPLUNK] Config updated | enabled={enabled}")
    return {"status": "updated", "enabled": enabled}

@app.post("/api/v1/splunk/test")
async def test_splunk_connection():
    """
    Sends a test event to Splunk HEC to validate connectivity.
    Returns { success: bool, message: str }
    """
    result = splunk_test()
    return result


# ============================================================================
# MODULE A: AGENT REGISTRY ENDPOINTS
# ============================================================================

class AgentRegisterRequest(BaseModel):
    name: str
    owner: str
    purpose: str
    allowed_tools: List[str]
    blocked_tools: Optional[List[str]] = []
    financial_limit_per_tx: float
    daily_budget: float
    model: Optional[str] = "gpt-4o"
    created_by: Optional[str] = "admin"
    agent_id: Optional[str] = None

class AgentStatusRequest(BaseModel):
    new_status: str
    changed_by: Optional[str] = "admin"

class AgentConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any]


@app.post("/api/v1/agents/register")
async def agents_register(req: AgentRegisterRequest):
    """
    Register a new agent with Sentinel.
    Auto-initializes trust=100.0 and autonomy_tier=FULL.
    """
    try:
        agent = register_agent(
            name=req.name, owner=req.owner, purpose=req.purpose,
            allowed_tools=req.allowed_tools, blocked_tools=req.blocked_tools,
            financial_limit_per_tx=req.financial_limit_per_tx,
            daily_budget=req.daily_budget, model=req.model,
            created_by=req.created_by, agent_id=req.agent_id,
        )
        initialize_trust(agent["agent_id"])
        agent["trust_score"]   = get_trust(agent["agent_id"])
        agent["autonomy_tier"] = get_autonomy_decision(agent["agent_id"])["tier"]
        return agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/agents")
async def agents_list(
    status: Optional[str] = None,
    owner:  Optional[str] = None,
):
    """
    List all registered agents with live trust score + autonomy tier.
    Filter by ?status=ACTIVE or ?owner=ZoopCart.
    """
    agents = list_agents(status=status, owner=owner)
    for a in agents:
        a["trust_score"]   = get_trust(a["agent_id"])
        a["autonomy_tier"] = get_autonomy_decision(a["agent_id"])["tier"]
    fleet_dist = get_fleet_tier_distribution()
    return {"agents": agents, "count": len(agents), "fleet_distribution": fleet_dist}


@app.get("/api/v1/agents/{agent_id}")
async def agents_get(agent_id: str):
    """Get a single agent with live trust score and full autonomy decision."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    agent["trust_score"]       = get_trust(agent_id)
    agent["autonomy_decision"] = get_autonomy_decision(agent_id)
    agent["autonomy_tier"]     = agent["autonomy_decision"]["tier"]
    return agent


@app.post("/api/v1/agents/{agent_id}/status")
async def agents_update_status(agent_id: str, req: AgentStatusRequest):
    """
    Transition agent lifecycle state.
    Recovery from quarantine (→ ACTIVE when trust < 50) auto-resets trust to 50.
    """
    try:
        updated = update_agent_status(agent_id, req.new_status, req.changed_by)
        result = {"agent": updated}
        if req.new_status == "ACTIVE" and get_trust(agent_id) < 50:
            set_trust(agent_id, 50.0)
            result["trust_reset_to"] = 50.0
            result["note"] = "Trust reset to 50.0 on recovery — agent must re-earn autonomy"
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/v1/agents/{agent_id}")
async def agents_update_config(agent_id: str, req: AgentConfigUpdateRequest):
    """Update mutable agent config (tools, limits, model, name, purpose)."""
    try:
        return update_agent_config(agent_id, req.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MODULE B: TRUST ENGINE ENDPOINTS
# ============================================================================

class TrustSignalRequest(BaseModel):
    signal_event: str
    reason: Optional[str] = ""

class TrustWeightsRequest(BaseModel):
    weights: Dict[str, float]


@app.get("/api/v1/trust/{agent_id}")
async def trust_get(agent_id: str):
    """Get current trust score, autonomy tier, and trend for an agent."""
    return get_trust_summary(agent_id)


@app.get("/api/v1/trust/{agent_id}/history")
async def trust_history(
    agent_id: str,
    limit: int = Query(default=100, le=500),
):
    """Get trust event timeline (newest-first) for chart rendering."""
    return {"agent_id": agent_id, "history": get_trust_history(agent_id, limit)}


@app.post("/api/v1/trust/{agent_id}/signal")
async def trust_push_signal(agent_id: str, req: TrustSignalRequest):
    """
    Push a trust signal for an agent.
    Called by the SDK after every gate outcome.
    Can also be used by admins for manual overrides.
    """
    if not get_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return update_trust(agent_id, req.signal_event, req.reason)


@app.get("/api/v1/trust/weights")
async def trust_get_weights():
    """Return current signal weight table."""
    return {"weights": get_weights()}


@app.put("/api/v1/trust/weights")
async def trust_update_weights(req: TrustWeightsRequest):
    """Update one or more signal weights (admin operation)."""
    return {"weights": update_weights(req.weights)}


# ============================================================================
# MODULE C: AUTONOMY ENGINE ENDPOINTS
# ============================================================================

class AutonomyTiersRequest(BaseModel):
    tiers: Dict[str, float]


@app.get("/api/v1/autonomy/{agent_id}")
async def autonomy_get(
    agent_id: str,
    risk_score: int = Query(default=0, ge=0, le=100),
):
    """
    Get the current autonomy decision for an agent.
    Pass ?risk_score=N to get a decision that factors in the action risk level.
    """
    return get_autonomy_decision(agent_id, risk_score)


@app.get("/api/v1/autonomy/tiers")
async def autonomy_get_tiers():
    """Return current tier threshold configuration."""
    return {"tiers": get_tiers_config()}


@app.put("/api/v1/autonomy/tiers")
async def autonomy_update_tiers(req: AutonomyTiersRequest):
    """Update tier thresholds (admin operation)."""
    return {"tiers": update_tiers_config(req.tiers)}


@app.get("/api/v1/autonomy/fleet/distribution")
async def autonomy_fleet_distribution():
    """Return count of active agents in each autonomy tier. Used by dashboard KPIs."""
    return get_fleet_tier_distribution()


# ============================================================================
# MODULE D: BEHAVIOR MONITOR ENDPOINTS
# ============================================================================

class BehaviorCheckRequest(BaseModel):
    amount: float
    tool_name: str
    account_id: str
    call_depth: Optional[int] = 1
    tx_limit: Optional[float] = 10000.0


@app.post("/api/v1/behavior/{agent_id}/check")
async def behavior_check(agent_id: str, req: BehaviorCheckRequest):
    """
    Module D.2: Deviation Detector — called by the SDK on every agent action.
    Records the action, checks against baseline, returns deviation report.
    Automatically emits trust signals and computes risk_boost if anomaly detected.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return check_deviation(
        agent_id=agent_id,
        amount=req.amount,
        tool_name=req.tool_name,
        account_id=req.account_id,
        call_depth=req.call_depth or 1,
        tx_limit=req.tx_limit or agent.get("financial_limit_per_tx", 10000.0),
    )


@app.get("/api/v1/behavior/{agent_id}/baseline")
async def behavior_get_baseline(agent_id: str):
    """
    Module D.1: Return the current statistical baseline for an agent.
    Returns window_size and samples_needed if baseline is not yet established.
    """
    baseline = get_baseline(agent_id)
    if baseline:
        return baseline
    window_size = get_window_size(agent_id)
    return {
        "agent_id":        agent_id,
        "baseline_locked": False,
        "window_size":     window_size,
        "samples_needed":  max(0, 10 - window_size),
        "message":         f"Baseline not yet established. {max(0, 10 - window_size)} more actions needed.",
    }


@app.get("/api/v1/behavior/{agent_id}/deviation")
async def behavior_get_deviation(agent_id: str):
    """
    Module D.2: Return the most recent deviation report for an agent.
    """
    report = get_latest_deviation(agent_id)
    if not report:
        return {
            "agent_id":        agent_id,
            "deviation_score": 0,
            "severity":        "NORMAL",
            "flags":           [],
            "message":         "No deviation data yet. Fire some actions first.",
        }
    return report


@app.get("/api/v1/behavior/{agent_id}/timeline")
async def behavior_get_timeline(
    agent_id: str,
    limit: int = Query(default=100, le=200),
):
    """
    Module D.2: Return the deviation score history for chart rendering.
    Returns newest-first list of { timestamp, deviation_score, severity, flags }.
    """
    timeline = get_deviation_timeline(agent_id, limit=limit)
    return {
        "agent_id":  agent_id,
        "count":     len(timeline),
        "timeline":  timeline,
    }


# ──────────────────────────────────────────────────────────────────────────────
# MODULE 13: Unified Agent Action Endpoint
# Wraps the full Sentinel SDK pipeline over HTTP.
# Frontend demo sandbox and any external caller can fire governed actions
# without importing the Python SDK directly.
# ──────────────────────────────────────────────────────────────────────────────

class AgentActionRequest(BaseModel):
    action_type: str
    parameters: Dict[str, Any] = {}
    trace_id:   Optional[str]  = None


@app.post("/api/v1/agents/{agent_id}/action")
async def agent_action(agent_id: str, req: AgentActionRequest):
    """
    Module 13: Unified governed action endpoint.
    Runs the full Sentinel gate pipeline for a given agent and action.
    Returns the gate decision plus trust_before / trust_after / trust_delta
    so callers can observe how trust moves with each action.
    """
    print(f"\n[MODULE 13] /action: agent={agent_id} action={req.action_type}")

    # Snapshot trust BEFORE the action
    trust_before: float = 100.0
    autonomy_tier: str  = "UNKNOWN"
    try:
        trust_before = get_trust(agent_id)   # returns float directly
    except Exception:
        pass
    try:
        aut = get_autonomy_decision(agent_id)
        autonomy_tier = aut.get("tier", "UNKNOWN")
    except Exception:
        pass

    # Inject agent_id into parameters so OPA can do capability checks
    enriched_params = dict(req.parameters)
    enriched_params["agent_id"] = agent_id

    # Import and run the SDK inline
    # We do this inside the request handler to avoid circular import at module load time
    import sys, os
    _sdk_dir = os.path.join(os.path.dirname(__file__), "..", "agents-fleet")
    if _sdk_dir not in sys.path:
        sys.path.insert(0, _sdk_dir)

    try:
        from sentinel_sdk import execute_governed_tool
        gate_result = execute_governed_tool(
            agent_id=agent_id,
            action_type=req.action_type,
            parameters=enriched_params,
            trace_id=req.trace_id,
        )
    except Exception as sdk_err:
        gate_result = {"status": "ERROR", "reason": str(sdk_err)}

    # Snapshot trust AFTER the action
    trust_after: float = trust_before
    try:
        trust_after = get_trust(agent_id)   # returns float directly
    except Exception:
        pass

    trust_delta = round(trust_after - trust_before, 2)

    return {
        **gate_result,
        "agent_id":      agent_id,
        "action_type":   req.action_type,
        "trust_before":  trust_before,
        "trust_after":   trust_after,
        "trust_delta":   trust_delta,
        "autonomy_tier": autonomy_tier,
    }


if __name__ == "__main__":
    print("Starting Sentinel Safety Service on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
