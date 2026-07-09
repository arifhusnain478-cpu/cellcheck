"""Manual check for the LLM explanation layer (Slice: verdict explanation).

Runs the real pipeline (Cellosaurus -> ICLAC -> verdict) then asks the configured
LLM provider to phrase a grounded explanation, and prints it for review.

Requires an LLM provider + key in the environment, e.g.:
    LLM_PROVIDER=groq GROQ_API_KEY=... python backend/scripts/check_explanation.py

Hard grounding check: flags any year in the explanation that is NOT in the source
facts (the classic hallucination). HeLa's facts contain no year, so any year there
is invented.
"""
import asyncio
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Load keys from a gitignored .env (backend/.env preferred, then project-root .env)
# so the key never has to be pasted into the shell/transcript.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(_HERE, "..", ".env"))          # cellcheck/backend/.env
load_dotenv(os.path.join(_HERE, "..", "..", ".env"))    # cellcheck/.env

from services.cellosaurus_client import get_cell_line  # noqa: E402
from services.iclac_service import check_misidentification, compute_verdict  # noqa: E402
from services.verdict_explainer import build_facts_prompt, explain  # noqa: E402

# query -> years that are legitimately present in that line's facts (all others = hallucinated)
CASES = [
    ("MDA-MB-435", {"2002"}),
    ("HeLa", set()),
]

_issues: list[str] = []


async def run(query: str, allowed_years: set[str]):
    print("\n" + "=" * 68)
    print(f"QUERY: {query}")
    identity = await get_cell_line(query)
    if identity is None:
        print("  not found"); return
    status = check_misidentification(identity.rrid) if identity.rrid else None
    verdict = compute_verdict(status, identity_found=True)
    print(f"  verdict: {verdict}")

    prompt = build_facts_prompt(query, identity, status, verdict)
    print("\n  --- FACTS SENT TO LLM ---")
    print("  " + prompt.replace("\n", "\n  "))

    text = await explain(query, identity, status, verdict)
    print("\n  --- LLM EXPLANATION ---")
    if not text:
        print("  (none — LLM unavailable; set LLM_PROVIDER + <PROVIDER>_API_KEY)")
        return
    print("  " + text.replace("\n", "\n  "))

    # hard grounding check: any year not in the source facts is invented
    years = set(re.findall(r"\b(?:19\d{2}|20\d{2})\b", text))
    invented = years - allowed_years
    if invented:
        _issues.append(f"{query}: invented year(s) {sorted(invented)} not in facts")
        print(f"  [GROUNDING WARNING] years in output {sorted(years)}, "
              f"allowed {sorted(allowed_years)} -> invented {sorted(invented)}")
    else:
        print("  [grounding] no invented years")


async def main() -> int:
    print(f"LLM_PROVIDER={os.getenv('LLM_PROVIDER') or '(unset -> anthropic default)'} | "
          f"GROQ_API_KEY set={bool(os.getenv('GROQ_API_KEY'))} | "
          f"ANTHROPIC_API_KEY set={bool(os.getenv('ANTHROPIC_API_KEY'))}")
    for query, allowed in CASES:
        await run(query, allowed)

    print("\n" + "=" * 68)
    if _issues:
        print("GROUNDING ISSUES FOUND — tighten the prompt:")
        for i in _issues:
            print(f"  - {i}")
        return 1
    print("No invented-year grounding issues detected. Review the text above for accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
