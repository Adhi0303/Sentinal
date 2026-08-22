# Sentinel — Complete End-to-End Architectural Modules & Engineering Blueprint

> **System Name:** Sentinel (Zero-Trust Agent Control Plane & AgentOS for Autonomous Financial AI Fleets)  
> **Target Goal:** Industrial-grade governance infrastructure ensuring sub-15ms inline security validation, 100% deterministic safety, real-time spending controls, sub-10ms fleet isolation, and immutable auditability for autonomous financial agents.  
> **Standards Alignment:** NIST Financial Services AI Risk Management Framework (FS AI RMF), OWASP Top 10 for Agentic AI (2026), EU AI Act (Article 14 Human Oversight), SEC/FINRA Auditability Guidelines.

---

## 📌 Executive Summary & Master Modular Roadmap

To build **Sentinel** systematically from scratch to production, monitoring, and maintenance, the project is structured into **12 core modules** encompassing **36 specialized submodules**. 

```
                                SENTINEL MASTER MODULE MAP

 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 0: Shared Core Protocols, Data Schemas & Infrastructure Foundation               │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 1: Ingress Identity & Lifecycle Gateway (SPIFFE/SPIRE & Fleet State Manager)    │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 2: AI Safety, Input Sanitizer & Context Guardrail Engine (OWASP ASI01/05/06)   │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 3: Multi-Agent Coordinator & Execution Graph Analysis Engine (OWASP ASI08)      │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 4: Deterministic Policy Engine (Open Policy Agent - OPA/Rego PDP Engine)        │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 5: Dynamic Financial Guardrails & Ledger Reserve Engine (Redis Token Bucket/2PC)│
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 6: Sub-10ms Emergency Fleet Isolation & Kill-Switch System                      │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 7: Cryptographic Merkle Audit Engine & Telemetry Pipeline                       │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                        ┌────────────────────┴────────────────────┐
                        │                                         │
                        ▼                                         ▼
 ┌────────────────────────────────────────┐    ┌──────────────────────────────────────────┐
 │ MODULE 8: Agentic Client Layer & Mock  │    │ MODULE 9: Operator Command Center & UI   │
 │ Banking API Services Ecosystem         │    │ (Real-Time Dashboard & Simulation UI)    │
 └───────────────────┬────────────────────┘    └──────────────────┬───────────────────────┘
                     │                                            │
                     └────────────────────┬───────────────────────┘
                                          │
                                          ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 10: Chaos Engineering, Simulation & Verification Suite                         │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 11: Production Monitoring, Observability & Operational Maintenance              │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Detailed Breakdown of Modules & Submodules

---

### Module 0: Shared Infrastructure, Protocols & Data Foundation

**Purpose:** Establishes the core data models, serialization protocols, high-performance messaging channels, and distributed state storage required across all control plane microservices.

#### Submodule 0.1: Protocol Buffers, JSON Schemas & Common Data Contracts
* **What We Are Building:** Unified interface definition specs defining Agent Requests, Intents, Decision Responses, Execution Metrics, and Audit Envelopes.
* **Exact Functionality:**
  * Defines standard `AgentIntentPayload` (Agent ID, Action Type, Tool Name, Parameters, Context Hash, Risk Vector, Velocity Fingerprint).
  * Defines `GovernanceDecision` (Status: ALLOWED / DENIED / REQUIRE_HITL, Policy Trigger, Evaluation Latency, Risk Score, Lock Reservation Token).
  * Enforces JSON Schemas for tool parameter structures (e.g., fee waivers, wire transfers, card re-issuance).
* **Tech Stack & Libraries:** `Protobuf (v3)`, `gRPC`, `Pydantic (v2)` (Python), `Go Protoc Compiler`.

#### Submodule 0.2: Distributed In-Memory State Infrastructure
* **What We Are Building:** Ultra-fast Redis Cluster setup configured for atomic lua script executions, sub-millisecond key-value tracking, sliding window counters, and distributed locking.
* **Exact Functionality:**
  * Stores agent status flags (`ACTIVE`, `COOLDOWN`, `QUARANTINED`).
  * Manages sliding window spend caps per agent across time buckets (1s, 1m, 1h, 24h).
  * Executes atomic Redlock algorithms for TOCTOU multi-agent concurrency.
* **Tech Stack & Libraries:** `Redis 7.2 Cluster`, `go-redis/v9` (Go), `redis-py / redis.asyncio` (Python).

#### Submodule 0.3: High-Throughput Event Streaming Bus
* **What We Are Building:** Decoupled, asynchronous event pipeline for broadcasting telemetry, security alerts, and audit streams without impacting inline decision latency (<15ms SLA).
* **Exact Functionality:**
  * NATS JetStream topics: `sentinel.telemetry.v1`, `sentinel.security.alerts`, `sentinel.audit.merkle`, `sentinel.killswitch.broadcast`.
  * Guarantees at-least-once delivery with low resource consumption.
* **Tech Stack & Libraries:** `NATS Server (JetStream enabled)`, `nats.go` (Go client), `nats-py` (Python client).

#### Submodule 0.4: Immutable Ledger & Primary Database Store
* **What We Are Building:** Database persistence layer for policy store, historical agent analytics, human approval queues, and cryptographic Merkle tree root hashes.
* **Exact Functionality:**
  * Stores historical decision records with indexed querying.
  * Maintains Merkle tree leaves and node hashes in append-only tables with row-level integrity constraints.
* **Tech Stack & Libraries:** `PostgreSQL 16`, `SQLAlchemy 2.0` (Async), `pgx` (Go driver), `Liquibase/Flyway` (Migrations).

---

### Module 1: Ingress Identity & Lifecycle Gateway

**Purpose:** First line of defense. Validates machine identity, verifies agent lifecycle state, and maintains dynamic trust/reputation metrics for every incoming agent tool request.

#### Submodule 1.1: SPIFFE/SPIRE Machine Identity Authenticator
* **What We Are Building:** Zero-trust cryptographically verifiable identity validator for AI agents using SPIFFE Verifiable Identity Documents (SVIDs).
* **Exact Functionality:**
  * Extracts short-lived X.509 SVID or JWT SVID from incoming gRPC/mTLS headers.
  * Validates agent identity URI (`spiffe://amex.com/agent/servicing-dispute-01`).
  * Rejects unauthenticated or expired agent calls in `<2ms`.
