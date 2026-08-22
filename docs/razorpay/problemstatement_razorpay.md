Absolutely, boss. Based on the Sentinel material we reviewed, the new Razorpay direction can now be framed as a **clear problem statement rather than just a collection of features**.

# Sentinel — Adaptive Autonomy Control Plane

## 1. The problem we are actually solving

The next generation of software systems will not just contain a single AI chatbot. Businesses will increasingly operate **fleets of autonomous AI agents**.

For example, a payment/fintech company could have:

```text
Customer Support Agent
        │
        ├── Refund Agent
        │
        ├── Payment Investigation Agent
        │
        ├── Fraud Analysis Agent
        │
        ├── Settlement Agent
        │
        └── Merchant Operations Agent
```

These agents won't merely answer questions.

They may:

* retrieve customer information
* inspect payments
* initiate refunds
* create invoices
* communicate with customers
* trigger other agents
* invoke APIs
* modify operational state
* make decisions without asking a human every time

That creates a new problem:

> **How do we safely give AI agents autonomy without giving them uncontrolled authority?**

The existing Sentinel work identified the underlying governance gap: traditional IAM, RBAC, API gateways and conventional security controls answer questions like *"Does this identity have permission?"*, but autonomous agents introduce a different question: *"Should this particular AI action be trusted in this particular context?"* 

Our new project takes that problem one level further.

---

# 2. The central problem statement

### **Businesses lack a dynamic control mechanism for managing the autonomy of AI agents.**

Today, an organization can give an AI agent a set of permissions:

```text
RefundAgent
   ↓
Can refund payments
Can read orders
Can access customer data
```

But permissions alone don't tell us whether the agent **should continue operating with that level of freedom**.

Imagine:

```text
Day 1

Agent behaves normally
Trust = 95
Autonomy = High
```

Then:

```text
Day 20

Agent starts making unusual requests
Agent accesses unexpected tools
Agent's transaction velocity increases
Agent begins interacting with other agents abnormally
```

Traditional authorization may still say:

```text
✓ Agent has permission
```

But something much more important has changed:

```text
The agent's BEHAVIOR has changed.
```

That is the gap Sentinel will address.

---

# 3. The fundamental idea

We are building a system where:

> **Autonomy is not a permanent permission. Autonomy is a continuously earned level of trust.**

Instead of:

```text
Agent → Permission → Execute
```

we create:

```text
Agent
   ↓
Identity
   ↓
Capabilities
   ↓
Policy
   ↓
Behavior
   ↓
Risk
   ↓
Trust
   ↓
Autonomy Level
   ↓
Action Governance
   ↓
Execute / Review / Restrict / Block
```

This is the core idea of the new Sentinel.

---

# 4. What makes this different from the original Sentinel

The original Sentinel primarily asks:

> **"Is this action safe enough to execute?"**

The new Sentinel asks two questions:

### Question 1

> **"Is this particular action safe?"**

That's the existing governance engine.

### Question 2

> **"Given everything we know about this agent, how much autonomy should this agent currently have?"**

That's the new control-plane layer.

So:

```text
             OLD SENTINEL
                  │
                  ▼
        Action Governance
                  │
          ALLOW / BLOCK
```

becomes:

```text
             NEW SENTINEL
                  │
                  ▼
          Agent Governance
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
   Agent Trust          Action Risk
        │                   │
        └─────────┬─────────┘
                  ▼
          Autonomy Decision
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     Allow      Review     Block
```

---

# 5. Real-world Razorpay scenario

Let's make this concrete.

Imagine Razorpay has a merchant using an autonomous:

# **Refund Agent**

Its job is simple:

> Automatically process legitimate customer refund requests.

The agent is given:

```text
Agent:
RefundAgent-001

Allowed operations:
✓ Read payment
✓ Read order
✓ Verify refund eligibility
✓ Initiate refund

Financial limit:
₹5,000 per transaction

Daily limit:
₹1,00,000

Autonomy:
Bounded
```

Initially, everything works perfectly.

---

# 6. Normal operation

Customers request refunds.

The agent performs:

```text
Order #1001
₹800 refund
      ↓
Approved

Order #1002
₹1,500 refund
      ↓
Approved

Order #1003
₹2,000 refund
      ↓
Approved
```

Sentinel observes:

