# Sentinel — Complete Project File Schema & Directory Structure

This document defines the complete directory tree, module mappings, and file organization for the **Sentinel Zero-Trust Agent Control Plane** project.

---

## 📂 Master Directory Tree

```
d:\Projects\american express hackthon/
├── README.md                           # Executive Overview & Hackathon Presentation
├── ProjectDescription.md               # Formatted submission text for hackathon portal
├── modules.md                          # Master 12-Module Architectural Breakdown
├── PROJECT_STRUCTURE.md                # Project File Schema & Folder Mapping (This File)
├── docker-compose.yml                  # One-click multi-container stack orchestration
├── Makefile                            # Developer shortcuts for build, test, and run
│
├── api/                                # Module 0.1: Protocols & API Schemas
│   ├── proto/                          # Protocol Buffers definitions
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

## 🎯 Module-to-Folder Mapping Matrix

| Architectural Module | Primary Code Location | Key Files |
| :--- | :--- | :--- |
| **Module 0: Infrastructure & Protocols** | `/api`, `/infrastructure` | `agent_intent.proto`, `docker-compose.yml`, `redis.conf` |
| **Module 1: Identity & Lifecycle** | `/control-plane/pkg/identity` | `spiffe_validator.go`, `state_manager.go`, `reputation_scorer.go` |
| **Module 2: AI Safety & Sanitizer** | `/control-plane/pkg/sanitizer` | `prompt_firewall.go`, `schema_validator.go`, `rag_guard.go` |
| **Module 3: Multi-Agent Coordinator** | `/control-plane/pkg/coordinator` | `graph_tracker.go`, `cycle_detector.go`, `risk_scorer.go` |
| **Module 4: OPA Policy PDP Engine** | `/control-plane/pkg/pdp`, `/policies` | `opa_evaluator.go`, `main.rego`, `servicing_disputes.rego` |
| **Module 5: Financial Guardrails** | `/control-plane/pkg/guardrails` | `token_bucket.go`, `lua_scripts.go`, `redlock_2pc.go` |
| **Module 6: Sub-10ms Emergency Kill-Switch**| `/control-plane/pkg/killswitch` | `broadcast_listener.go`, `token_revoker.go` |
| **Module 7: Merkle Audit & Telemetry** | `/control-plane/pkg/audit` | `merkle_tree.go`, `prometheus_exporter.go` |
| **Module 8: Agents & Mock Banking API** | `/agents-fleet`, `/mock-banking-api` | `servicing_agent.py`, `sentinel_sdk.py`, `transfers.py` |
| **Module 9: Operator Dashboard UI** | `/dashboard` | `FleetMap.tsx`, `RedButtonKillSwitch.tsx`, `PolicyEditor.tsx` |
| **Module 10: Chaos & Load Testing** | `/chaos-testing` | `prompt_injection_storm.py`, `k6_sla_test.js` |
| **Module 11: Production & Observability** | `/infrastructure` | `prometheus.yml`, `gateway_latency.json` |

---
*Sentinel Project File Schema Blueprint.*
