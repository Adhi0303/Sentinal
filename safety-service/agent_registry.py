"""
Module A: Agent Registry
========================
Manages the lifecycle of AI agents registered with Sentinel.
Each agent has a persistent profile, status, and lifecycle state.

This is the foundation of the new Razorpay Sentinel — agents are no longer
anonymous request senders. They are named, managed entities with a full
lifecycle: ACTIVE → SUSPENDED / QUARANTINED → RETIRED.

Redis keys used:
  sentinel:agent:{agent_id}    → Hash (agent profile fields)
  sentinel:agent:list          → Set  (all registered agent IDs)
"""

import uuid
import json
import redis
from datetime import datetime, timezone
from typing import Optional, List

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

AGENT_KEY_PREFIX = "sentinel:agent:"
AGENT_LIST_KEY   = "sentinel:agent:list"

# Valid lifecycle transitions (from_state → list of allowed to_states)
VALID_TRANSITIONS = {
    "ACTIVE":      ["SUSPENDED", "QUARANTINED", "RETIRED"],
    "SUSPENDED":   ["ACTIVE", "RETIRED"],
    "QUARANTINED": ["ACTIVE", "RETIRED"],
    "RETIRED":     [],   # terminal — no further transitions
}


def register_agent(
    name: str,
    owner: str,
    purpose: str,
    allowed_tools: List[str],
    blocked_tools: List[str],
    financial_limit_per_tx: float,
    daily_budget: float,
    model: str = "gpt-4o",
    created_by: str = "admin",
    agent_id: Optional[str] = None,
) -> dict:
    """
    Create and persist a new agent. Returns full agent profile.
    If agent_id is not provided, one is auto-generated from the name.
    """
    if agent_id is None:
        slug = name.lower().replace(" ", "-")[:20]
        agent_id = f"{slug}-{uuid.uuid4().hex[:6]}"

    now = datetime.now(timezone.utc).isoformat()

    profile = {
        "agent_id":               agent_id,
        "name":                   name,
        "owner":                  owner,
        "purpose":                purpose,
        "allowed_tools":          json.dumps(allowed_tools),
        "blocked_tools":          json.dumps(blocked_tools),
        "model":                  model,
        "financial_limit_per_tx": str(financial_limit_per_tx),
        "daily_budget":           str(daily_budget),
        "status":                 "ACTIVE",
        "created_at":             now,
        "created_by":             created_by,
        "updated_at":             now,
    }

    redis_client.hset(f"{AGENT_KEY_PREFIX}{agent_id}", mapping=profile)
    redis_client.sadd(AGENT_LIST_KEY, agent_id)

    print(f"[REGISTRY] Agent registered: '{agent_id}' | owner='{owner}' | tools={allowed_tools}")
    return _format_agent(redis_client.hgetall(f"{AGENT_KEY_PREFIX}{agent_id}"))


def get_agent(agent_id: str) -> Optional[dict]:
    """
    Retrieve agent profile by ID.
    Returns None if the agent does not exist.
    """
    data = redis_client.hgetall(f"{AGENT_KEY_PREFIX}{agent_id}")
    if not data:
        return None
    return _format_agent(data)


def list_agents(
    status: Optional[str] = None,
    owner: Optional[str] = None,
) -> List[dict]:
    """
    Return all registered agents.
    Optionally filter by status (ACTIVE / SUSPENDED / QUARANTINED / RETIRED)
    or by owner (case-insensitive merchant name).
    """
    agent_ids = redis_client.smembers(AGENT_LIST_KEY)
    agents = []
    for aid in agent_ids:
        a = get_agent(aid)
        if a is None:
            continue
        if status and a["status"] != status:
            continue
        if owner and a["owner"].lower() != owner.lower():
            continue
        agents.append(a)
    # Return newest-first (most recently registered at top)
    return sorted(agents, key=lambda x: x["created_at"], reverse=True)


