# Sentinel: Zero Trust Governance Control Plane for Autonomous Financial AI Agents

## The Problem Worth Solving

Financial institutions are at an inflection point. Autonomous AI agents are no longer theoretical. They are being deployed right now to process refunds, execute wire transfers, manage merchant settlements, and resolve customer disputes at a scale no human team could match.

The problem is not the agents themselves. The problem is what happens when something goes wrong.

A misaligned agent does not make one mistake. It can make ten thousand mistakes per second before anyone notices. A single compromised prompt can redirect an agent into executing unauthorized transactions. A cascading failure across a multi-agent workflow can corrupt ledgers in ways that take days to untangle. And yet, most organizations deploying autonomous AI today are relying on the same static access controls built for humans clicking buttons, not for software executing millions of decisions per hour.

This is the governance gap Sentinel was built to close.

---

## What Sentinel Is

Sentinel is a production-ready, inline Zero Trust Governance Control Plane that sits between autonomous AI agents and the financial APIs they control. Every single action an agent attempts, whether it is a fee waiver, a wire transfer, or a payment capture, passes through Sentinel before it reaches the underlying banking system.

Sentinel does not just check whether an action is "allowed." It evaluates the action against the agent's current trust state, behavioral baseline, active business policies, contextual risk factors, and real-time operational context, all within milliseconds. It is the difference between giving a contractor a key to your building versus giving them a key that tracks where they go, what they touch, and revokes access the moment they do something unexpected.

The system ships with a fully working demo around a consumer banking workflow, where a Customer Service Agent handles fee waivers and a Treasury Agent handles high-value wire transfers. The demo shows Sentinel's three core behaviors in real time: allowing a safe action, escalating a high-risk action to a human, and hard-blocking a dangerous action.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User / Operator                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Sentinel Admin Dashboard                       │
│          (React + TanStack Router, Port 5173)                   │
│    Agent Fleet · Policy Engine · HITL Queue · Audit Ledger      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌──────────────┐  ┌───────────────┐  ┌──────────────┐
│  Customer    │  │   Treasury    │  │   (Other     │
│  Service     │  │   Agent       │  │   Agents)    │
│  Agent       │  │               │  │              │
└──────┬───────┘  └───────┬───────┘  └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │  Sentinel SDK
                          │  execute_governed_tool()
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               Sentinel Safety Service (Port 8001)               │
│                                                                 │
│  Gate 1: Agent Registry Check                                   │
│  Gate 2: Authentication Validation                              │
│  Gate 3: Schema + Deep Parameter Validation                     │
│  Gate 4: Idempotency Lock (Redis TTL)                           │
│  Gate 5: Hard Financial Limits                                  │
│  Gate 6: Trust + Autonomy Check                                 │
│  Gate 7: OPA Rego Policy Evaluation                             │
│  Gate 8: Behavioral Baseline Monitor                            │
│  Gate 9: Emergency Kill Switch                                  │
│                                                                 │
│  Dynamic Trust Engine · Cryptographic Audit Ledger              │
└─────────────────────────┬───────────────────────────────────────┘
                          │  (Only if ALL 9 gates pass)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Mock Banking API (Port 8000)                       │
│     Accounts · Transactions · Fee Waivers · Wire Transfers      │
└─────────────────────────────────────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    ▼           ▼
              ┌──────────┐  ┌──────────┐
              │  Redis   │  │ Pinecone │
              │  (State) │  │  (RAG)   │
              └──────────┘  └──────────┘
