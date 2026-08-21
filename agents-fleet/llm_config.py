"""
Shared Groq LLM configuration for all Sentinel agents.
=======================================================
Single source of truth for the Groq model and client initialization.
Every agent in the fleet imports from here -- never hardcode model names.

Models verified against this account API key (Aug 2026):
  PRIMARY:   openai/gpt-oss-120b
             Best tool-calling + reasoning. Groq recommended replacement
             for llama-3.3-70b-versatile.

  FAST:      openai/gpt-oss-20b
             Lower-latency. Use for high-frequency / simple tasks.

  REASONING: qwen/qwen3.6-27b
             Chain-of-thought model. Use for complex analysis.

  GUARD:     meta-llama/llama-prompt-guard-2-86m
             Tiny injection-detection classifier. Safety pipeline only.

Full model list on this account:
  openai/gpt-oss-120b, openai/gpt-oss-20b, openai/gpt-oss-safeguard-20b,
  qwen/qwen3.6-27b, meta-llama/llama-prompt-guard-2-86m,
  meta-llama/llama-prompt-guard-2-22m, groq/compound, groq/compound-mini,
  allam-2-7b, whisper-large-v3, whisper-large-v3-turbo

DEPRECATED -- do not use:
  llama-3.3-70b-versatile, llama-3.1-8b-instant (removed June 2026)

To update the model fleet-wide: change GROQ_DEFAULT_MODEL here only.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load from agents-fleet/.env (where GROQ_API_KEY lives)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError(
        "[SENTINEL] GROQ_API_KEY not found. "
        "Set it in agents-fleet/.env: GROQ_API_KEY=gsk_..."
    )

# ── Model registry (verified Aug 2026 against this account) ──────────────────
GROQ_DEFAULT_MODEL   = "openai/gpt-oss-120b"                   # best tool-calling
GROQ_FAST_MODEL      = "openai/gpt-oss-20b"                    # low-latency
GROQ_REASONING_MODEL = "qwen/qwen3.6-27b"                      # CoT reasoning
GROQ_GUARD_MODEL     = "meta-llama/llama-prompt-guard-2-86m"   # injection detection


def get_llm(
    model: str = GROQ_DEFAULT_MODEL,
    temperature: float = 0,
    max_tokens: int = 2048,
) -> ChatGroq:
    """
    Create and return a configured ChatGroq client.

    Args:
        model:       Groq model ID. Defaults to GROQ_DEFAULT_MODEL.
        temperature: 0 = deterministic (best for tool-calling agents).
        max_tokens:  Max response tokens.

    Returns:
        Configured ChatGroq instance.
    """
    return ChatGroq(
        model=model,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_llm_with_tools(tools: list, model: str = GROQ_DEFAULT_MODEL) -> ChatGroq:
    """
    Create a ChatGroq client bound to a list of LangChain tools.
    Use this for agentic loops that need tool-calling capability.

    Args:
        tools: List of @tool-decorated LangChain functions.
        model: Groq model ID. Defaults to GROQ_DEFAULT_MODEL.

    Returns:
        ChatGroq instance with tools bound.
    """
    return get_llm(model=model).bind_tools(tools)
