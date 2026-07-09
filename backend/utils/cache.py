"""Minimal in-memory cache stub.

Swap for a TTL cache or Redis once external API calls are wired up — external
lookups (Cellosaurus, CLASTR, Semantic Scholar) are prime candidates for caching.
"""
from typing import Any, Optional

_STORE: dict[str, Any] = {}


def get(key: str) -> Optional[Any]:
    # TODO: add TTL / eviction.
    return _STORE.get(key)


def set(key: str, value: Any) -> None:
    _STORE[key] = value


def clear() -> None:
    _STORE.clear()