```

Every component on the left side of this diagram is code that runs locally. No action reaches the Mock Banking API without first surviving the complete 9-gate evaluation.

---

## The 9 Gate Governance Pipeline

The core of Sentinel is a sequential interception pipeline. Failure at any gate stops execution immediately, logs a denial event, and applies a trust penalty to the offending agent.

### Gate 1 — Agent Registry Check

Before anything else, Sentinel verifies that the requesting agent is a known, registered entity. Agents must be enrolled in the registry with an explicit identity, allowed tools, financial limits, and an active status. An agent that has been suspended, retired, or never registered at all cannot execute a single action. This prevents rogue or shadow processes from interacting with financial systems even if they somehow obtain an API endpoint.

### Gate 2 — Authentication Validation

Sentinel validates the cryptographic token embedded in every SDK request. This ensures the request originated from a genuine agent process running the approved Sentinel SDK and has not been replayed or spoofed from an external source.

### Gate 3 — Schema and Deep Parameter Validation

Every parameter in every tool call is structurally validated against a strict JSON schema. Beyond structure, Sentinel runs deep content inspection across all string values, scanning for SQL injection patterns, shell injection signatures, and malformed boundary values. An agent that has been manipulated via prompt injection often attempts to pass malicious strings as tool arguments. This gate catches that class of attack before it reaches any logic layer.

### Gate 4 — Idempotency Lock

Autonomous agents frequently retry actions when they do not immediately receive a confirmation. Without idempotency protection, a single intended transaction can become dozens of duplicate executions. Sentinel hashes the combination of agent identity, action type, and parameters and stores the key in Redis with a time-to-live window. An identical request submitted within that window is immediately rejected as a duplicate.

### Gate 5 — Hard Financial Limits

Each registered agent has an absolute maximum transaction value and a daily spend ceiling configured in its registry profile. These limits cannot be overridden by any policy or runtime argument. A customer service agent configured with a $500 per transaction limit cannot execute a $10,000 action no matter what the policy engine or the LLM requests.

### Gate 6 — Trust and Autonomy Check

This is where Sentinel's dynamic governance model becomes visible. Each agent carries a live trust score from 0 to 100. The score changes in real time based on the outcomes of every action the agent takes. The score determines which autonomy tier the agent operates in, and the tier determines how Sentinel handles the current request.

| Trust Score | Autonomy Tier | Behavior |
|---|---|---|
| 90 to 100 | FULL | Actions execute automatically |
| 70 to 89 | BOUNDED | Standard actions auto-approve, high-risk actions escalate |
| 40 to 69 | HITL | Every modifying action requires human approval |
| 0 to 39 | QUARANTINE | All actions blocked |

An agent that starts making policy violations or suspicious requests will see its trust score degrade. As it degrades, Sentinel progressively restricts what the agent can do autonomously, moving it through the tiers until the issue is resolved or a human intervenes.

### Gate 7 — Open Policy Agent (OPA) Rego Evaluation

Business logic is evaluated using Open Policy Agent with Rego policies stored as code. For the demo, the active policy governs wire transfer limits:

- Transfers at or below $10,000 are automatically approved
- Transfers between $10,000 and $100,000 require a human to review and approve
- Transfers above $100,000 are hard-blocked regardless of any other factor

Policies are defined in plain Rego files and can be updated without redeploying any code. The evaluation happens within milliseconds and returns a structured decision that Sentinel uses to either continue, escalate, or deny.

### Gate 8 — Behavioral Baseline Monitor

Traditional policy enforcement only asks whether an action is allowed. Sentinel also asks whether the action is normal for this specific agent.

During an initial learning period, Sentinel records the agent's baseline: average transaction amounts, call velocity, tool usage patterns, and common target accounts. Once the baseline is established, every subsequent action is scored against it across six dimensions: amount deviation, velocity surge, call depth increase, tool drift, target account drift, and limit clustering.

An agent that suddenly attempts a transaction ten times its typical amount, or starts calling tools it has never used before, is exhibiting the exact pattern you would expect from a compromised or manipulated system. Sentinel detects this statistically and fires trust penalties proportional to the severity of the deviation.

### Gate 9 — Emergency Kill Switch

The final check before any action reaches the banking API is a lookup against the kill switch state. Operators can activate kill switches at three levels from the dashboard: for a single agent, for a category of agents, or for the entire fleet. This check runs on every request, which means a fleet-wide shutdown propagates to all active agents within milliseconds of the operator pressing the button.

---

## Adaptive Autonomy: The Core Insight

Most governance systems are binary. An agent either has permission or it does not. Sentinel operates on a spectrum.

The same agent that executes a $10 fee waiver without any human involvement will have that exact same request paused for review if its trust score has dropped due to prior suspicious behavior. The same policy that auto-approves a $5,000 transfer will escalate a $50,000 transfer for human review. The system dynamically calibrates how much autonomy it grants based on real-time evidence rather than static role assignments.

This is the concept of Adaptive Autonomy. The agent's freedom to act is continuously earned and continuously evaluated. The moment evidence of misalignment appears, the system tightens the leash automatically.

---

## AI Safety Layer

Beyond the core governance pipeline, Sentinel includes a dedicated safety layer that runs before and around agent execution.

**Prompt Injection Detection** scans every incoming user prompt for injection patterns before the agent even sees it. The system uses a combination of regex fingerprinting for known attack signatures and LlamaGuard classification for novel adversarial inputs.

**RAG Firewall** protects the agent's knowledge retrieval. When Sentinel retrieves policy documents from the vector store (Pinecone), it verifies the SHA-256 hash of every retrieved chunk against a set of trusted hashes registered at ingestion time. If a retrieved chunk does not match its registered hash, the system blocks the retrieval and flags the anomaly. This prevents RAG poisoning attacks where an adversary modifies the knowledge base to manipulate agent reasoning.

**Graph Cycle Detection** tracks the execution graph of multi-agent interactions. If Agent A calls Agent B which calls Agent C which attempts to call Agent A again, Sentinel detects the cycle and breaks it before it causes a cascading failure or an infinite loop.

---

## Dynamic Trust Engine

Every event that Sentinel observes about an agent generates a trust signal. These signals accumulate in real time and continuously update the agent's score.

| Signal | Score Delta | Description |
|---|---|---|
| TRANSACTION_COMPLETED | +5.0 | Successful, safe action executed |
| HITL_APPROVED | +0.2 | Human reviewed and confirmed the agent was correct |
| ACTION_DENIED_POLICY | -5.0 | Agent attempted something blocked by business rules |
| HIGH_RISK_ESCALATED | -2.0 | Agent attempted a high-risk action requiring escalation |
| HITL_REJECTED | -8.0 | Human reviewed and explicitly rejected the agent's proposal |
| PROMPT_INJECTION_DETECTED | -10.0 | Suspicious injection pattern found in agent parameters |
| BEHAVIOR_ANOMALY_SEVERE | -8.0 | Agent deviated significantly from its behavioral baseline |
| KILL_SWITCH_TRIGGERED | -20.0 | Extreme violation detected, agent isolated |

Trust degradation is the system's early warning mechanism. By the time an agent reaches the HITL tier, there is already a documented history of why its autonomy was reduced, which is exactly what a compliance audit would require.

---

## Cryptographic Audit Ledger

Standard logs can be altered. Sentinel's audit ledger cannot.

Every governance decision, whether an action was approved, denied, escalated, or blocked, is written as a structured event containing the agent identity, action type, parameters, gate-by-gate results, trust score before and after, and the final outcome. Before being appended to the ledger, Sentinel takes the SHA-256 hash of the previous entry and embeds it as a field in the current entry. It then hashes the current entry to generate the forward link.

This creates a hash chain. Altering any historical entry invalidates every hash that follows it, making tampering cryptographically detectable. The same mechanism used to verify blockchain integrity is applied here to every AI agent action that touches a financial system.

The ledger also integrates with Splunk via HTTP Event Collector. Every governance event is structured for SIEM ingestion, enabling security operations teams to run real-time queries across the full agent action history.

---

## Human in the Loop Escalation

When an action is escalated rather than auto-approved or denied, it enters the HITL queue visible on the operator dashboard. A human operator sees the complete context: the agent's identity and current trust score, the exact action being proposed, the parameters including amounts and account identifiers, the OPA policy that triggered escalation, the contextual risk score, and the agent's reasoning trace.

The operator approves or rejects. Both outcomes are logged, both carry trust signal consequences for the agent, and both are captured in the audit ledger.

---

## Technology Stack

**Frontend Dashboard**
React 18 with TypeScript, TanStack Router for navigation, Recharts for live telemetry visualization, TailwindCSS for styling, Vite as the build tool. The dashboard runs at Port 5173 and provides real-time streaming of governance telemetry, agent management, policy editing, the HITL approval queue, and the full audit log.

**Governance Backend (Safety Service)**
Python with FastAPI as the web framework. The 9-gate pipeline, trust engine, behavioral monitor, OPA policy evaluator, RAG firewall, and cryptographic audit ledger all live in this service. It runs at Port 8001.

**AI Agents**
Python with LangChain for the agentic loop and tool binding. The agents connect to Groq for fast LLM inference. The Sentinel SDK (`sentinel_sdk.py`) wraps every tool call so agents cannot bypass governance. No agent holds direct API credentials to the banking backend.

**Mock Banking API**
Python with FastAPI simulating a consumer banking backend. Handles account lookups, transaction history, fee waivers, eligibility checks, and wire transfers. Runs at Port 8000.

**Policy Engine**
Open Policy Agent with Rego policies stored as plain text files. Policies are evaluated per-request and can be updated without touching any application code.

**State and Memory**
Redis as the primary state store for trust scores, idempotency keys, behavioral baselines, kill switch state, and agent registry data. Pinecone as the vector store for RAG policy document retrieval.

---

## Project Structure

```
sentinel/
├── frontend/                    # Operator dashboard (React + Vite)
│   └── src/routes/
│       ├── index.tsx            # Home overview
│       ├── demo.tsx             # Live agent demo sandbox
│       ├── agents.tsx           # Agent fleet management
│       ├── policies.tsx         # Policy engine editor
│       ├── audit.tsx            # Cryptographic audit log viewer
│       └── hitl.tsx             # Human-in-the-loop approval queue
│
├── safety-service/              # Core governance backend (FastAPI)
│   ├── main.py                  # API entrypoint with all 9 gate implementations
│   ├── agent_registry.py        # Agent identity and lifecycle management
│   ├── trust_engine.py          # Dynamic trust scoring engine
│   ├── behavior_monitor.py      # Statistical baseline and anomaly detection
│   ├── kill_switch.py           # Emergency fleet isolation controller
│   ├── rag_firewall.py          # RAG chunk hash verification
│   ├── rag_pipeline.py          # Pinecone vector retrieval integration
│   ├── ingest_docs.py           # Trusted document ingestion and hash registration
│   ├── report_generator.py      # Compliance report generator (PDF + JSON)
│   ├── classifiers/
│   │   └── injection_detector.py  # Prompt injection scanning
│   └── policies/
│       └── trading_limits.rego    # OPA Rego governance policy
│
├── agents-fleet/                # Autonomous AI agents
│   ├── sentinel_sdk.py          # Core SDK interceptor (execute_governed_tool)
│   ├── customer_service_agent.py  # Fee waiver and account inquiry agent
│   ├── treasury_agent.py        # Intraday wire transfer agent
│   ├── llm_config.py            # Shared LLM configuration (Groq)
│   └── rag_docs/
│       ├── fee_waiver_policy.txt  # Trusted policy document
│       └── poisoned_policy.txt    # Attack scenario document (demo only)
│
├── mock-banking-api/            # Simulated banking backend (FastAPI)
│   └── main.py                  # Accounts, transactions, fee waivers, transfers
│
├── api/
│   └── schemas/                 # JSON schemas for parameter validation
│       ├── fee_waiver_schema.json
│       └── wire_transfer_schema.json
│
├── infrastructure/
│   └── redis/
│       └── redis.conf           # Redis configuration
│
├── docker-compose.yml           # Redis container orchestration
└── Docs/                        # Detailed component documentation
    ├── ARCHITECTURE.md
    ├── AGENTS.md
    ├── TRUST_AND_BEHAVIOR.md
    ├── WORKFLOW.md
    ├── REPORTING_AND_AUDIT.md
    └── DEMO_GUIDE.md
