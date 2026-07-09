"""Manual check for the Cellosaurus client (Slice 1) — hits the live API.

Run from anywhere:
    python backend/scripts/check_cellosaurus.py
No LLM calls — Cellosaurus only.
"""
import asyncio
import os
import sys

# Make `services` / `models` importable no matter where this is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cell-line data (and our own output) can contain non-Latin-1 characters; keep
# printing on a Windows cp1252 console from crashing.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from services.cellosaurus_client import CellosaurusError, get_cell_line  # noqa: E402

EXPECTED_FIELDS = {"correct_name", "rrid", "true_origin", "species", "synonyms", "source_lab"}

_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"    [{status}] {label}" + (f" - {detail}" if detail else ""))
    if not condition:
        _failures.append(f"{label} ({detail})" if detail else label)


async def show(title: str, query: str):
    print(f"\n=== {title}  (query={query!r}) ===")
    identity = await get_cell_line(query)
    if identity is None:
        print("    -> not found (None)")
        return None
    print(identity.model_dump_json(indent=2))
    check("shape has exactly the contract fields",
          set(identity.model_dump().keys()) == EXPECTED_FIELDS,
          str(set(identity.model_dump().keys()) ^ EXPECTED_FIELDS) or "ok")
    check("synonyms is a list", isinstance(identity.synonyms, list))
    return identity


async def main() -> int:
    # --- core: the three demo lines -----------------------------------------
    hela = await show("HeLa via RRID", "CVCL_0030")
    if hela:
        check("HeLa name", hela.correct_name == "HeLa", hela.correct_name)
        check("HeLa RRID", hela.rrid == "CVCL_0030", str(hela.rrid))
        check("HeLa species is human", (hela.species or "").startswith("Homo sapiens"), str(hela.species))
        check("HeLa has a true origin", bool(hela.true_origin), str(hela.true_origin))
    else:
        check("HeLa resolved", False, "got None")

    mcf7 = await show("MCF-7 via name", "MCF-7")
    if mcf7:
        check("MCF-7 name", mcf7.correct_name == "MCF-7", mcf7.correct_name)
        check("MCF-7 RRID", mcf7.rrid == "CVCL_0031", str(mcf7.rrid))
    else:
        check("MCF-7 resolved", False, "got None")

    mda = await show("MDA-MB-435 via name", "MDA-MB-435")
    if mda:
        check("MDA-MB-435 RRID", mda.rrid == "CVCL_0417", str(mda.rrid))
        # The misidentification signal: Cellosaurus reports melanoma, not breast.
        check("MDA-MB-435 true origin is melanoma",
              "melanoma" in (mda.true_origin or "").lower(), str(mda.true_origin))
    else:
        check("MDA-MB-435 resolved", False, "got None")

    # --- extra: catalog-number path + not-found path ------------------------
    catalog = await show("Catalog number HTB-22 -> MCF-7", "HTB-22")
    if catalog:
        check("HTB-22 resolves to MCF-7", catalog.rrid == "CVCL_0031", str(catalog.rrid))
    else:
        check("HTB-22 resolved", False, "got None")

    missing = await show("Bogus RRID (not-found path)", "CVCL_ZZZZ")
    check("bogus RRID returns None", missing is None)

    print("\n" + "=" * 60)
    if _failures:
        print(f"RESULT: {len(_failures)} check(s) FAILED:")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print("RESULT: all checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except CellosaurusError as exc:
        print(f"\nCellosaurusError (network/upstream problem): {exc}")
        raise SystemExit(2)
