"""Lookup against the ICLAC Register of Misidentified Cell Lines.

The register is bundled locally as data/iclac_register.json (built from the
official v14 .xlsx by scripts/build_iclac_register.py). If that file is missing
or unreadable, a small hardcoded STARTER SET covering the demo lines is used so
the service still works.

Public interface:
    check_misidentification(cellosaurus_ac) -> ICLACStatus
    compute_verdict(status, identity_found=True) -> "green" | "yellow" | "red"

Register: https://iclac.org/databases/cross-contaminations/
"""
import json
import re
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel

from models.quick_check import Verdict
from utils.logger import get_logger

logger = get_logger("cellcheck.iclac")

REGISTER_PATH = Path(__file__).resolve().parent.parent / "data" / "iclac_register.json"

Status = Literal["misidentified", "authentic_stock_exists", "not_listed"]

# Hardcoded fallback — STARTER SET, used only if the bundled register JSON can't
# be loaded. Of our 5 demo lines only MDA-MB-435 is on the register; the other
# four (HeLa, MCF-7, HEK293, MDA-MB-231) are authentic and are correctly absent,
# which is itself their known ICLAC status (-> green).
_FALLBACK_REGISTER = {
    "meta": {
        "source": "ICLAC Register of Misidentified Cell Lines (hardcoded STARTER SET)",
        "version": "starter",
        "note": "Fallback — demo lines only. Run scripts/build_iclac_register.py for the full register.",
    },
    "entries": [
        {
            "accession": "CVCL_0417",
            "name": "MDA-MB-435",
            "table": 1,
            "claimed_cell_type": "Breast carcinoma",
            "contaminant_name": "M14",
            "actual_cell_type": "Melanoma",
            "contaminant_accession": "CVCL_1395",
            "reported_by": "Ellison et al, 2002; Rae et al, 2007",
            "year_reported": 2002,
            "pubmed_ids": "12354931, 17004106",
        },
    ],
}


class ICLACStatus(BaseModel):
    accession: str
    on_register: bool
    status: Status
    table: Optional[int] = None                 # 1 = misidentified, 2 = authentic stock exists
    name: Optional[str] = None
    claimed_identity: Optional[str] = None
    true_identity: Optional[str] = None
    true_identity_accession: Optional[str] = None
    year_reported: Optional[int] = None
    reported_by: Optional[str] = None
    pubmed_ids: list[str] = []
    source: str = "ICLAC Register"


# --- register loading (lazy, cached) -----------------------------------------

_index: Optional[dict[str, dict]] = None
_meta: dict = {}


def _load() -> dict[str, dict]:
    global _index, _meta
    if _index is not None:
        return _index

    data = None
    if REGISTER_PATH.exists():
        try:
            data = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read %s (%s); using STARTER SET fallback", REGISTER_PATH, exc)
    else:
        logger.warning("ICLAC register not found at %s; using STARTER SET fallback", REGISTER_PATH)

    if data is None:
        data = _FALLBACK_REGISTER

    _meta = data.get("meta", {})
    _index = {}
    for entry in data.get("entries", []):
        ac = (entry.get("accession") or "").upper()
        if ac:
            _index.setdefault(ac, entry)  # first occurrence wins
    logger.info("ICLAC register loaded: %d indexed entries (v%s)",
                len(_index), _meta.get("version", "?"))
    return _index


def register_meta() -> dict:
    _load()
    return dict(_meta)


def _source_label() -> str:
    version = _meta.get("version")
    return f"ICLAC Register v{version}" if version and version != "starter" \
        else "ICLAC Register (starter set)"


# --- public API --------------------------------------------------------------

def check_misidentification(cellosaurus_ac: str) -> ICLACStatus:
    """Return the ICLAC status for a Cellosaurus accession / RRID."""
    ac = _normalize(cellosaurus_ac)
    entry = _load().get(ac)

    if entry is None:
        return ICLACStatus(accession=ac, on_register=False, status="not_listed",
                           source=_source_label())

    table = int(entry.get("table") or 1)
    return ICLACStatus(
        accession=ac,
        on_register=True,
        status="misidentified" if table == 1 else "authentic_stock_exists",
        table=table,
        name=entry.get("name"),
        claimed_identity=entry.get("claimed_cell_type"),
        true_identity=_true_identity(entry),
        true_identity_accession=entry.get("contaminant_accession"),
        year_reported=entry.get("year_reported"),
        reported_by=entry.get("reported_by"),
        pubmed_ids=_split_ids(entry.get("pubmed_ids")),
        source=_source_label(),
    )


def compute_verdict(status: ICLACStatus, *, identity_found: bool = True) -> Verdict:
    """Traffic-light verdict grounded in the ICLAC register.

    red    — confirmed misidentified/cross-contaminated (register table 1)
    yellow — caution: authentic stock exists (table 2), or identity undetermined
    green  — not on the register (and the line was found)
    """
    if status.on_register:
        return "red" if status.table == 1 else "yellow"
    if not identity_found:
        return "yellow"
    return "green"


# --- helpers -----------------------------------------------------------------

def _normalize(ac: str) -> str:
    ac = (ac or "").strip()
    if ac.lower().startswith("rrid:"):
        ac = ac[5:].strip()
    return ac.upper()


def _true_identity(entry: dict) -> Optional[str]:
    name = entry.get("contaminant_name")
    cell_type = entry.get("actual_cell_type")
    if name and cell_type:
        return f"{name} ({cell_type})"
    return name or cell_type


def _split_ids(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[,;]", raw) if part.strip()]