```text
Normal behavior
Normal velocity
Correct tools
Correct parameters
No policy violations
No unusual agent interactions
```

Therefore:

```text
Trust Score = 96

Autonomy = BOUNDED / HIGH
```

The agent continues operating automatically.

---

# 7. Now the interesting part

Suppose something goes wrong.

Maybe:

* the underlying model changes,
* the agent's prompt gets manipulated,
* retrieved context becomes poisoned,
* a tool behaves unexpectedly,
* another compromised agent influences it,
* or the agent simply starts behaving abnormally.

The agent suddenly starts doing:

```text
₹4,900 refund
₹4,850 refund
₹4,700 refund
₹4,950 refund
₹4,800 refund
...
```

Each transaction individually might technically be below the ₹5,000 limit.

This is exactly why simple authorization isn't enough.

The existing Sentinel research already identifies machine-speed velocity and micro-transaction attacks as a key failure mode. 

---

# 8. Traditional system response

A conventional permission system may see:

```text
₹4,900 < ₹5,000

✓ PERMITTED
```

Then:

```text
₹4,850 < ₹5,000

✓ PERMITTED
```

Then:

```text
₹4,700 < ₹5,000

✓ PERMITTED
```

And the agent keeps going.

The problem isn't necessarily that **one transaction violates the rule**.

The problem is that:

> **The overall behavior of the agent has become abnormal.**

---

# 9. Sentinel's response

Sentinel sees the bigger picture.

It observes:

```text
Transaction velocity ↑
Refund frequency ↑
Tool usage pattern changed
Customer targeting changed
Behavior deviates from baseline
Financial exposure ↑
```

The system recalculates:

```text
Risk ↑
Trust ↓
```

For example:

```text
Trust

96
 ↓
89
 ↓
76
 ↓
61
```

And therefore:

```text
AUTONOMY

High
 ↓
Bounded
 ↓
Human Approval
```

The agent doesn't necessarily get killed immediately.

**Its autonomy is reduced.**

That's the important concept.

---

# 10. Then imagine the agent tries something worse

The agent attempts:

```text
modify_payout_account()
```

But its original purpose is:

> Refund customers.

Its capability profile says:

```text
Allowed:
✓ Payment read
✓ Order read
✓ Refund

Not allowed:
✗ Modify payout
```

Sentinel catches it.

```text
Capability violation
        ↓
Policy violation
        ↓
Risk HIGH
        ↓
Action BLOCKED
```

And if repeated:

```text
Trust → 25

Autonomy → QUARANTINED
```

The agent is isolated.

The existing Sentinel architecture already provides the underlying quarantine, revocation and fleet-control mechanisms we can reuse here. 

---

# 11. The key innovation: autonomy adapts

This is the core of the new system.

Instead of:

```text
Permission = ON/OFF
```

we have:

```text
                    TRUST
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     HIGH           MEDIUM          LOW
       │              │              │
       ▼              ▼              ▼
   AUTONOMOUS       BOUNDED        HUMAN
   EXECUTION        EXECUTION      APPROVAL
                                      │
                                      ▼
                                  QUARANTINE
```

For example:

|  Trust | Autonomy               |
| -----: | ---------------------- |
| 90–100 | High autonomy          |
|  70–89 | Bounded autonomy       |
|  40–69 | Human approval         |
|    <40 | Restricted/quarantined |

These are **illustrative thresholds**, not something we should hard-code into the final product.

The organization should be able to configure them.

---

# 12. What contributes to Trust?

Trust shouldn't be some random AI-generated number.

It should be based on measurable signals.

### Positive signals

```text
✓ Successful actions
✓ Policy compliance
✓ Stable behavior
✓ Correct tool usage
✓ Normal transaction patterns
✓ Successful task completion
✓ Clean historical record
```

### Negative signals

```text
✗ Policy violations
✗ Unusual tool calls
✗ Abnormal transaction velocity
✗ Repeated failures
✗ Unexpected API access
✗ Suspicious agent delegation
✗ Prompt/context attacks
✗ Risky financial behavior
✗ Repeated HITL rejection
```

So:

```text
              Agent Behavior
                    │
                    ▼
              Trust Engine
                    │
             Trust Score
                    │
                    ▼
             Autonomy Engine
```

---

# 13. Multi-agent scenario

