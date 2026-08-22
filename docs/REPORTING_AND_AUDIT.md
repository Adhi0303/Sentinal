# Cryptographic Audit Ledger & Compliance Reporting

When AI agents manage real money, standard logging is insufficient. Logs can be tampered with, deleted, or accidentally altered. Sentinel solves this by implementing a **Cryptographic Hash Chain Ledger**.

## The Audit Log (`audit_log.jsonl`)

Every time an action completes its journey through the 9-gate pipeline (whether it was APPROVED, DENIED, or flagged for HITL), a comprehensive event object is generated. 

This object contains:
- `trace_id` & `timestamp`
- `agent_id`, `action_type`, and exact `parameters`
- The results of every individual gate check.
- The `trust_before`, `trust_after`, and `trust_delta`.
- The final `status`.

**The Cryptographic Link**:
Before the event is appended to `audit_log.jsonl`, Sentinel takes the SHA-256 hash of the *previous* event in the file and embeds it into the current event as `prev_hash`. It then hashes the current event to generate the `hash` for the current line.

This creates an unbreakable blockchain-style ledger. If a single byte of historical log data is altered, all subsequent hashes become invalid, instantly flagging the tamper attempt.

## The Report Generator (`report_generator.py`)

Financial institutions require formal compliance reports to prove that autonomous agents are operating safely. The Sentinel Report Generator automates this process.

When a compliance report is requested:
1. **Verification**: The system reads the entire `audit_log.jsonl` file and recalculates every hash from the genesis block to the tip. If the chain is broken, the report halts and flags a critical compliance failure.
2. **Aggregation**: The system calculates metrics specific to Razorpay integrations, such as:
   - Total Refunds Processed
   - Total Payouts Evaluated
   - Total INR (₹) Spend Evaluated
   - Count of actions blocked by policies or kill switches.
   - Count of HITL escalations.
3. **Translation**: The system translates the raw JSON event data into plain English audit paragraphs (e.g., *"✅ REFUND ₹2000.00 PROCESSED by refund-agent-001 (Trace: abc-123)"*).

### Export Formats
The report is exposed via REST endpoints in two formats:
- `/api/v1/audit/report` (Raw JSON for programmatic compliance checks).
- `/api/v1/audit/report/pdf` (A downloadable, professionally formatted PDF generated using `ReportLab`, suitable for human auditors).