* **Tech Stack & Libraries:** `SPIFFE/SPIRE Workload API`, `go-spiffe/v2`, `PyJWT`, `cryptography`.

#### Submodule 1.2: Agent Fleet Lifecycle & Quarantine Controller
* **What We Are Building:** State machine managing operational modes of all registered agents in the fleet.
* **Exact Functionality:**
  * Operational States: `ACTIVE`, `COOLDOWN` (temporary rate limit breach), `FROZEN` (manual operator pause), `QUARANTINED` (security violation breach).
  * Blocks any requests originating from non-ACTIVE agents instantaneously.
* **Tech Stack & Libraries:** `Go` (State Machine), `Redis Cluster` (Distributed state synchronization).

#### Submodule 1.3: Dynamic Agent Reputation & Trust Scoring Engine
* **What We Are Building:** Real-time scoring algorithm computing an agent trust score (0 – 1000) based on execution history.
* **Exact Functionality:**
  * Increases score for compliant operations over time.
  * Decreases score rapidly on policy warnings, schema validation errors, or high risk scores.
  * Automatically downgrades high-risk tool permissions if trust score drops below threshold (e.g. < 600).
* **Tech Stack & Libraries:** `Python / Go`, `Exponential Moving Average (EMA)` algorithms.

---

### Module 2: AI Safety, Input Sanitizer & Context Guardrail Engine

**Purpose:** Protects the control plane and core downstream APIs against prompt injection, malicious context manipulation, and parameter schema violations.

#### Submodule 2.1: Indirect Prompt Injection & Goal Hijacking Detector (OWASP ASI01)
* **What We Are Building:** Pre-execution prompt firewall inspecting unstructured inputs (customer emails, uploaded PDFs, RAG context) contained within tool arguments.
* **Exact Functionality:**
  * Scans parameter text for hidden injection signatures, override commands ("Ignore previous instructions", "System override"), and invisible unicode exploits.
  * Strips malicious payload fragments or flags request for immediate rejection.
* **Tech Stack & Libraries:** `FastAPI` (Python), `Regex / Pattern Matcher Engine`, `Llama-Guard / DeBERTa-v3 Injection Classifier`.

#### Submodule 2.2: Tool Selection & Parameter Boundary Validator (OWASP ASI05)
* **What We Are Building:** Strict JSON-Schema parameter boundary enforcer ensuring agents do not execute arbitrary code or pass out-of-range arguments.
* **Exact Functionality:**
  * Validates tool call parameters against registered JSON schemas (e.g. `amount` must be float > 0, `account_id` must match regex `^ACCT-[0-9]{8}$`).
  * Prevents SQL injection strings, shell command injection, or parameter type pollution.
* **Tech Stack & Libraries:** `jsonschema` (Python/Go), `FastAPI Pydantic validation`.

#### Submodule 2.3: Context Poisoning & Vector RAG Memory Firewall (OWASP ASI06)
* **What We Are Building:** Memory integrity inspector for agents leveraging Retrieval-Augmented Generation (RAG).
* **Exact Functionality:**
  * Computes cryptographic hashes of RAG context snippets passed alongside tool intents.
  * Detects malicious vector memory alterations or poisoned context strings prior to execution.
* **Tech Stack & Libraries:** `SHA-256 Hashing`, `Python Vector Guard Helper`.

---

### Module 3: Multi-Agent Coordinator & Execution Graph Analysis Engine

**Purpose:** Prevents cascading inter-agent feedback loops, deadlocks, and multi-agent salami slicing by analyzing execution dependency graphs in real-time.

#### Submodule 3.1: Distributed Execution Graph Tracker (OWASP ASI08)
* **What We Are Building:** Graph-based context tracer tracking multi-agent tool execution stacks across agent chains.
* **Exact Functionality:**
  * Tracks parent-child call chains using distributed trace headers (`Trace-ID`, `Span-ID`, `Parent-Agent-ID`).
  * Measures call-stack depth (e.g., max allowed depth = 4 levels).
* **Tech Stack & Libraries:** `OpenTelemetry Go/Python SDK`, `Redis Graph / In-Memory NetworkX Graph`.