This becomes even more interesting with agent-to-agent communication.

Imagine:

```text
Customer Agent
      │
      ▼
Refund Agent
      │
      ▼
Payment Agent
      │
      ▼
Settlement Agent
```

Normally:

```text
Customer Agent
    ↓
"Refund customer"

Refund Agent
    ↓
"Check payment"

Payment Agent
    ↓
"Verify transaction"

Settlement Agent
    ↓
"Update settlement"
```

But imagine a compromised agent starts delegating unexpectedly:

```text
Refund Agent
     ↓
Settlement Agent
     ↓
Payout Agent
     ↓
Bank Account Modification
```

Now the problem isn't just an individual action.

It's the **relationship between agents**.

Sentinel's existing multi-agent governance already considers dependency chains, circular execution, privilege escalation and cascading failures. 

We extend that into the new control plane:

```text
WHO
 ↓
DELEGATED TO WHOM?
 ↓
FOR WHAT PURPOSE?
 ↓
WITH WHAT PERMISSION?
 ↓
WHAT FINANCIAL IMPACT?
```

---

# 14. The system therefore becomes a continuous feedback loop

This is the architecture we really want to demonstrate:

```text
              REGISTER AGENT
                    │
                    ▼
             DEFINE PURPOSE
                    │
                    ▼
           ASSIGN CAPABILITIES
                    │
                    ▼
             ASSIGN POLICIES
                    │
                    ▼
            INITIAL TRUST
                    │
                    ▼
            INITIAL AUTONOMY
                    │
                    ▼
                 DEPLOY
                    │
                    ▼
              AGENT ACTS
                    │
                    ▼
              SENTINEL
              OBSERVES
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Policy       Risk      Behavior
        │           │           │
        └───────────┼───────────┘
                    ▼
              TRUST UPDATE
                    │
                    ▼
          AUTONOMY ADJUSTMENT
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        ALLOW     REVIEW     BLOCK
          │         │         │
          └─────────┼─────────┘
                    ▼
                  AUDIT
                    │
                    └─────────────►
                         CONTINUOUSLY
```

That's the **actual product loop**.

---

# 15. What Sentinel provides to a Razorpay merchant

Imagine I'm a merchant.

I don't want to understand:

* OPA
* Redis
* Rego
* SAGA
* cryptographic ledgers
* agent graphs

I want to see:

### My AI Agents

```text
┌──────────────────────────────────┐
│ Refund Agent                     │
│                                  │
│ Trust       94                   │
│ Risk        Low                  │
│ Autonomy    Bounded              │
│ Status      ● Active             │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ Support Agent                    │
│                                  │
│ Trust       82                   │
│ Risk        Medium               │
│ Autonomy    Human Approval       │
│ Status      ● Active             │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ Settlement Agent                 │
│                                  │
│ Trust       31                   │
│ Risk        Critical             │
│ Autonomy    Quarantined          │
│ Status      ● Isolated           │
└──────────────────────────────────┘
```

Now the merchant immediately understands the value.

---

# 16. What happens when something goes wrong?

This is another important part of the problem statement.

We don't want:

> "Sentinel detected a bad transaction."

We want:

> **"Sentinel detected that the agent itself was becoming unsafe."**

Then:

```text
ANOMALY
   ↓
RISK INCREASE
   ↓
TRUST DECREASE
   ↓
AUTONOMY REDUCTION
   ↓
ACTION RESTRICTION
   ↓
HUMAN REVIEW
   ↓
QUARANTINE IF NECESSARY
   ↓
RECOVERY
```

This gives us **progressive containment**.

Instead of:

```text
Everything normal
        ↓
BOOM
        ↓
Kill agent
```

we have:

```text
Normal
 ↓
Suspicious
 ↓
Restricted
 ↓
Human supervised
 ↓
Blocked
 ↓
Quarantined
```

That is much more realistic for enterprise AI operations.

---

# 17. Why Razorpay is a strong environment for this

For the hackathon, we don't need to pretend we're building a generic enterprise platform with no concrete use case.

We anchor it around **financial operations**, because the consequences of uncontrolled autonomous actions are easy to understand.

The original Sentinel research already centered on financial operations such as refunds, credit decisions, treasury operations and payments. 

For the Razorpay version, we can demonstrate:

### Payment Agent

