# System Architecture

Sentinel is a **Zero-Trust Governance Control Plane** designed to sit inline between autonomous AI agents and core financial APIs (like Razorpay). 

Instead of allowing LLM agents to call payment APIs directly, Sentinel forces all agents to route their actions through a 9-gate interception pipeline. This ensures that every action is cryptographically audited, behaviorally monitored, and policy-checked before it ever reaches the real world.

## High-Level Architecture Diagram

```mermaid
graph TD
    subgraph AI Agent Fleet
        A1[Refund Agent]
        A2[Settlement Agent]
        A3[Fraud Analysis Agent]
        SDK[Sentinel SDK]
    end

    subgraph Sentinel Control Plane (Safety Service)
        G1[1. Registry Check]
        G2[2. Authentication]
        G3[3. Schema Validation]
        G4[4. Idempotency Lock]
        G5[5. Hard Limits Check]
        G6[6. Trust Autonomy Check]
        G7[7. OPA Rego Policies]
        G8[8. Behavior Monitor]
        G9[9. Kill Switch Check]
        
        TE[Dynamic Trust Engine]
        RL[Cryptographic Audit Ledger]
    end

    subgraph External Systems
        RB[Razorpay Mock API]
        UI[React Operator Dashboard]
        DB[(Redis State Store)]
    end

    A1 --> SDK
    A2 --> SDK
    A3 --> SDK
    
    SDK -- "Action Request" --> G1
    G1 --> G2 --> G3 --> G4 --> G5 --> G6 --> G7 --> G8 --> G9
    
    G9 -- "Approved Action" --> RB
    RB -- "API Response" --> G9
    
    G6 -. "Needs Approval" .-> UI
    G7 -. "Policy Evaluation" .-> TE
    G8 -. "Anomaly Detected" .-> TE
    
    G9 -- "Final Log" --> RL
    
    TE <--> DB
    RL <--> DB
    UI <--> DB
```

## Core Components

### 1. `safety-service` (The Control Plane)
- **Tech**: FastAPI + Python
- **Role**: The core brain of Sentinel. It exposes the `/api/v1/agents/{agent_id}/action` endpoint which the SDK hits. It implements the 9-gate pipeline, runs the Trust Engine, and maintains the cryptographic ledger.
- **Port**: `8001`

### 2. `agents-fleet` (The Autonomous Actors)
- **Tech**: Python + LangChain + Groq LLMs
- **Role**: Specialized AI agents (Refunds, Settlements, Fraud) that attempt to solve user problems. They do not have direct API keys. Instead, their "tools" are wrappers around the Sentinel SDK.

### 3. `mock-banking-api` (The Financial Backend)
- **Tech**: FastAPI + Python
- **Role**: A simulated Razorpay API that processes payouts, refunds, and payment captures. It only accepts requests that have successfully passed the Sentinel pipeline.
- **Port**: `8000`

### 4. `frontend` (The Operator Dashboard)
- **Tech**: React, TanStack Router, Recharts, TailwindCSS
- **Role**: A beautiful, real-time control panel where human operators can monitor agent trust scores, view behavior deviation radar charts, approve/reject HITL (Human-in-the-Loop) escalations, and download PDF compliance reports.
- **Port**: `3000`

### 5. Redis (The State Store)
- **Role**: Powers the distributed state of the system. It holds the sliding window for behavior monitoring, idempotency cache keys, active Rego policies, and the trust scores.

## Data Flow: From Intent to Execution
1. A user asks the **Refund Agent** to refund a payment.
2. The agent uses LangChain to decide to call the `refund_payment` tool.
3. The tool calls the **Sentinel SDK**, sending the intent to the **Safety Service**.
4. The Safety Service runs the request through the **9-Gate Pipeline**.
5. If the agent's trust score is high enough and the action passes all Rego policies, Sentinel forwards the request to the **Mock Banking API**.
6. The result is returned to the agent, and the entire decision tree is hashed and saved to the **Audit Ledger**.
