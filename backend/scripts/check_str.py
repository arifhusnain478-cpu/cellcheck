"""Manual check for the STR Test Reader pipeline (Mode 2) — end-to-end.

Pulls real reference STR profiles from Cellosaurus, runs CLASTR search -> analyze
-> LLM interpretation, and prints results for three scenarios:
  1. MCF-7 profile claimed as MCF-7            -> expect green (confirmed match)
  2. HeLa profile claimed as MCF-7 (contam.)   -> expect red (matches HeLa, not MCF-7)
  3. MCF-7 profile with one altered allele      -> expect green with a differing locus

Needs an LLM key for the interpretation text:
    LLM_PROVIDER=groq GROQ_API_KEY=... (or backend/.env)
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

import httpx  # noqa: E402

from services.clastr_client import analyze, search  # noqa: E402
from services.str_interpreter import interpret  # noqa: E402

# a realistic user paste: core CODIS/ESS markers
CORE = {"Amelogenin", "CSF1PO", "D13S317", "D16S539", "D5S818", "D7S820", "TH01",
        "TPOX", "vWA", "D3S1358", "D8S1179", "D18S51", "D21S11", "FGA", "D2S1338", "D19S433"}

_failures: list[str] = []


def profile_from_cellosaurus(ac: str) -> dict[str, list[str]]:
    cl = httpx.get(f"https://api.cellosaurus.org/cell-line/{ac}",
                   params={"format": "json"}, timeout=30).json()["Cellosaurus"]["cell-line-list"][0]
    out: dict[str, list[str]] = {}
    for m in cl.get("str-list", {}).get("marker-list", []):
        mid = m.get("id")
        md = m.get("marker-data-list", [])
        if mid in CORE and md:
            alleles = (md[0].get("marker-alleles") or "").split(",")
            out[mid] = [a.strip() for a in alleles if a.strip()]
    return out


async def scenario(title: str, profile: dict, claimed: str, expect: str):
    print("\n" + "=" * 70)
    print(f"{title}\n  claimed = {claimed!r}, {len(profile)} loci submitted")
    results = await search(profile)
    a = analyze(results, claimed)
    print(f"  verdict: {a.match_verdict}  |  match: {a.matched_name} ({a.matched_accession}) "
          f"{round(a.match_percentage)}%")
    print(f"  loci: {a.matching_loci}/{a.total_loci} matching; "
          f"differing: {a.anomalous_loci or 'none'}")
    text = await interpret(claimed, a)
    print(f"  interpretation: {text or '(LLM unavailable)'}")
    ok = a.match_verdict == expect
    print(f"  [{'PASS' if ok else 'FAIL'}] expected {expect}, got {a.match_verdict}")
    if not ok:
        _failures.append(title)
    return a


async def main() -> int:
    print(f"LLM_PROVIDER={os.getenv('LLM_PROVIDER') or '(unset)'} | "
          f"GROQ_API_KEY set={bool(os.getenv('GROQ_API_KEY'))}")

    mcf7 = profile_from_cellosaurus("CVCL_0031")
    hela = profile_from_cellosaurus("CVCL_0030")

    await scenario("1) MCF-7 profile, claimed MCF-7", mcf7, "MCF-7", "green")
    await scenario("2) HeLa profile, claimed MCF-7 (contamination)", hela, "MCF-7", "red")

    drifted = dict(mcf7)
    if "TH01" in drifted:
        drifted["TH01"] = ["9.3"]  # deliberately wrong allele
    a3 = await scenario("3) MCF-7 profile with altered TH01, claimed MCF-7", drifted, "MCF-7", "green")
    if a3.match_verdict == "green" and "TH01" not in a3.anomalous_loci:
        print("  [note] expected TH01 to show as a differing locus")

    print("\n" + "=" * 70)
    if _failures:
        print(f"RESULT: {len(_failures)} FAILED: {_failures}")
        return 1
    print("RESULT: all verdict checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