#### Submodule 3.2: Circular Dependency & Infinite Loop Breaker
* **What We Are Building:** Real-time cycle detector identifying recursive inter-agent call loops.
* **Exact Functionality:**
  * Detects loops like: *Dispute Agent* -> *Treasury Agent* -> *Overdraft Agent* -> *Dispute Agent*.
  * Immediately breaks loop execution, halts sub-chain, and issues security alert.
* **Tech Stack & Libraries:** `Tarjan's / Tarjan-DFS Cycle Detection Algorithm` (Go/Python).

#### Submodule 3.3: Contextual Multi-Agent Risk Scoring Engine
* **What We Are Building:** Dynamic risk evaluation module scoring every transaction intent from 0 (Safe) to 100 (Critical Risk).
* **Exact Functionality:**
  * Computes risk dynamically based on: Amount, Agent Reputation, Time of Day, Target Account Vulnerability, and Call-Stack Depth.
  * Feeds risk score directly into the Policy Engine for path determination (Allow vs HITL).
* **Tech Stack & Libraries:** `Go` (In-memory Risk Scoring Rules Engine).

---

### Module 4: Deterministic Policy Engine (OPA / Rego PDP)

**Purpose:** Decouples non-deterministic LLM reasoning from actual API execution using a compiled, fine-grained Policy Decision Point (PDP).

#### Submodule 4.1: Open Policy Agent (OPA) Embedded Evaluator
* **What We Are Building:** High-performance, sub-5ms policy decision engine embedded directly inside the Control Plane Gateway.
* **Exact Functionality:**
  * Evaluates structured JSON intent against compiled Rego policy bundles.
  * Guarantees 100% deterministic outputs (`ALLOW`, `DENY`, `REQUIRE_HITL`).
* **Tech Stack & Libraries:** `Open Policy Agent (OPA)`, `OPA Wasm / Go Native SDK (github.com/open-policy-agent/opa/rego)`.

#### Submodule 4.2: Rego Policy Repository & Policy-as-Code Manager
* **What We Are Building:** Declarative repository containing enterprise policy rules for financial agent domains.
* **Exact Functionality:**
  * Domain Rules:
    * `servicing_disputes.rego`: Max provisional credit $100; max fee waiver $50/day.
    * `treasury_liquidity.rego`: Rebalancing allowed only during market hours; max sweep $50,000.
    * `commercial_credit.rego`: Credit limit increases > $5,000 require manual human approval.
  * Supports policy versioning and hot-reloading without service restarts.
* **Tech Stack & Libraries:** `Rego DSL`, `OPA CLI`, `Git Version Control`.

#### Submodule 4.3: ABAC/RBAC Granular Scoping & Human-in-the-Loop (HITL) Gatekeeper
* **What We Are Building:** Access control enforcer and escalation routing manager for risky transactions.
* **Exact Functionality:**
  * Validates agent role scopes (Attribute-Based & Role-Based Access Control).
  * If policy returns `REQUIRE_HITL`, intercepts action, pauses execution, generates human-readable risk breakdown, and routes to Operator Dashboard Queue.
* **Tech Stack & Libraries:** `Go` (Escalation Router), `PostgreSQL` (HITL Pending Queue).

---

### Module 5: Dynamic Financial Guardrails & Ledger Reserve Engine

**Purpose:** Implements real-time financial velocity limiters, idempotency checks, and atomic two-phase commit ledger reservations.

#### Submodule 5.1: Redis Sliding-Window Multi-Tier Spend Limiter (OWASP ASI02)
* **What We Are Building:** Multi-tiered sliding-window token bucket budget tracker protecting against salami-slicing micro-transactions.
* **Exact Functionality:**
  * Enforces dynamic spend caps across multiple time windows: Per-Second, Per-Minute, Per-Hour, Per-24-Hours.
  * Example: Agent capped at $50/txn, $200/min, $1,000/day. Blocks $1 micro-transaction attacks instantly when velocity cap is reached.
* **Tech Stack & Libraries:** `Redis Lua Scripts` (Atomic sliding-window counters), `go-redis`.

#### Submodule 5.2: Idempotency & Duplicate Execution Preventer
* **What We Are Building:** Request deduplication service preventing agents from executing duplicate charges/refunds due to API retries or network drops.
* **Exact Functionality:**
  * Generates unique idempotency hash from `(Agent_ID, Action, Account_ID, Amount, Timestamp_Window)`.
  * Locks key in Redis for TTL window (e.g., 300s). Rejects duplicate incoming payloads with cached prior response.
* **Tech Stack & Libraries:** `Redis SETNX with TTL`, `Go Hashing (crypto/sha256)`.

#### Submodule 5.3: Two-Phase Commit (2PC) Ledger Reserve Locking Engine
* **What We Are Building:** Concurrency and TOCTOU (Time-of-Check to Time-of-Use) race condition prevention engine.
* **Exact Functionality:**
  * **Phase 1 (Prepare & Reserve):** Sentinel locks requested fund amount in Core Ledger reservation buffer.
  * **Phase 2 (Commit or Abort):** Once policy check succeeds, commits transaction; if policy or downstream fails, automatically releases reservation lock.
* **Tech Stack & Libraries:** `Redlock Distributed Lock Algorithm`, `PostgreSQL / Redis 2PC Transaction Manager`.

