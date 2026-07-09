"""Capture pre-approved LLM text for the demo cache (data/demo_cache.json).

Runs the LIVE pipeline (backend must be up with DEMO_MODE off) for the 5 Quick
Check demo lines, the 2 STR scenarios, and the 1 Methods example, then freezes the
grounded LLM-generated text into data/demo_cache.json. Review the printed output
before trusting it — this pins whatever the model said on this run.

Usage (from backend/):
    python scripts/build_demo_cache.py
"""
import asyncio
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

import httpx  # noqa: E402

from services.demo_cache import methods_key, str_key  # noqa: E402

BASE = os.getenv("CELLCHECK_API", "http://127.0.0.1:8000") + "/api/cellcheck"
OUT = os.path.join(_HERE, "..", "data", "demo_cache.json")

# Quick Check demo lines and the accession each MUST resolve to (sanity check).
QUICK_LINES = {
    "HeLa": "CVCL_0030",
    "MCF-7": "CVCL_0031",
    "MDA-MB-435": "CVCL_0417",
    "HEK293": "CVCL_0045",
    "MDA-MB-231": "CVCL_0062",
}

# STR scenarios (mirror the frontend example buttons exactly).
STR_MCF7_PROFILE = {
    "Amelogenin": ["X"], "CSF1PO": ["10"], "D13S317": ["11"], "D16S539": ["11", "12"],
    "D5S818": ["11", "12"], "D7S820": ["8", "9"], "TH01": ["6"], "TPOX": ["9", "12"],
    "vWA": ["14", "15"],
}
STR_HELA_AS_MCF7_PROFILE = {
    "Amelogenin": ["X"], "CSF1PO": ["9", "10"], "D13S317": ["12"], "D16S539": ["9", "10"],
    "D5S818": ["11", "12"], "D7S820": ["8", "12"], "TH01": ["7"], "TPOX": ["8", "12"],
    "vWA": ["16", "18"],
}
STR_SCENARIOS = [
    ("MCF-7 match", "MCF-7", STR_MCF7_PROFILE),
    ("HeLa-as-MCF-7 contamination", "MCF-7", STR_HELA_AS_MCF7_PROFILE),
]

# Methods example (mirrors the frontend "Load MCF-7 example" button).
METHODS_EXAMPLE = {
    "cell_line": "MCF-7",
    "source": "ATCC (HTB-22)",
    "authentication_service": "ATCC STR profiling service",
    "authentication_date": "2026-05-10",
    "mycoplasma_test_date": "2026-05-08",
    "passage_range": "8-15",
    "target_journal": "Cancer Research",
}


async def main():
    cache = {"quick_check": {}, "str_demo_cache": {}, "methods_demo_cache": {}}
    async with httpx.AsyncClient(timeout=120) as client:
        # --- Quick Check ---
        print("== Quick Check ==")
        for name, expected in QUICK_LINES.items():
            r = (await client.post(f"{BASE}/quick", json={"query": name})).json()
            rrid = r["identity"]["rrid"]
            flag = "OK" if rrid == expected else f"!! expected {expected}"
            cache["quick_check"][rrid] = {
                "explanation": r["explanation"],
                "source_lab": r["identity"]["source_lab"],
            }
            print(f"  {name:12} -> {rrid} [{flag}] verdict={r['verdict']} "
                  f"source_lab={r['identity']['source_lab']!r}")
            print(f"      {r['explanation'][:110]}...")

        # --- STR Reader ---
        print("\n== STR Reader ==")
        for label, claimed, profile in STR_SCENARIOS:
            r = (await client.post(f"{BASE}/str-analysis",
                                   json={"claimed_identity": claimed, "str_profile": profile})).json()
            matched = r["matched_line"]["rrid"]
            key = str_key(claimed, matched)
            cache["str_demo_cache"][key] = {"interpretation": r["interpretation"]}
            print(f"  {label:32} key={key} verdict={r['match_verdict']} "
                  f"{round(r['match_percentage'])}% -> {r['matched_line']['name']}")
            print(f"      {r['interpretation'][:110]}...")

        # --- Methods Generator ---
        print("\n== Methods Generator ==")
        r = (await client.post(f"{BASE}/methods-section", json=METHODS_EXAMPLE)).json()
        rrid = r["rrid_used"]
        key = methods_key(rrid, METHODS_EXAMPLE["target_journal"])
        cache["methods_demo_cache"][key] = {"methods_paragraph": r["methods_paragraph"]}
        print(f"  MCF-7 / Cancer Research  key={key} rrid={rrid}")
        print(f"      {r['methods_paragraph'][:140]}...")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(f"\nWrote {os.path.abspath(OUT)}")


if __name__ == "__main__":
    asyncio.run(main())