```

---

## Running the System

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Docker (for Redis)
- A Groq API key (free tier works)
- A Pinecone API key (for RAG functionality)

### Environment Setup

Create `agents-fleet/.env` with the following:

```
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_index_name
```

Create a Python virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r safety-service/requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

### Starting the System

Start Redis:

```bash
docker-compose up -d
```

Start the Mock Banking API:

```bash
venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

Start the Safety Service:

```bash
cd safety-service
..\venv\Scripts\python.exe -m uvicorn main:app --port 8001 --reload
```

Start the Frontend:

```bash
cd frontend
npm run dev
```

Register the agents (must be done after every Safety Service restart because agent registry lives in memory):

```bash
curl -X POST http://localhost:8001/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_cust_srv_01", "name": "Customer Service Agent", ...}'
```

Ingest trusted RAG documents (required before running the customer service demo):

```bash
venv\Scripts\python.exe safety-service/ingest_docs.py
```

Navigate to `http://localhost:5173` to open the operator dashboard.

---

## The Demo

The Demo Sandbox at `http://localhost:5173/demo` is the fastest way to see everything working. Four preset scenarios are available.

**$10 Fee Waiver** sends a low-risk fee waiver request through the Customer Service Agent. Sentinel verifies the agent identity, scans the prompt, retrieves and validates the trusted fee waiver policy from Pinecone, runs the OPA policy evaluation, confirms the amount is within the allowed range, and approves the action. The agent executes the waiver and responds to the user. The entire governance trace is visible in real time in the telemetry panel.

