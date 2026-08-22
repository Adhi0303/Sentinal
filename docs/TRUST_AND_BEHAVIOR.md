# Trust Engine & Behavioral Monitoring

Traditional RBAC (Role-Based Access Control) assumes that if an entity has a role, it can always perform the actions associated with that role. Sentinel uses a **Zero-Trust, Dynamic Scoring** approach instead.

## The Dynamic Trust Score (0.0 - 100.0)

Every AI agent starts with a baseline trust score (e.g., 80.0). Every action the agent attempts, and the outcome of that action, generates a "Trust Signal." These signals dynamically increase or decrease the agent's score in real-time.

### Trust Signals & Weights
- `TRANSACTION_COMPLETED` (+5.0): The agent successfully executed a safe action.
- `HITL_APPROVED` (+0.2): A human operator reviewed and approved the agent's proposal. (Small reward because the agent was correct, but it still required manual intervention).
- `ACTION_DENIED_POLICY` (-2.0): The agent attempted something blocked by business rules.
- `HIGH_RISK_ESCALATED` (-2.0): The agent attempted a high-risk action requiring manager review.
- `HITL_REJECTED` (-8.0): A human operator reviewed and explicitly rejected the agent's proposal.
- `BEHAVIOR_ANOMALY_SEVERE` (-8.0): The agent deviated significantly from its normal baseline.
- `KILL_SWITCH_TRIGGERED` (-20.0): An extreme violation or prompt injection was detected.

*All weights are configurable in the Dashboard.*

### Autonomy Tiers
The trust score dictates the agent's "Autonomy Tier" (Gate 6 in the pipeline):
- **FULL (90-100)**: The agent operates completely autonomously.
- **BOUNDED (70-89)**: Standard actions are autonomous, but high-value actions are escalated.
- **HITL (40-69)**: The agent loses autonomy. Every modifying action is paused and sent to the Human-In-The-Loop queue.
- **QUARANTINE (<40)**: The agent is locked out completely.

## The Behavior Monitor

Because LLMs are non-deterministic, they can act unpredictably if confused or subjected to Prompt Injection attacks. Sentinel's Behavior Monitor protects against this by establishing statistical baselines.

### Establishing the Baseline
For the first 10 actions an agent takes, the Behavior Monitor operates in "learning mode." It records:
- Average transaction amount.
- Transaction velocity (actions per minute).
- Standard call depth.
- Most commonly used tools.
- Most common target accounts.

### Detecting Deviations
Once the baseline is locked, every subsequent action is scored against the profile across 6 axes:
1. **Amount Deviations**: `amount_spike` (1.5x average) or `amount_extreme` (3x average).
2. **Velocity Surges**: `velocity_surge` (doing too much too fast).
3. **Complexity**: `depth_increase` (making too many recursive tool calls).
4. **Tool Drift**: `tool_drift` (attempting to use a tool it rarely uses).
5. **Target Drift**: `new_account_target` (sending money to an unknown account).
6. **Limit Proximity**: `near_limit_cluster` (repeatedly trying to send money just below the hard limit).

If the combined deviation score exceeds 25/100, the Monitor emits a trust penalty. If it exceeds 60/100, a `BEHAVIOR_ANOMALY_SEVERE` (-8.0) signal is immediately fired, often dropping the agent out of the FULL autonomy tier instantly.