def update_agent_status(
    agent_id: str,
    new_status: str,
    changed_by: str = "system",
) -> dict:
    """
    Transition an agent's lifecycle state.
    Validates the transition against VALID_TRANSITIONS.
    Raises ValueError on invalid transitions or if agent not found.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent '{agent_id}' not found in registry")

    current = agent["status"]
    allowed = VALID_TRANSITIONS.get(current, [])

    if new_status not in allowed:
        raise ValueError(
            f"Invalid lifecycle transition: {current} → {new_status}. "
            f"Allowed transitions from '{current}': {allowed or ['(none — terminal state)']}"
        )

    now = datetime.now(timezone.utc).isoformat()
    redis_client.hset(f"{AGENT_KEY_PREFIX}{agent_id}", mapping={
        "status":     new_status,
        "updated_at": now,
    })

    print(f"[REGISTRY] '{agent_id}' lifecycle: {current} → {new_status} (by '{changed_by}')")
    return get_agent(agent_id)


def update_agent_config(
    agent_id: str,
    updates: dict,
) -> dict:
    """
    Update mutable agent config fields (tools, limits, model).
    Does NOT allow changing agent_id, owner, created_at, or status via this function.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent '{agent_id}' not found")

    # Fields that are allowed to be updated
    MUTABLE_FIELDS = {
        "name", "purpose", "model",
        "allowed_tools", "blocked_tools",
        "financial_limit_per_tx", "daily_budget",
    }

    now = datetime.now(timezone.utc).isoformat()
    mapped = {"updated_at": now}

    for field, value in updates.items():
        if field not in MUTABLE_FIELDS:
            continue  # silently skip immutable fields
        if field in ("allowed_tools", "blocked_tools"):
            mapped[field] = json.dumps(value)
        elif field in ("financial_limit_per_tx", "daily_budget"):
            mapped[field] = str(value)
        else:
            mapped[field] = value

    redis_client.hset(f"{AGENT_KEY_PREFIX}{agent_id}", mapping=mapped)
    print(f"[REGISTRY] '{agent_id}' config updated: {list(updates.keys())}")
    return get_agent(agent_id)


def check_tool_allowed(agent_id: str, tool_name: str) -> dict:
    """
    Check if a specific tool is in the agent's allowed_tools list
    and NOT in blocked_tools.
    Used by the capability check gate in main.py.
    Returns: { allowed: bool, reason: str }
    """
    agent = get_agent(agent_id)
    if not agent:
        return {"allowed": False, "reason": f"Agent '{agent_id}' not registered"}

    allowed_tools = agent.get("allowed_tools", [])
    blocked_tools = agent.get("blocked_tools", [])

    if tool_name in blocked_tools:
        return {
            "allowed": False,
            "reason":  f"Tool '{tool_name}' is explicitly blocked for agent '{agent_id}'"
        }
    if tool_name not in allowed_tools:
        return {
            "allowed": False,
            "reason":  f"Tool '{tool_name}' is not in agent '{agent_id}' allowed_tools list"
        }
    return {"allowed": True, "reason": f"Tool '{tool_name}' is permitted for agent '{agent_id}'"}


def _format_agent(raw: dict) -> dict:
    """Parse Redis hash strings back into proper Python types."""
    return {
        "agent_id":               raw.get("agent_id"),
        "name":                   raw.get("name"),
        "owner":                  raw.get("owner"),
        "purpose":                raw.get("purpose"),
        "allowed_tools":          json.loads(raw.get("allowed_tools", "[]")),
        "blocked_tools":          json.loads(raw.get("blocked_tools", "[]")),
        "model":                  raw.get("model"),
        "financial_limit_per_tx": float(raw.get("financial_limit_per_tx", 0)),
        "daily_budget":           float(raw.get("daily_budget", 0)),
        "status":                 raw.get("status"),
        "created_at":             raw.get("created_at"),
        "created_by":             raw.get("created_by"),
        "updated_at":             raw.get("updated_at"),
    }
