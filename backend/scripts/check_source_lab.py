"""Manual check for source_lab extraction — all 5 demo lines.

Grounded LLM extraction of the originating institution from Cellosaurus data.
Needs an LLM key (backend/.env).
"""
import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(_HERE, "..", ".env"))
load_dotenv(os.path.join(_HERE, "..", "..", ".env"))

from services.cellosaurus_client import extract_source_lab, get_cell_line_with_entry  # noqa: E402

LINES = ["HeLa", "MCF-7", "MDA-MB-435", "HEK293", "MDA-MB-231"]


async def main():
    print(f"LLM_PROVIDER={os.getenv('LLM_PROVIDER') or '(unset)'} | GROQ set={bool(os.getenv('GROQ_API_KEY'))}\n")
    for q in LINES:
        resolved = await get_cell_line_with_entry(q)
        if resolved is None:
            print(f"  {q:12} -> (not found)")
            continue
        _identity, entry = resolved
        lab = await extract_source_lab(entry)
        print(f"  {q:12} -> source_lab = {lab!r}")


if __name__ == "__main__":
    asyncio.run(main())
