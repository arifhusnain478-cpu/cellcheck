"""Grounded, plain-language interpretation of a CLASTR STR-match result.

The match verdict is decided deterministically (clastr_client.analyze); the LLM
only phrases an interpretation of the facts. Best-effort: returns None on failure.
Grounding rules live in prompts/str_interpretation.txt.
"""
from pathlib import Path
from typing import Optional

from services.clastr_client import ClastrAnalysis
from services.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger("cellcheck.str_interpreter")

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "str_interpretation.txt"
_system_prompt: Optional[str] = None

_VERDICT_MEANING = {
    "green": "confirmed match to the claimed identity",
    "yellow": "inconclusive — no confident match",
    "red": "the profile matches a different line than claimed",
}


def _load_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    return _system_prompt


def build_facts_prompt(claimed_identity: str, a: ClastrAnalysis) -> str:
    matched = a.matched_name or "no reference line matched"
    if a.matched_accession:
        matched += f" ({a.matched_accession})"
    differing = ", ".join(a.anomalous_loci) if a.anomalous_loci else "none"
    return "\n".join([
        "FACTS (use only these — do not add anything else):",
        f"- Claimed identity: {claimed_identity}",
        f"- Match verdict (already decided, do not change): {a.match_verdict} = "
        f"{_VERDICT_MEANING.get(a.match_verdict, a.match_verdict)}",
        f"- Best-matching reference line (CLASTR, Tanabe similarity): {matched}",
        f"- Similarity to that line: {round(a.match_percentage)}%",
        f"- Does that best match agree with the claimed identity? "
        f"{'yes' if a.matched_consistent else 'no'}",
        f"- Loci compared: {a.total_loci}; loci fully matching: {a.matching_loci}; "
        f"differing loci: {differing}",
        "",
        "Write a 2-3 sentence plain-language interpretation of this result, "
        "using only the facts above.",
    ])


async def interpret(claimed_identity: str, analysis: ClastrAnalysis) -> Optional[str]:
    """Return a grounded interpretation, or None if the LLM is unavailable."""
    try:
        client = get_llm_client()
        text = await client.complete(
            system=_load_system_prompt(),
            prompt=build_facts_prompt(claimed_identity, analysis),
            max_tokens=300,
        )
        text = (text or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 — interpretation is best-effort
        logger.warning("LLM STR interpretation unavailable (%s)", exc)
        return None
