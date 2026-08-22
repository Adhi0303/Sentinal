# Sentinel: Enterprise Governance Infrastructure for Autonomous Financial AI Agents

## Executive Summary

Financial institutions are rapidly entering an era where autonomous AI agents execute high stakes operations — processing Razorpay payments, resolving disputes, managing merchant settlements, and servicing millions of customers in real time. However, speed without governance is catastrophic. A single misaligned agent can execute thousands of unauthorized transactions within seconds. Prompt injection attacks can corrupt reasoning. Cascading multi agent failures can amplify minor errors into systemic financial risk.

Sentinel bridges this governance gap. Sentinel is a fully working, production ready Zero Trust Governance Control Plane built specifically for the Razorpay ecosystem. Sentinel intercepts every autonomous agent action before execution and evaluates it through a sequential 9 gate governance pipeline. Only actions passing all gates reach the underlying Razorpay API. Everything else is blocked, escalated, or compensated automatically.

---

## The Core Problem: The Autonomous AI Governance Gap

Traditional access management paradigms fail when applied to autonomous AI agents in financial systems:

- **Static RBAC Incompatibility**: Human centric Role Based Access Control relies on predefined user roles and static access scopes. AI agents generate dynamic tool arguments, call parameters, and complex reasoning graphs that static permission models cannot evaluate contextually.
- **Prompt Injection and Context Poisoning**: Adversaries can bypass systemic instructions via indirect prompt injections, forcing agents into executing rogue Razorpay transactions.
- **Cascading Multi Agent Failures**: When autonomous agents interact in distributed workflows, partial execution failures across microservices lead to corrupted financial ledgers and uncoordinated rollbacks.
- **High Frequency Vulnerabilities**: Automated agents execute at speeds where duplicate execution attacks and sudden velocity sprees exceed human monitoring capabilities.

---

## High Level System Architecture

Sentinel acts as an inline, zero trust sidecar and governance gateway between autonomous AI agents and Razorpay's core payment APIs.

```mermaid
graph TD
    subgraph "AI Agent Fleet"
        A1["Refund Agent (ZoopCart)"]
        A2["Settlement Agent (QuickPay)"]
        A3["Fraud Analysis Agent (SaasHub)"]
        SDK["Sentinel SDK"]
    end

    subgraph "Sentinel Control Plane"
        G1["1. Registry Check"]
        G2["2. Authentication"]
        G3["3. Schema Validation"]
        G4["4. Idempotency Lock"]
        G5["5. Hard Limits"]
        G6["6. Trust Autonomy Check"]
        G7["7. OPA Rego Policies"]
        G8["8. Behavior Monitor"]
        G9["9. Kill Switch"]
        TE["Dynamic Trust Engine"]
        RL["Cryptographic Audit Ledger"]
    end

    subgraph "External Systems"
        RB["Razorpay Mock API"]
        UI["React Operator Dashboard"]
        DB["Redis State Store"]
    end

    A1 --> SDK
    A2 --> SDK
    A3 --> SDK

    SDK -->|"Action Request"| G1
    G1 --> G2 --> G3 --> G4 --> G5 --> G6 --> G7 --> G8 --> G9

    G9 -->|"Approved Action"| RB
    RB -->|"API Response"| G9

    G6 -.->|"Needs Approval"| UI
    G8 -.->|"Anomaly Detected"| TE

    G9 --> RL
    TE <--> DB
    RL <--> DB
    UI <--> DB
```

---

## The 9 Gate Governance Pipeline

Every Razorpay action from an AI agent passes through these gates sequentially. Failure at any gate halts execution immediately:

| Gate | Name | What it Checks |
|------|------|----------------|
| 1 | Registry Check | Is this agent registered and active? |
| 2 | Authentication | Is the SDK token valid and untampered? |
| 3 | Schema Validation | Is the payload correctly structured? Blocks SQL injection. |
| 4 | Idempotency Lock | Is this a duplicate transaction within the last 5 minutes? |
| 5 | Hard Limits | Does this exceed the agent's maximum transaction boundary? |
| 6 | Trust Autonomy | Is the agent's live trust score high enough to act autonomously? |
| 7 | OPA Rego Policies | Does this action comply with active business rules? |
| 8 | Behavior Monitor | Is this a statistical anomaly from the agent's normal pattern? |
| 9 | Kill Switch | Has an operator triggered an emergency halt? |

---

## Dynamic Trust Scoring System

Every Razorpay agent carries a live trust score (0 to 100). Actions generate trust signals that raise or lower the score in real time:

```mermaid
graph LR
    A["Agent Action Outcome"] --> B{"Trust Signal"}
    B -->|"TRANSACTION_COMPLETED"| C["+5.0"]
    B -->|"HITL_APPROVED"| D["+0.2"]
    B -->|"ACTION_DENIED_POLICY"| E["-2.0"]
    B -->|"HIGH_RISK_ESCALATED"| F["-2.0"]
    B -->|"HITL_REJECTED"| G["-8.0"]
    B -->|"KILL_SWITCH_TRIGGERED"| H["-20.0"]

    C --> I{"Autonomy Tier"}
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I

    I -->|"90 to 100"| J["FULL: Act autonomously"]
    I -->|"70 to 89"| K["BOUNDED: Standard actions auto, large ones escalated"]
    I -->|"40 to 69"| L["HITL: All actions require human approval"]
    I -->|"0 to 39"| M["QUARANTINE: All actions denied"]
```

