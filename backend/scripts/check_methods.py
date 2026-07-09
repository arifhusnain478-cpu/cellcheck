"""Manual check for the Methods Generator (Mode 3) — end-to-end.

Cellosaurus RRID -> journal policy/compliance -> LLM methods paragraph.
Needs an LLM key (backend/.env) for the paragraph text.
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
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(_HERE, "..", ".env"))
load_dotenv(os.path.join(_HERE, "..", "..", ".env"))

from models.methods import MethodsRequest  # noqa: E402
from services.cellosaurus_client import get_cell_line  # noqa: E402
from services.journal_policies import missing_field_labels, resolve_policy  # noqa: E402
from services.methods_writer import write_methods  # noqa: E402

_failures: list[str] = []


def check(label, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" - {detail}" if detail else ""))
    if not cond:
        _failures.append(label)


async def run(title, req: MethodsRequest, expect_listed: bool, allowed_years: set[str]):
    print("\n" + "=" * 72)
    print(title)
    identity = await get_cell_line(req.cell_line)
    if identity is None:
        check("cell line resolved", False, "None"); return
    policy = resolve_policy(req.target_journal)
    missing = missing_field_labels(req, policy)
    para = await write_methods(req, identity)

    print(f"  rrid_used: {identity.rrid}")
    print(f"  policy: {policy.name} (listed={policy.listed})  compliant={not missing}  missing={missing}")
    print(f"  paragraph:\n    {(para or '(LLM unavailable)')}")

    check("policy listed flag", policy.listed == expect_listed, f"{policy.listed}")
    if para:
        check("paragraph cites correct RRID", (identity.rrid or '') in para, identity.rrid)
        check("paragraph names the line", req.cell_line.replace('-', '') in para.replace('-', ''))
        years = set(re.findall(r"\b(?:19|20)\d{2}\b", para))
        invented = years - allowed_years
        check("no invented years", not invented, f"years={sorted(years)} invented={sorted(invented)}")
    return policy, missing


async def main() -> int:
    print(f"LLM_PROVIDER={os.getenv('LLM_PROVIDER') or '(unset)'} | GROQ set={bool(os.getenv('GROQ_API_KEY'))}")

    full = MethodsRequest(
        cell_line="MCF-7", source="ATCC (HTB-22)",
        authentication_date="2026-05-10", authentication_service="ATCC STR profiling service",
        mycoplasma_test_date="2026-05-08", passage_range="8-15", target_journal="Cancer Research",
    )
    await run("1) MCF-7 -> Cancer Research (complete)", full, expect_listed=True, allowed_years={"2026"})

    # missing passage_range -> Cancer Research requires it -> should be flagged
    incomplete = full.model_copy(update={"passage_range": None})
    _, missing = await run("2) MCF-7 -> Cancer Research (missing passage range)",
                           incomplete, expect_listed=True, allowed_years={"2026"})
    check("missing passage range flagged", any("passage" in m for m in missing), str(missing))

    # unlisted journal -> generic fallback
    elife = full.model_copy(update={"target_journal": "eLife"})
    await run("3) MCF-7 -> eLife (unlisted -> generic fallback)", elife,
              expect_listed=False, allowed_years={"2026"})

    print("\n" + "=" * 72)
    if _failures:
        print(f"RESULT: {len(_failures)} FAILED: {_failures}")
        return 1
    print("RESULT: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
