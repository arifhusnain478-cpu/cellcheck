"""Generate a grounded, plain-language explanation of a Quick Check verdict.

The verdict is decided deterministically (services/iclac_service.compute_verdict);
the LLM only *phrases* an explanation of the facts it is handed. It must never
invent details — the grounding rules live in prompts/verdict_generation.txt.

The explanation is best-effort: if the LLM is unavailable (no key, network error,
provider error), `explain()` returns None and the verdict is returned without it.
"""
from pathlib import Path
from typing import Optional

from models.quick_check import Identity
from services.iclac_service import ICLACStatus
from services.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger("cellcheck.explainer")

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "verdict_generation.txt"
_system_prompt: Optional[str] = None

_VERDICT_MEANING = {
    "red": "confirmed misidentified or cross-contaminated",
    "yellow": "caution — identity not fully certain",
    "green": "no known misidentification",
}


def _load_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    return _system_prompt


def build_facts_prompt(query: str, identity: Identity, status: ICLACStatus, verdict: str) -> str:
    """Assemble the grounded fact list handed to the LLM (only known fields)."""
    lines = [
        "FACTS (use only these — do not add anything else):",
        f"- User query: {query}",
        f"- Verdict (already decided, do not change): {verdict} = "
        f"{_VERDICT_MEANING.get(verdict, verdict)}",
        f"- Cell line name (Cellosaurus): {identity.correct_name}",
    ]
    if identity.rrid:
        lines.append(f"- RRID / accession: {identity.rrid}")
    if identity.species:
        lines.append(f"- Species: {identity.species}")
    if identity.true_origin:
        lines.append(f"- Established identity / origin (Cellosaurus): {identity.true_origin}")

    lines.append("- ICLAC Register of Misidentified Cell Lines:")
    if status.on_register:
        lines.append("    * This line IS listed as misidentified / cross-contaminated.")
        if status.claimed_identity:
            lines.append(f"    * Commonly assumed / claimed to be: {status.claimed_identity}")
        if status.true_identity:
            lines.append(f"    * Actually is: {status.true_identity}")
        if status.year_reported:
            lines.append(f"    * Year the misidentification was reported: {status.year_reported}")
    else:
        lines.append("    * This line is NOT listed in the ICLAC register.")

    lines.append("")
    lines.append(
        "Write a 2-3 sentence plain-language explanation of why this verdict was reached, "
        "using only the facts above."
    )
    return "\n".join(lines)


async def explain(query: str, identity: Identity, status: ICLACStatus,
                  verdict: str) -> Optional[str]:
    """Return a grounded explanation string, or None if the LLM is unavailable."""
    try:
        client = get_llm_client()
        text = await client.complete(
            system=_load_system_prompt(),
            prompt=build_facts_prompt(query, identity, status, verdict),
            max_tokens=300,
        )
        text = (text or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 — explanation is optional; never fail the verdict
        logger.warning("LLM explanation unavailable (%s); returning verdict without it", exc)
        return None