---

### Module 6: Sub-10ms Emergency Fleet Isolation & Kill-Switch System

**Purpose:** Provides instant fleet-wide or single-agent emergency shutdown capabilities during active security breaches or anomalous market events.

#### Submodule 6.1: Real-Time Emergency Pub/Sub Broadcast Network
* **What We Are Building:** Ultra-low latency pub/sub channel for kill-switch signal propagation across distributed gateway nodes.
* **Exact Functionality:**
  * Listens for `KILL_AGENT(agent_id)` or `KILL_FLEET_ALL()` signals.
  * Achieves propagation latency `< 5ms` across all control plane nodes.
* **Tech Stack & Libraries:** `NATS JetStream System Channel` / `Redis PubSub`, `WebSockets`.

#### Submodule 6.2: Fleet Token Revocation & Quarantine Controller
* **What We Are Building:** Instant credential invalidation worker.
* **Exact Functionality:**
  * Revokes active SPIFFE/JWT authorization tokens immediately upon kill signal.
  * Updates agent state in Redis to `QUARANTINED`.
  * Rejects all subsequent API invocations at Stage 1.
* **Tech Stack & Libraries:** `Go Token Blacklist Cache`, `SPIRE Agent Quarantine API`.

#### Submodule 6.3: In-Flight Transaction Rollback & Compensation Worker
* **What We Are Building:** Automatic transaction compensation engine handling interrupted multi-step workflows.
* **Exact Functionality:**
  * Intercepts in-flight transactions affected by emergency isolation.
  * Triggers compensation APIs (e.g. release balance lock, reverse partial card block) ensuring clean state.
* **Tech Stack & Libraries:** `Saga Pattern / Compensation Handler` (Go/Python).

---

### Module 7: Cryptographic Merkle Audit Engine & Telemetry Pipeline

**Purpose:** Generates tamper-proof, 100% reproducible audit logs for regulatory compliance (NIST, SEC, FINRA, EU AI Act).

#### Submodule 7.1: Immutable Merkle Tree Decision Logger
* **What We Are Building:** Cryptographic hash-tree audit log generator.
* **Exact Functionality:**
  * Hashes every agent decision: `SHA256(Agent_ID + Intent + Policy_Result + Risk_Score + Timestamp + Previous_Hash)`.
  * Chains decisions into an append-only Merkle Tree.
  * Computes periodic Merkle Root Hashes for immutable storage verification.
* **Tech Stack & Libraries:** `Merkle Tree Algorithm` (Go/Python), `PostgreSQL Append-Only Tables`.

#### Submodule 7.2: Structured Telemetry & Prometheus Metric Exporter
* **What We Are Building:** Real-time operational metrics exporter tracking control plane performance and security SLAs.
* **Exact Functionality:**
  * Metrics: `sentinel_decisions_total{status="allowed|denied"}`, `sentinel_latency_seconds_bucket`, `sentinel_spend_current_dollars`, `sentinel_killswitch_events`.
  * Exposes standard `/metrics` endpoint for Prometheus scraping.
* **Tech Stack & Libraries:** `prometheus/client_golang` (Go), `prometheus-fastapi-instrumentator` (Python).

#### Submodule 7.3: Regulatory Explainability & Audit Trail Exporter
* **What We Are Building:** Human-readable audit report generator for compliance auditors.
* **Exact Functionality:**
  * Translates raw decision trees and Rego evaluations into clear audit explanations (e.g., *"Transaction $12,000 DENIED because it exceeded Tier 2 single-txn limit ($10,000) and required Human Approval"*).
  * Exports formatted PDF/JSON audit packages.
* **Tech Stack & Libraries:** `Python ReportLab` (PDF generation), `JSON-LD Compliance Exporter`.

---

### Module 8: Agentic Client Layer & Mock Financial Banking API Ecosystem

**Purpose:** Provides a realistic simulation environment consisting of 4 autonomous AI agents and mock Core Banking APIs to demonstrate real-world governance.

#### Submodule 8.1: Mock Core Banking & Ledger API Engine
* **What We Are Building:** High-performance mock financial backend simulating core banking systems.
* **Exact Functionality:**
  * Endpoints:
    * `/api/v1/ledger/accounts/{id}/balance` (Read balance)
    * `/api/v1/ledger/transfers/wire` (Execute wire transfer)
    * `/api/v1/cards/fee-waiver` (Issue fee credit)
    * `/api/v1/credit/limit-increase` (Adjust credit limit)
  * Implements 2PC balance locking header validation.
* **Tech Stack & Libraries:** `FastAPI` (Python 3.12) / `Go Gin framework`, `PostgreSQL`.

#### Submodule 8.2: Enterprise Autonomous Financial AI Agents Fleet
* **What We Are Building:** 4 specialized AI agents executing multi-step operational tasks:
  1. **Customer Servicing & Dispute Agent:** Handles chargebacks, fee waiver requests, provisional credit.
  2. **Treasury & Liquidity Agent:** Monitors corporate cash flow, performs intra-day sweeps and FX hedging.
  3. **Commercial Credit Underwriting Agent:** Analyzes financial statements and adjusts revolving credit limits.
  4. **Procurement & Payables Agent:** Parses vendor invoices and executes B2B wire transfers.
