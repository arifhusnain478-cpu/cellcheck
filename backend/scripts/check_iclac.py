"""Manual check for the ICLAC service + verdict (Slice 2) — end-to-end.

Pipeline per line: Cellosaurus (Slice 1) name -> accession -> ICLAC lookup -> verdict.
Hits the live Cellosaurus API; ICLAC is the local register. No LLM.

    python backend/scripts/check_iclac.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from services.cellosaurus_client import get_cell_line  # noqa: E402
from services.iclac_service import (  # noqa: E402
    ICLACStatus,
    check_misidentification,
    compute_verdict,
    register_meta,
)

DEMO = [
    ("HeLa", "CVCL_0030"),
    ("MCF-7", "MCF-7"),
    ("MDA-MB-435", "MDA-MB-435"),
    ("HEK293", "HEK293"),
    ("MDA-MB-231", "MDA-MB-231"),
]
EXPECTED = {"HeLa": "green", "MCF-7": "green", "MDA-MB-435": "red",
            "HEK293": "green", "MDA-MB-231": "green"}

_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"    [{'PASS' if condition else 'FAIL'}] {label}" + (f" - {detail}" if detail else ""))
    if not condition:
        _failures.append(label)


async def run_line(query: str):
    """Cellosaurus -> accession -> ICLAC -> verdict."""
    identity = await get_cell_line(query)
    if identity is None or not identity.rrid:
        status = ICLACStatus(accession="", on_register=False, status="not_listed")
        return None, status, compute_verdict(status, identity_found=False)
    status = check_misidentification(identity.rrid)
    verdict = compute_verdict(status, identity_found=True)
    return identity, status, verdict


async def main() -> int:
    meta = register_meta()
    print(f"ICLAC register: v{meta.get('version')} ({meta.get('released', 'n/a')}) — "
          f"{meta.get('counts', 'starter set')}\n")

    print("=== Verdicts for the 5 demo lines (Cellosaurus -> ICLAC -> verdict) ===")
    for label, query in DEMO:
        identity, status, verdict = await run_line(query)
        ac = identity.rrid if identity else "?"
        print(f"\n  {label}  ({ac})  ->  {verdict.upper()}")
        if identity:
            print(f"     cellosaurus identity: {identity.correct_name} — {identity.true_origin}")
        if status.on_register:
            print(f"     ICLAC: claimed {status.claimed_identity!r} but actually "
                  f"{status.true_identity!r} ({status.true_identity_accession}); "
                  f"reported {status.year_reported}; {status.source}")
        else:
            print("     ICLAC: not on the register")
        check(f"{label} verdict == {EXPECTED[label]}", verdict == EXPECTED[label], verdict)

    print("\n=== Yellow-path demonstrations ===")
    # (a) A real Table 2 line — misidentified but authentic stock exists -> caution.
    t2 = _first_table2_entry()
    if t2:
        status = check_misidentification(t2["accession"])
        verdict = compute_verdict(status, identity_found=True)
        print(f"\n  Table 2 line {t2['name']} ({t2['accession']})  ->  {verdict.upper()}")
        print(f"     authentic stock exists elsewhere; claimed {status.claimed_identity!r} "
              f"vs {status.true_identity!r}")
        check("table-2 line -> yellow", verdict == "yellow", verdict)
    else:
        print("\n  (no Table 2 entry available — full register not loaded)")

    # (b) A line that can't be resolved in Cellosaurus -> identity undetermined -> caution.
    identity, status, verdict = await run_line("Totally-Not-A-Real-Cell-Line-XYZ")
    print(f"\n  Unresolvable query  ->  {verdict.upper()}  (identity undetermined)")
    check("unresolvable line -> yellow", verdict == "yellow", verdict)

    print("\n" + "=" * 60)
    if _failures:
        print(f"RESULT: {len(_failures)} check(s) FAILED: {_failures}")
        return 1
    print("RESULT: all checks passed")
    return 0


def _first_table2_entry():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "iclac_register.json")
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for entry in data.get("entries", []):
        if entry.get("table") == 2 and entry.get("accession"):
            return entry
    return None


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
