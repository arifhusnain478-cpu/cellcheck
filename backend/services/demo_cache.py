"""Byte-stable demo cache for scripted demo recordings.

Problem: the LLM-generated prose (Quick Check "why" explanation + source_lab,
STR interpretation, Methods paragraph) is non-deterministic, so two recording
takes word things slightly differently — which looks inconsistent in a video edit.

When DEMO_MODE=true, the three endpoints pin *only* their LLM-generated text to
pre-approved values in data/demo_cache.json. Everything else — Cellosaurus identity,
ICLAC verdict, CLASTR match %/loci, Crossref retractions — still runs LIVE, so the
demo remains byte-stable while still proving real database integration.

When DEMO_MODE is false (the default), this module is inert: every accessor returns
None and every request runs fully live.

The cached values were captured from real live runs (scripts/build_demo_cache.py)
and reviewed as accurate and grounded before being committed. A cache miss (a line
or scenario not in the file) always falls back to live generation.
"""
import json
import os
from pathlib import Path
from typing import Optional

from utils.logger import get_logger

logger = get_logger("cellcheck.demo_cache")

_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_cache.json"
_cache: Optional[dict] = None
_TRUE = {"1", "true", "yes", "on"}


def demo_mode_enabled() -> bool:
    """True when DEMO_MODE is set truthy in the environment (read per call so a
    restart with a changed .env takes effect without code changes)."""
    return os.getenv("DEMO_MODE", "false").strip().lower() in _TRUE


def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("demo cache unavailable (%s); demo mode will run live", exc)
            _cache = {}
    return _cache


# --- key builders (kept identical between capture and serve) ------------------

def str_key(claimed_identity: str, matched_accession: Optional[str]) -> str:
    """Key an STR scenario by (claimed identity, the line CLASTR matched it to)."""
    return f"{(claimed_identity or '').strip().lower()}|{matched_accession or ''}"


def methods_key(accession: Optional[str], journal: Optional[str]) -> str:
    """Key a methods paragraph by (cell line accession, target journal)."""
    return f"{accession or ''}|{(journal or '').strip().lower()}"


# --- accessors (return None on any miss -> caller runs live) ------------------

def quick_demo(accession: Optional[str]) -> Optional[dict]:
    """Pinned {explanation, source_lab} for a Quick Check line, or None."""
    if not accession:
        return None
    return _load().get("quick_check", {}).get(accession)


def str_demo(claimed_identity: str, matched_accession: Optional[str]) -> Optional[str]:
    """Pinned STR interpretation text for a scenario, or None."""
    entry = _load().get("str_demo_cache", {}).get(str_key(claimed_identity, matched_accession))
    return entry.get("interpretation") if entry else None


def methods_demo(accession: Optional[str], journal: Optional[str]) -> Optional[str]:
    """Pinned methods paragraph for a (line, journal), or None."""
    entry = _load().get("methods_demo_cache", {}).get(methods_key(accession, journal))
    return entry.get("methods_paragraph") if entry else None