* **Tech Stack & Libraries:** `LangChain / LangGraph` or `CrewAI` / `OpenAI / Anthropic APIs`, `Python 3.12`.

#### Submodule 8.3: Sentinel SDK Client & Gateway Proxy Interceptor
* **What We Are Building:** Lightweight client SDK wrapping agent tool calls with Sentinel governance headers.
* **Exact Functionality:**
  * Automatically injects SPIFFE identity tokens, trace context, and idempotency keys into outgoing tool requests.
  * Intercepts tool calls before network transmission and routes through Sentinel Control Plane Gateway.
* **Tech Stack & Libraries:** `Python / Go SDK library` (`sentinel-agent-sdk`).

---

### Module 9: Operator Command Center & Security Dashboard (UI)

**Purpose:** Provides human risk officers and security administrators with real-time fleet visibility, interactive kill-switches, policy editors, and audit explorers.

#### Submodule 9.1: Real-Time Agent Fleet Map & Telemetry Dashboard
* **What We Are Building:** High-impact, visually stunning UI dashboard providing live monitoring of active AI agents.
* **Exact Functionality:**
  * Displays active agent nodes, current status (`ACTIVE`, `COOLDOWN`, `QUARANTINED`), live throughput (req/sec), latency metrics (<15ms budget gauge), and risk heatmaps.
  * Live streaming updates via WebSocket.
* **Tech Stack & Libraries:** `React 18`, `TypeScript`, `TailwindCSS`, `Lucide Icons`, `Recharts / Tremor`, `WebSockets`.

#### Submodule 9.2: Red-Button Emergency Fleet Kill-Switch Interface
* **What We Are Building:** Prominent emergency circuit breaker panel on the dashboard.
* **Exact Functionality:**
  * Features a two-step confirmation Modal: "HALT FLEET IMMEDIATELY" or "QUARANTINE SPECIFIC AGENT".
  * Triggers immediate sub-10ms broadcast across backend control plane upon activation.
* **Tech Stack & Libraries:** `React Modal / State Management`, `WebSocket Kill Trigger API`.

#### Submodule 9.3: Policy-as-Code Visual Editor & "What-If" Simulation Sandbox
* **What We Are Building:** Interactive Rego policy manager and digital twin simulator.
* **Exact Functionality:**
  * Allows compliance officers to edit Rego policies directly in browser.
  * "What-If" Simulator: Replays historical agent requests against modified policy rules to visualize approval/rejection rates before deploying to production.
* **Tech Stack & Libraries:** `@monaco-editor/react` (Rego code editor), `React Query`.

#### Submodule 9.4: Cryptographic Merkle Audit Explorer & HITL Approval Queue
* **What We Are Building:** Dual-purpose panel for audit verification and human review.
* **Exact Functionality:**
  * **HITL Queue:** Displays pending Tier 3 high-risk transactions requiring human operator click approval (APPROVE / REJECT).
  * **Merkle Explorer:** Interactive visual tree viewer verifying cryptographic hashes of decision records.
* **Tech Stack & Libraries:** `React Flow / D3.js` (Merkle Tree & Decision Graph Visualization).

---

### Module 10: Chaos Engineering, Simulation & Verification Suite

**Purpose:** Validates Sentinel’s resilience under adversarial attacks, prompt injection storms, velocity breaches, model drift, and heavy load.

#### Submodule 10.1: Adversarial Chaos Attack Generator
* **What We Are Building:** Automated test harness executing chaos attacks against the control plane.
* **Exact Functionality:**
  * Attacks Executed:
    1. **Prompt Injection Storm:** Injecting adversarial prompt overrides inside invoice PDFs.
    2. **Velocity Salami Slicing:** Firing 10,000 $1 micro-transactions in under 5 seconds.
    3. **Circular Feedback Loop:** Triggering inter-agent recursive call loops.
  * Verifies 100% block rate by Sentinel.
* **Tech Stack & Libraries:** `Python pytest`, `Locust`, `Asyncio HTTP runner`.

#### Submodule 10.2: Model Behavior Diffing & LLM Drift Simulator
* **What We Are Building:** Benchmarking tool comparing agent behavior across model upgrades (e.g. GPT-4 vs GPT-5 / Claude 3.5).
* **Exact Functionality:**
  * Evaluates how model updates affect intent parameter generation and policy violation frequency.
* **Tech Stack & Libraries:** `Python Evaluation Harness`, `Pandas / NumPy`.

#### Submodule 10.3: High-Throughput SLA Load Tester
* **What We Are Building:** Load testing script verifying performance SLAs under heavy traffic.
* **Exact Functionality:**
  * Simulates 25,000 req/sec concurrent traffic load across Go Gateway nodes.
  * Measures 95th and 99th percentile latency to guarantee `<15ms` inline overhead.
* **Tech Stack & Libraries:** `k6` (Grafana k6 load tester in Go/JS), `Locust`.

---

### Module 11: Production Monitoring, Observability & Operational Maintenance

**Purpose:** Comprehensive production stack monitoring, alert routing, logging, and deployment automation.