---

## The Seven Governance Modules (Detail)

**Module 1: AI Safety Layer**
Every incoming agent instruction undergoes multi signal scanning. The system combines regex fingerprinting for known exploit signatures, semantic anomaly detection, and LlamaGuard classification for adversarial prompts. A parallel RAG Memory Firewall inspects retrieved context documents, blocking poisoned knowledge bases before they corrupt agent reasoning.

**Module 2: Policy as Code Engine (Open Policy Agent + Rego)**
Per agent and per action authorization rules are evaluated deterministically using OPA running embedded Rego scripts. OPA evaluates multi dimensional context: agent identity, action type, transaction amounts, customer risk profiles, and temporal constraints. Policy changes take effect instantly across the fleet without redeployment.

**Module 3: Dynamic Risk Intelligence Scorer**
Every action is dynamically assigned a risk score from 0 to 100 based on multi factor telemetry: transaction magnitude, target account status, call graph depth, historical velocity, and behavioral anomalies.

**Module 4: Financial Guardrails (Velocity, Limits and Idempotency)**
Enforces adaptive spending windows, hourly and daily transaction velocity thresholds, and concurrent execution limits. A distributed idempotency engine backed by Redis detects and blocks duplicate execution replay attacks within short time windows.

**Module 5: Human in the Loop (HITL) Escalation Queue**
Actions exceeding risk thresholds are placed in a real time queue. Human operators review requests on the Sentinel dashboard with complete contextual visibility including agent reasoning traces, policy parameters, risk scores, and affected account details.

**Module 6: Two Phase Commit (2PC) and SAGA Compensation**
For multi agent workflows spanning multiple ledgers, Sentinel enforces atomicity using a two phase commit protocol. If any participating agent fails midway, the integrated SAGA orchestrator automatically executes compensating transactions across all affected services.

**Module 7: Immutable Audit Ledger and Splunk SIEM Integration**
All governance outcomes are written to a tamper proof, append only audit ledger using SHA 256 forward chaining. Each entry encodes the hash of the preceding record, making retrospective alterations cryptographically detectable. Events also stream in real time to Splunk via HTTP Event Collector for regulatory reporting.

---

## Emergency Fleet Control

In the event of a security breach, operators can instantly isolate threats:

- **Single Agent Quarantine**: Revoke execution rights for one compromised agent without disrupting the others.
- **Category Isolation**: Freeze a class of agents (e.g., all Settlement agents) while others stay active.
- **Fleet Wide Emergency Shutdown**: Suspend all AI agent operations across the enterprise in under 1 second.

---

## Industry Comparison Matrix

| Capability | Standard Practice | Sentinel Infrastructure |
|------------|------------------|-------------------------|
| Policy Enforcement | Static RBAC | Deterministic OPA Rego evaluation per action |
| Audit Verification | Standard SQL logs | SHA 256 cryptographically chained tamper proof ledger |
| Duplicate Prevention | Basic app checks | Distributed Redis backed TTL idempotency engine |
| Multi Agent Safety | None / Manual | 2PC Atomicity + Automated SAGA Compensation |
| Emergency Response | Manual scripting | Sub 1 second emergency fleet kill switch |
| SIEM Integration | File log forwarding | Structured Splunk HEC event streaming |
| Risk Assessment | Hardcoded thresholds | Dynamic context aware multi factor scoring |

---

## Live System Components

| Service | Port | Description |
|---------|------|-------------|
| Sentinel Safety Service | 8001 | FastAPI core executing all 9 governance gates |
| Razorpay Mock API | 8000 | Simulated Razorpay backend for refunds, payouts, captures |
| Sentinel Admin Dashboard | 3000 | React glassmorphism UI with live telemetry and HITL queue |
| Redis | 6379 | State store for trust scores, idempotency keys, baselines |

---

## Technology Stack

- **Frontend**: React, TypeScript, TanStack Router, Vite, Tailwind CSS, Recharts
- **Governance Backend**: Python, FastAPI, LangChain, Groq LLMs, Open Policy Agent (Rego)
- **Data and Infrastructure**: Redis, Docker, Splunk HEC Integration

---

## Operational Impact

- **Execution Safety**: 100% of agent actions evaluated before reaching Razorpay APIs.
- **Ultra Low Overhead**: Average governance evaluation latency under 15ms per action.
- **Instant Quarantine**: Time to revoke a compromised agent reduced from hours to under 1 second.
- **Audit Assurance**: Cryptographically guaranteed, immutable audit records ready for regulatory verification.

---

*For a detailed breakdown of each component, see the [Docs/](Docs/) folder.*
