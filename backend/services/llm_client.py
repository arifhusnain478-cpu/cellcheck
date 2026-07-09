"""LLM client with provider routing.

Reads ``LLM_PROVIDER`` from the environment and routes to Anthropic (default)
or Groq. Both providers implement the same interface, so switching providers is
a one-line env change:

    LLM_PROVIDER=anthropic   # default — Claude via the anthropic SDK
    LLM_PROVIDER=groq        # temporary fallback — Llama via the groq SDK

Model IDs are configurable per provider via ANTHROPIC_MODEL / GROQ_MODEL.
"""
import os
from typing import Optional

DEFAULT_PROVIDER = "anthropic"

# Per-provider default model IDs (override via env).
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-5"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


class BaseLLMClient:
    """Shared interface. Every provider implements ``complete`` identically."""

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        raise NotImplementedError


class AnthropicClient(BaseLLMClient):
    """Claude via the official ``anthropic`` SDK (default provider)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from anthropic import AsyncAnthropic  # lazy import — only if this provider is used

        self._client = AsyncAnthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._model = model or os.getenv("ANTHROPIC_MODEL", ANTHROPIC_DEFAULT_MODEL)

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class GroqClient(BaseLLMClient):
    """Llama via the ``groq`` SDK (temporary fallback provider)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from groq import AsyncGroq  # lazy import — only if this provider is used

        self._client = AsyncGroq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self._model = model or os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL)

    async def complete(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""


_PROVIDERS = {
    "anthropic": AnthropicClient,
    "groq": GroqClient,
}


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """Return an LLM client for the configured (or given) provider."""
    name = (provider or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER)).lower()
    try:
        return _PROVIDERS[name]()
    except KeyError:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{name}'. Expected one of: {', '.join(_PROVIDERS)}."
        )