#### Submodule 11.1: Prometheus & Grafana Monitoring Dashboard Setup
* **What We Are Building:** Production observability infrastructure.
* **Exact Functionality:**
  * Pre-configured Grafana Dashboards displaying Gateway Latency P99, Policy Engine Evaluation Latency, Redis Memory Usage, NATS Queue Depth, and Active Agent Count.
  * Configures Prometheus alert rules for SLA breaches (>15ms latency or >5% policy violation spike).
* **Tech Stack & Libraries:** `Prometheus 2.50`, `Grafana 10`, `Alertmanager`.

#### Submodule 11.2: Centralized Logging & SIEM Export Engine
* **What We Are Building:** Structured JSON logger forwarding security events to enterprise SIEM platforms.
* **Exact Functionality:**
  * Formats security alerts into CEF / Syslog / OpenTelemetry Log format.
  * Routes security alerts (e.g. Prompt Injection Detected, Fleet Quarantine Triggered) to security operations center (SOC).
* **Tech Stack & Libraries:** `Zap Logger` (Go) / `structlog` (Python), `Vector / FluentBit`.

#### Submodule 11.3: Containerized Orchestration & Maintenance Pipeline
* **What We Are Building:** Docker Compose & Kubernetes deployment configuration for one-click setup.
* **Exact Functionality:**
  * `docker-compose.yml` deploying: Go Control Gateway, Python Safety Service, OPA PDP, Redis Cluster, NATS JetStream, PostgreSQL, React Dashboard, Prometheus, Grafana.
  * Health check endpoints (`/healthz`, `/readyz`) for automated container recovery.
* **Tech Stack & Libraries:** `Docker`, `Docker Compose (v2)`, `Kubernetes Helm Charts` (optional production manifest).

---

## 📋 Comprehensive Tech Stack & Library Reference Matrix

| Module | Core Responsibility | Technologies, Libraries & Frameworks Used |
| :--- | :--- | :--- |
| **Module 0** | Shared Protocols & Infra | `Go 1.22+`, `Python 3.12+`, `gRPC / Protobuf`, `Redis 7.2 Cluster`, `NATS JetStream`, `PostgreSQL 16` |
| **Module 1** | Identity & Lifecycle | `SPIFFE / SPIRE Workload API`, `go-spiffe/v2`, `PyJWT`, `Redis State Store` |
| **Module 2** | AI Safety & Sanitizer | `FastAPI`, `Pydantic v2`, `Llama-Guard / Injection Classifier`, `jsonschema` |
| **Module 3** | Multi-Agent Coordinator | `OpenTelemetry SDK`, `Tarjan Cycle Algorithm`, `Redis Graph / NetworkX` |
| **Module 4** | Deterministic OPA PDP | `Open Policy Agent (OPA)`, `Rego DSL`, `OPA Wasm / Go Native SDK` |
| **Module 5** | Financial Guardrails | `Redis Lua Scripts (Sliding-Window Token Bucket)`, `Redlock 2PC Manager`, `crypto/sha256` |
| **Module 6** | Emergency Kill-Switch | `NATS JetStream System Channel`, `Redis PubSub`, `Go Token Blacklist Cache` |
| **Module 7** | Merkle Audit & Telemetry | `Merkle Tree Cryptographic Hash Engine`, `Prometheus Go Client`, `PostgreSQL Append-Only Tables` |
| **Module 8** | Agents & Mock Financial APIs | `FastAPI / Go Gin`, `LangChain / LangGraph / CrewAI`, `OpenAI / Anthropic APIs`, `Sentinel SDK` |
| **Module 9** | Operator Dashboard UI | `React 18`, `TypeScript`, `TailwindCSS`, `Lucide Icons`, `Recharts`, `@monaco-editor/react`, `WebSockets` |
| **Module 10** | Chaos & SLA Testing | `Python pytest`, `Grafana k6`, `Locust`, `Pandas` |
| **Module 11** | Production & Maintenance | `Prometheus`, `Grafana`, `Docker / Docker Compose`, `Zap Logger`, `Vector` |

---

## 🚀 Step-by-Step Execution Plan

Now that all **12 Modules** and **36 Submodules** are defined with exact responsibilities and tech stacks, we will build the project in **6 logical phases**:

1. **Phase 1 (Foundations):** Implement **Module 0** (Schemas, Protocols, Redis, NATS, Postgres) and **Module 8.1** (Mock Core Banking APIs).
2. **Phase 2 (Control Plane Gateway & Safety):** Implement **Module 1** (Identity), **Module 2** (AI Safety/Sanitizer), and **Module 4** (OPA Rego PDP Engine).
3. **Phase 3 (Financial Guardrails & Multi-Agent Coordinator):** Implement **Module 3** (Graph Coordinator/Loop Breaker) and **Module 5** (Redis Spend Caps & 2PC Locks).
4. **Phase 4 (Emergency Isolation & Audit):** Implement **Module 6** (Sub-10ms Kill-Switch) and **Module 7** (Cryptographic Merkle Audit Engine).
5. **Phase 5 (AI Agents & Dashboard UI):** Build **Module 8.2/8.3** (Autonomous Agents & SDK) and **Module 9** (React Operator Dashboard).
6. **Phase 6 (Chaos Verification & Observability):** Execute **Module 10** (Chaos/Load Testing) and **Module 11** (Prometheus/Grafana Observability Stack).

---
*Sentinel Modules Blueprint generated for American Express Autonomous AI Governance Architecture.*