```text
Create payment
Check payment
Verify payment
```

### Refund Agent

```text
Check refund eligibility
Initiate refund
Track refund
```

### Merchant Support Agent

```text
Read payment status
Explain failed payment
Create support ticket
```

### Settlement Agent

```text
Check settlement
Analyze settlement
```

And then Sentinel controls what each agent is actually allowed to do.

---

# 18. The actual security problem

The danger is not simply:

> **"AI can make mistakes."**

The deeper problem is:

> **AI agents can make mistakes at machine speed while possessing real-world authority.**

A human employee might make 20 decisions in an hour.

An autonomous agent could potentially make thousands of API calls in the same period.

Your original Sentinel research specifically identifies this machine-speed execution and micro-transaction problem. 

Therefore:

```text
Human mistake
     ↓
Limited blast radius

AI mistake
     ↓
Machine speed
     ↓
Repeated execution
     ↓
Multiple systems
     ↓
Multiple agents
     ↓
Potentially massive blast radius
```

Sentinel's job is to control that blast radius.

---

# 19. The business problem

For a company like Razorpay, there's a tension:

### Without autonomous AI

```text
Human involvement ↑
Automation ↓
Operational cost ↑
Response time ↑
```

### With unrestricted autonomous AI

```text
Automation ↑
Risk ↑
Financial exposure ↑
Compliance risk ↑
Operational uncertainty ↑
```

So companies end up stuck in the middle:

```text
             AUTONOMOUS AI
                  ▲
                  │
                  │
       ───────────┼──────────
                  │
             TRUST GAP
                  │
                  │
                  ▼
             HUMAN ONLY
```

They want more automation, but they need confidence that agents won't exceed their mandate.

### Sentinel bridges that gap.

```text
             FULL AUTONOMY
                  ▲
                  │
          Sentinel gradually
          increases autonomy
                  │
                  │
             TRUST ENGINE
                  │
                  │
          monitored autonomy
                  │
                  ▼
          HUMAN SUPERVISION
```

---

# 20. What the Razorpay hackathon solution ultimately provides

Our product gives a business:

### 1. Agent Identity

Every agent has a distinct identity.

### 2. Agent Capabilities

Every agent has clearly defined tools and permissions.

### 3. Agent Policies

Rules define what the agent can and cannot do.

### 4. Agent Risk

Every action and agent behavior is risk-evaluated.

### 5. Agent Trust

Trust evolves according to actual behavior.

### 6. Adaptive Autonomy

The system dynamically decides how much freedom the agent receives.

### 7. Multi-Agent Governance

Agent delegation and interaction are monitored.

### 8. Human Oversight

High-risk decisions can be escalated.

### 9. Progressive Containment

Agents can move from:

```text
Autonomous
→ Restricted
→ Human supervised
→ Blocked
→ Quarantined
```

### 10. Recovery

Compensation, rollback, revocation and recovery mechanisms are available through the existing Sentinel foundation.

---

# 21. The one-sentence problem statement

If the judges ask:

> **"What problem are you solving?"**

I'd answer:

> **As businesses deploy fleets of autonomous AI agents to perform financial and operational tasks, existing permission systems cannot dynamically determine whether an agent should continue operating with its current level of autonomy. Sentinel solves this by continuously evaluating agent identity, capabilities, policies, behavior, risk and trust, and dynamically increasing, restricting or revoking autonomy before unsafe behavior can cause real-world impact.**

---

# 22. The one-sentence solution

If they ask:

> **"What exactly did you build?"**

Say:

> **Sentinel is an adaptive autonomy control plane that manages the lifecycle of AI agents and continuously adjusts their permissions and autonomy based on real-time behavior, risk and trust while enforcing every action through a zero-trust governance layer.**

---

# 23. The strongest pitch

And honestly, boss, **this is the line I'd build the entire Razorpay presentation around:**

> ## **"AI agents shouldn't receive permanent autonomy. They should earn it."**

Then explain:

```text
Register
   ↓
Trust
   ↓
Authorize
   ↓
Observe
   ↓
Adapt
   ↓
Recover
```

And the final statement:

> **Sentinel enables businesses to move from "AI that can act" to "AI that can be trusted to act."**

That is the problem, the product, and the reason the existing Sentinel work is valuable for this new Razorpay stream.