**$50,000 Transaction** sends a high-value wire transfer request through the Treasury Agent. The OPA policy evaluates the amount against the $10,000 to $100,000 threshold and returns a REQUIRE_HITL decision. The agent's autonomy is insufficient for self-approval at this value. The action is placed in the HITL queue where a human operator can review and approve or reject it.

**Malicious Prompt** sends a prompt injection attempt through the Customer Service Agent. The text contains explicit override instructions designed to bypass governance. The injection detector identifies the pattern before the agent even processes the message. Sentinel blocks the action, logs the event, and applies a trust penalty to the agent's score.

**$5,000,000 Transaction** sends a massive transfer request through the Treasury Agent. The OPA policy applies the hard block rule for amounts exceeding $100,000. The action is denied regardless of any other factor, the trust score is penalized, and the decision is recorded in the audit ledger with full cryptographic integrity.

---

## What Makes This Different

The question worth asking about any governance tool is: what does it catch that nothing else would catch?

Standard API authentication catches unauthenticated requests. Sentinel catches authenticated agents doing the wrong things.

Standard role-based access control catches requests from agents that were never given permission. Sentinel catches agents that were given permission but are now behaving in ways that suggest something has gone wrong, whether that is prompt manipulation, a software bug, or a gradual drift in model behavior.

Standard logging captures what happened. Sentinel's cryptographic ledger proves what happened in a way that cannot be tampered with after the fact.

The combination of adaptive trust scoring, real-time behavioral monitoring, policy-as-code evaluation, and cryptographic audit integrity is what moves Sentinel from a demo into the category of infrastructure that financial institutions would actually deploy.

---

## Submission Context

This project was built for the American Express Hackathon (Track 5: Open). The problem it addresses is real and growing. As AI agents take on more financial responsibility, the governance layer sitting between those agents and the systems they control becomes the most critical piece of infrastructure in the stack.

Sentinel is a working demonstration that this governance layer is buildable today, that it can operate at the speed financial systems require, and that it can provide the kind of observable, auditable, and adaptive control that regulators and risk teams will eventually require of any institution deploying autonomous financial AI.

---

*See the `Docs/` folder for detailed component documentation covering the full pipeline, trust engine, behavioral monitor, audit system, and agent architecture.*