---

### 📂 Master Project Directory Tree

```
d:\Projects\american express hackthon/
├── README.md                           # Executive Overview & Hackathon Presentation
├── ProjectDescription.md               # Formatted submission text for hackathon portal
├── modules.md                          # Master 12-Module Architectural Breakdown
├── PROJECT_STRUCTURE.md                # Project File Schema & Folder Mapping
├── docker-compose.yml                  # One-click multi-container stack orchestration
├── Makefile                            # Developer shortcuts for build, test, and run
│
├── api/                                # Module 0.1: Protocols & API Schemas
│   ├── proto/                          # Protocol Buffers definitions (.proto)
│   │   ├── agent_intent.proto          # Agent Intent Payload specs
│   │   ├── governance_decision.proto   # PDP Decision Output specs
│   │   └── audit_telemetry.proto       # Telemetry Event Stream specs
│   └── schemas/                        # JSON Schemas for Parameter Boundaries
│       ├── fee_waiver_schema.json
│       ├── wire_transfer_schema.json
│       └── credit_limit_schema.json
│
├── control-plane/                      # Core Sentinel Zero-Trust Gateway (Go / Python)
│   ├── cmd/
│   │   └── gateway/
│   │       └── main.go                 # Control Plane Gateway Entrypoint
│   ├── pkg/
│   │   ├── identity/                   # Module 1: SPIFFE/SPIRE & Reputation Scorer
│   │   │   ├── spiffe_validator.go     # X.509 / JWT SVID Machine Auth
│   │   │   ├── state_manager.go        # ACTIVE, COOLDOWN, QUARANTINED State Machine
│   │   │   └── reputation_scorer.go    # 0-1000 Dynamic Agent Trust Score
│   │   ├── sanitizer/                  # Module 2: AI Safety & Sanitizer
│   │   │   ├── prompt_firewall.go      # Indirect Prompt Injection Detector (ASI01)
│   │   │   ├── schema_validator.go     # Parameter JSON Schema Validator (ASI05)
│   │   │   └── rag_guard.go            # Vector Context Hashing Guard (ASI06)
│   │   ├── coordinator/                # Module 3: Inter-Agent Graph & Loop Breaker
│   │   │   ├── graph_tracker.go        # Distributed Execution Graph Tracker
│   │   │   ├── cycle_detector.go       # Tarjan Circular Dependency Detector (ASI08)
│   │   │   └── risk_scorer.go          # Contextual Risk Engine (0-100 Score)
│   │   ├── pdp/                        # Module 4: Open Policy Agent Engine
│   │   │   ├── opa_evaluator.go        # Embedded OPA Rego PDP Evaluator (<5ms)
│   │   │   └── hitl_router.go          # Escalation Manager for Tier 3 Actions
│   │   ├── guardrails/                 # Module 5: Spend Limiters & Ledger Locks
│   │   │   ├── token_bucket.go         # Redis Multi-Tier Sliding-Window Limiter (ASI02)
│   │   │   ├── lua_scripts.go          # Atomic Redis Lua Spend Limit Scripts
│   │   │   ├── idempotency.go          # Duplicate Execution Deduplicator
│   │   │   └── redlock_2pc.go          # Two-Phase Commit Ledger Reserve Locker
│   │   ├── killswitch/                 # Module 6: Sub-10ms Emergency Isolation
│   │   │   ├── broadcast_listener.go   # Low-latency NATS/Redis Killsignal Listener
│   │   │   ├── token_revoker.go        # Instant SPIFFE Token Blacklist Worker
│   │   │   └── rollback_handler.go     # In-flight Transaction Rollback Handler
│   │   └── audit/                      # Module 7: Merkle Audit & Telemetry
│   │       ├── merkle_tree.go          # Append-Only Merkle Tree Hashing Engine
│   │       └── prometheus_exporter.go  # Prometheus SLA Metrics Collector
│   └── config/
│       └── gateway_config.yaml         # Control Plane Configuration settings
│
├── policies/                           # Module 4.2: Rego Policy-as-Code Rules
│   ├── main.rego                       # Core Governance Policy Gateway Rule
│   ├── servicing_disputes.rego         # Fee Waiver & Provisional Credit Rules
│   ├── treasury_liquidity.rego         # Sweep & FX Hedging Rules
│   ├── commercial_credit.rego          # Credit Limit Adjustment Rules
│   └── procurement_payables.rego       # Vendor Wire Transfer Rules
│
├── agents-fleet/                       # Module 8.2 & 8.3: Autonomous AI Agents & SDK
│   ├── sdk/                            # Sentinel Client SDK / Proxy Interceptor
│   │   ├── sentinel_sdk.py             # Python Agent SDK wrapper
│   │   └── interceptor.go              # Go Agent gRPC Interceptor
│   ├── agents/                         # 4 Enterprise AI Agents
│   │   ├── servicing_agent.py          # Dispute & Fee Waiver Agent
│   │   ├── treasury_agent.py           # Cash Flow & Liquidity Agent
│   │   ├── credit_agent.py             # Underwriting Agent
│   │   └── procurement_agent.py        # Vendor Payables Agent
│   └── run_fleet.py                    # Multi-agent orchestrator script
│
├── mock-banking-api/                   # Module 8.1: Mock Core Banking Backend APIs
│   ├── main.py                         # FastAPI Core Banking Entrypoint
│   ├── routes/
│   │   ├── accounts.py                 # Balance & Account Info API
│   │   ├── cards.py                    # Fee Waiver & Card Re-issuance API
│   │   ├── transfers.py                # Wire Transfer & Ledger Lock API
│   │   └── credit.py                   # Credit Limit API
│   └── database/
│       ├── models.py                   # Banking Data Models
│       └── ledger_lock.py              # 2PC Balance Locking Engine
│
├── dashboard/                          # Module 9: React Operator Command Center UI
│   ├── package.json                    # Dependencies (React 18, Tailwind, Lucide, Monaco)
│   ├── vite.config.ts                  # Vite build bundler config
│   ├── tailwind.config.js              # Tailwind styling config
│   ├── src/
│   │   ├── components/
│   │   │   ├── FleetMap.tsx            # Live Agent Network Diagram & Status Cards
│   │   │   ├── RiskHeatmap.tsx         # Live Risk Matrix & Velocity Gauge
│   │   │   ├── RedButtonKillSwitch.tsx # Sub-10ms Emergency Fleet Isolation UI
│   │   │   ├── PolicyEditor.tsx        # Monaco Rego Code Editor & Simulation Sandbox
│   │   │   ├── MerkleExplorer.tsx      # Visual Cryptographic Audit Tree Explorer
│   │   │   └── HITLApprovalQueue.tsx   # Human-in-the-Loop Tier 3 Action Approval Queue
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts         # Real-time WebSocket connection to NATS/Gateway
│   │   ├── pages/
│   │   │   ├── FleetOverview.tsx       # Main Operator Telemetry Dashboard
│   │   │   ├── PolicyManager.tsx       # Policy-as-Code Editor Page
│   │   │   ├── AuditLogs.tsx           # Cryptographic Merkle Explorer Page
│   │   │   └── Simulation.tsx          # "What-If" Simulation & Attack Replay Page
│   │   ├── App.tsx                     # React Router Navigation
│   │   └── main.tsx                    # Application Entrypoint
│   └── public/
│
├── chaos-testing/                      # Module 10: Chaos Engineering & SLA Load Tests
│   ├── attacks/
│   │   ├── prompt_injection_storm.py   # Simulates OWASP ASI01 prompt attacks
│   │   ├── velocity_salami_attack.py   # Simulates OWASP ASI02 micro-transaction storms
│   │   └── circular_loop_attack.py     # Simulates OWASP ASI08 cascading agent loops
│   ├── load-test/
│   │   ├── k6_sla_test.js              # 25,000 req/sec k6 latency load generator
│   │   └── locustfile.py               # Locust Python load tester
│   └── model-drift/
│       └── model_behavior_diff.py      # GPT-4 vs GPT-5 model drift benchmarking
│
└── infrastructure/                     # Module 11: Production Monitoring & Maintenance
    ├── docker/
    │   ├── Dockerfile.gateway          # Control Plane Gateway Dockerfile
    │   ├── Dockerfile.dashboard        # React Dashboard Dockerfile
    │   ├── Dockerfile.agents           # AI Agents Fleet Dockerfile
    │   └── Dockerfile.banking_api      # Mock Banking API Dockerfile
    ├── prometheus/
    │   ├── prometheus.yml              # Prometheus scraper config
    │   └── alerts.yml                  # SLA breach & killswitch alert rules
    ├── grafana/
    │   ├── dashboards/
    │   │   ├── gateway_latency.json    # Latency & SLA Grafana Dashboard
    │   │   └── risk_analytics.json     # Risk Score & Violation Grafana Dashboard
    │   └── provisioning/
    ├── redis/
    │   └── redis.conf                  # Redis Cluster tuning config
    └── nats/
        └── nats-server.conf            # NATS JetStream server config
```

