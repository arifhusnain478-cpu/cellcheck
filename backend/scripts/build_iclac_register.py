"""Build backend/data/iclac_register.json from the official ICLAC v14 xlsx.

Re-run this to refresh the local register when ICLAC publishes a new version.
Uses only the stdlib + httpx (no Excel dependency — an .xlsx is a zip of XML).

    python backend/scripts/build_iclac_register.py

Source: ICLAC Register of Misidentified Cell Lines
        https://iclac.org/databases/cross-contaminations/
"""
import io
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

import httpx

VERSION = "14"
RELEASED = "2026-02-15"
RETRIEVED = "2026-07-09"
PAGE_URL = "https://iclac.org/databases/cross-contaminations/"
DOWNLOAD_URL = "https://iclac.org/wp-content/uploads/Cross-Contaminations_v14_distribution.xlsx"

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "iclac_register.json")

_M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"m": _M}


def _col_to_idx(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.findall(".//m:t", NS))
            for si in root.findall("m:si", NS)]


def _rows_by_num(z: zipfile.ZipFile, path: str, shared: list[str]) -> dict[int, dict[int, str]]:
    root = ET.fromstring(z.read(path))
    out: dict[int, dict[int, str]] = {}
    for row in root.findall(".//m:sheetData/m:row", NS):
        cells: dict[int, str] = {}
        for c in row.findall("m:c", NS):
            ci = _col_to_idx(c.get("r"))
            v = c.find("m:v", NS)
            if v is None:
                continue
            cells[ci] = shared[int(v.text)] if c.get("t") == "s" else v.text
        out[int(row.get("r"))] = cells
    return out


def _table_for_sheet(z: zipfile.ZipFile, sheet_no: int) -> str | None:
    rels = ET.fromstring(z.read(f"xl/worksheets/_rels/sheet{sheet_no}.xml.rels"))
    for rel in rels.iter():
        target = rel.get("Target") or ""
        if "tables/table" in target:
            return "xl/" + target.replace("../", "")
    return None


def _clean(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _year_of(reported_by):
    if not reported_by:
        return None
    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", reported_by)]
    return min(years) if years else None


def _parse_table(z, shared, sheet_no: int, table_no: int) -> list[dict]:
    table_path = _table_for_sheet(z, sheet_no)
    tdef = ET.fromstring(z.read(table_path))
    ref = tdef.get("ref")  # e.g. "A29:L589"
    m = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", ref)
    start_col = _col_to_idx(m.group(1) + m.group(2))
    header_row, end_row = int(m.group(2)), int(m.group(4))
    names = [c.get("name") for c in tdef.findall("m:tableColumns/m:tableColumn", NS)]
    col = {name: start_col + i for i, name in enumerate(names)}

    rows = _rows_by_num(z, f"xl/worksheets/sheet{sheet_no}.xml", shared)

    def cell(r, name):
        return _clean(r.get(col[name])) if name in col else None

    entries = []
    for rn in range(header_row + 1, end_row + 1):
        r = rows.get(rn)
        if not r:
            continue
        name = cell(r, "Misidentified Cell Line")
        if not name:
            continue
        ac = cell(r, "Misidentified Cell Line, Cellosaurus AC")
        reported_by = cell(r, "Misidentification Reported By")
        entries.append({
            "accession": ac.upper() if ac and ac.upper().startswith("CVCL_") else ac,
            "name": name,
            "table": table_no,
            "claimed_species": cell(r, "Claimed Species"),
            "claimed_cell_type": cell(r, "Claimed Cell Type"),
            "contaminant_name": cell(r, "Contaminating Cell Line"),
            "actual_species": cell(r, "Actual Species"),
            "actual_cell_type": cell(r, "Actual Cell Type"),
            "contaminant_accession": cell(r, "Contaminating Cell Line, Cellosaurus AC"),
            "reported_by": reported_by,
            "year_reported": _year_of(reported_by),
            "pubmed_ids": cell(r, "Reference PubMed ID"),
            "authentic_stock_location": cell(r, "Authentic Stock Location"),  # table 2 only
        })
    return entries


def main() -> None:
    print(f"Downloading ICLAC v{VERSION} register ...")
    data = httpx.get(DOWNLOAD_URL, timeout=60, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0 (CellCheck)"}).content
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = _shared_strings(z)

    table1 = _parse_table(z, shared, sheet_no=1, table_no=1)  # misidentified, no authentic stock
    table2 = _parse_table(z, shared, sheet_no=2, table_no=2)  # authentic stock located
    entries = table1 + table2

    register = {
        "meta": {
            "source": "ICLAC Register of Misidentified Cell Lines",
            "version": VERSION,
            "released": RELEASED,
            "retrieved": RETRIEVED,
            "page_url": PAGE_URL,
            "download_url": DOWNLOAD_URL,
            "counts": {"table1_misidentified": len(table1),
                       "table2_authentic_stock_exists": len(table2)},
            "tables": {
                "1": "Misidentified / cross-contaminated, no verified authentic stock (verdict: red)",
                "2": "Misidentified but authentic stock has been located (verdict: yellow / caution)",
            },
            "note": ("Converted from the official v14 .xlsx via "
                     "backend/scripts/build_iclac_register.py. Always link to the ICLAC "
                     "page for the current version; do not treat this copy as canonical."),
        },
        "entries": entries,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(register, fh, indent=2, ensure_ascii=False)
    print(f"Wrote {len(entries)} entries "
          f"({len(table1)} misidentified + {len(table2)} authentic-stock) -> {OUT_PATH}")


if __name__ == "__main__":
    main()
