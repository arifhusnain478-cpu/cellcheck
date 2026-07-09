"""Grounded generation of a publication-ready cell line methods paragraph.

The RRID and cell line identity come from Cellosaurus (authoritative); the LLM
writes the paragraph strictly from the form inputs + fetched identity. Best-effort:
returns None if the LLM is unavailable (endpoint has a deterministic fallback).
Grounding rules live in prompts/methods_generation.txt.
"""
from pathlib import Path
from typing import Optional

from models.methods import MethodsRequest
from models.quick_check import Identity
from services.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger("cellcheck.methods_writer")

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "methods_generation.txt"
_system_prompt: Optional[str] = None


def _load_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    return _system_prompt


def build_facts_prompt(req: MethodsRequest, identity: Identity) -> str:
    lines = ["FACTS (use only these — omit any clause whose fact is not present):",
             f"- Authoritative cell line name (Cellosaurus): {identity.correct_name}"]
    if identity.rrid:
        lines.append(f"- RRID: {identity.rrid}")
    if identity.species:
        lines.append(f"- Species: {identity.species}")
    if identity.true_origin:
        lines.append(f"- Tissue / disease of origin (Cellosaurus): {identity.true_origin}")
    if req.source:
        lines.append(f"- Obtained from (source / catalog): {req.source}")
    if req.authentication_service:
        lines.append(f"- Authentication method / service: {req.authentication_service}")
    if req.authentication_date:
        lines.append(f"- Authentication date: {req.authentication_date}")
    if req.mycoplasma_test_date:
        lines.append(f"- Mycoplasma tested negative on (date): {req.mycoplasma_test_date}")
    if req.passage_range:
        lines.append(f"- Passage range used in experiments: {req.passage_range}")
    lines.append(f"- Target journal (for formatting/tone): "
                 f"{req.target_journal or 'unspecified — use generic ANSI/ATCC style'}")
    lines.append("")
    lines.append("Write the cell line methods paragraph now, using only the facts above.")
    return "\n".join(lines)


async def write_methods(req: MethodsRequest, identity: Identity) -> Optional[str]:
    """Return the generated methods paragraph, or None if the LLM is unavailable."""
    try:
        client = get_llm_client()
        text = await client.complete(
            system=_load_system_prompt(),
            prompt=build_facts_prompt(req, identity),
            max_tokens=400,
        )
        text = (text or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 — best-effort; endpoint has a fallback
        logger.warning("LLM methods generation unavailable (%s)", exc)
        return None