---

### 📌 Module-to-Folder Quick Reference

| Module Name | Directory Location |
| :--- | :--- |
| **Module 0: Shared Infrastructure** | `/api`, `/infrastructure` |
| **Module 1: Ingress Identity** | `/control-plane/pkg/identity` |
| **Module 2: AI Safety & Sanitizer** | `/control-plane/pkg/sanitizer` |
| **Module 3: Multi-Agent Coordinator** | `/control-plane/pkg/coordinator` |
| **Module 4: OPA Policy Engine** | `/control-plane/pkg/pdp`, `/policies` |
| **Module 5: Financial Guardrails** | `/control-plane/pkg/guardrails` |
| **Module 6: Emergency Isolation** | `/control-plane/pkg/killswitch` |
| **Module 7: Cryptographic Merkle Audit** | `/control-plane/pkg/audit` |
| **Module 8: Agents & Mock Banking API** | `/agents-fleet`, `/mock-banking-api` |
| **Module 9: Operator Dashboard UI** | `/dashboard` |
| **Module 10: Chaos Engineering** | `/chaos-testing` |
| **Module 11: Monitoring & Ops** | `/infrastructure` |

You can inspect the full details in **[PROJECT_STRUCTURE.md](file:///d:/Projects/american%20express%20hackthon/PROJECT_STRUCTURE.md)**. Whenever you're ready, we can start creating the folder directories and implementing the first phase!