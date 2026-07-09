"""Client for the Cellosaurus API — cell line identity and RRID lookup.

Public interface:
    await get_cell_line(query) -> Optional[Identity]
        Base identity (source_lab left None — see below).
    await get_cell_line_with_entry(query) -> Optional[tuple[Identity, dict]]
        Base identity plus the raw Cellosaurus entry, for callers that want to add
        the source_lab enrichment themselves (e.g. in parallel with other work).
    await extract_source_lab(entry) -> Optional[str]
        Grounded LLM extraction of the originating institution (cached per accession).

`query` may be a cell line name ("HeLa"), a catalog number ("HTB-22"), or an
RRID / Cellosaurus accession ("CVCL_0030", optionally "RRID:CVCL_0030").

Returns an `Identity` (see models.quick_check) or None if the line is not found.
Raises `CellosaurusError` on network failures or unexpected upstream responses.

Docs: https://api.cellosaurus.org/
"""
import re
from pathlib import Path
from typing import Optional

import httpx

from models.quick_check import Identity
from services.llm_client import get_llm_client
from utils import cache
from utils.logger import get_logger

logger = get_logger("cellcheck.cellosaurus")

BASE_URL = "https://api.cellosaurus.org"
TIMEOUT = 20.0
SEARCH_ROWS = 10

_SOURCE_LAB_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "source_lab_extraction.txt"
_source_lab_prompt: Optional[str] = None

# Cellosaurus accessions are "CVCL_" + 4 alphanumerics (e.g. CVCL_0030, CVCL_A4CI).
_RRID_RE = re.compile(r"^CVCL_[0-9A-Za-z]{4}$", re.IGNORECASE)


class CellosaurusError(RuntimeError):
    """Cellosaurus was unreachable or returned an unexpected (non-404) error."""


async def get_cell_line_with_entry(query: str) -> Optional[tuple[Identity, dict]]:
    """Resolve a query to (Identity, raw Cellosaurus entry), or None if not found.

    The Identity's ``source_lab`` is left None here — it's an LLM enrichment the caller
    adds via ``extract_source_lab`` (which can run in parallel with other work).
    """
    q = (query or "").strip()
    if not q:
        return None

    key = _cache_key(q)
    cached = cache.get(key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        entry = await _resolve(client, q)

    if entry is None:
        return None  # not found — don't cache (cache miss and None are indistinguishable)

    result = (_to_identity(entry), entry)
    cache.set(key, result)
    return result


async def get_cell_line(query: str) -> Optional[Identity]:
    """Resolve a query to an Identity (source_lab NOT populated — it's an optional LLM
    enrichment; use get_cell_line_with_entry + extract_source_lab when you need it)."""
    resolved = await get_cell_line_with_entry(query)
    return resolved[0] if resolved else None


# --- resolution --------------------------------------------------------------

async def _resolve(client: httpx.AsyncClient, q: str) -> Optional[dict]:
    """Route the query to the right endpoint and return the raw cell-line dict."""
    candidate = q[5:].strip() if q.lower().startswith("rrid:") else q
    if _RRID_RE.match(candidate):
        return await _get_by_accession(client, candidate.upper())
    return await _search_best(client, q)


async def _get_by_accession(client: httpx.AsyncClient, accession: str) -> Optional[dict]:
    try:
        resp = await client.get(f"/cell-line/{accession}", params={"format": "json"})
    except httpx.RequestError as exc:
        raise CellosaurusError(f"Network error contacting Cellosaurus: {exc}") from exc
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise CellosaurusError(f"Cellosaurus returned HTTP {resp.status_code} for {accession}")
    lines = _cell_lines(resp)
    return lines[0] if lines else None


async def _search(client: httpx.AsyncClient, q: str, rows: int = SEARCH_ROWS) -> list[dict]:
    try:
        resp = await client.get(
            "/search/cell-line", params={"q": q, "format": "json", "rows": rows}
        )
    except httpx.RequestError as exc:
        raise CellosaurusError(f"Network error contacting Cellosaurus: {exc}") from exc
    if resp.status_code != 200:
        raise CellosaurusError(f"Cellosaurus search returned HTTP {resp.status_code} for {q!r}")
    return _cell_lines(resp)


async def _search_best(client: httpx.AsyncClient, q: str) -> Optional[dict]:
    """Resolve a name or catalog number to a single cell line.

    1. An exact identifier/synonym name match wins.
    2. Otherwise treat it as a catalog number and do a format-tolerant exact
       cross-reference match (see _resolve_catalog) — this handles CCL-2 / CCL2 /
       "ATCC CCL-2", and space-vs-hyphen forms like "ACC 305" (stored as "ACC-305").
    3. Otherwise fall back to the top relevance hit.
    """
    results = await _search(client, q)
    if results:
        score, best = _best_match(results, q)
        if score >= 2:  # exact identifier (3) or synonym (2) name match
            return best

    catalog = await _resolve_catalog(client, q, results or [])
    if catalog is not None:
        return catalog

    return results[0] if results else None


def _score(entry: dict, q_cf: str) -> int:
    """Higher is a better match: 3 identifier, 2 synonym, 1 cross-ref, 0 fuzzy."""
    score = 0
    for name in entry.get("name-list", []):
        if (name.get("value") or "").casefold() == q_cf:
            score = max(score, 3 if name.get("type") == "identifier" else 2)
    for xref in entry.get("xref-list", []):
        if (xref.get("accession") or "").casefold() == q_cf:
            score = max(score, 1)
    return score


def _best_match(results: list[dict], q: str) -> tuple[int, dict]:
    q_cf = q.casefold()
    best = max(results, key=lambda e: _score(e, q_cf))  # ties keep relevance order
    return _score(best, q_cf), best


# --- catalog-number resolution -----------------------------------------------

# Repository name that may prefix a catalog number ("ATCC CCL-2", "ATCC; CCL-2").
_REPO_PREFIX_RE = re.compile(
    r"^(ATCC|DSMZ|ECACC|JCRB|RIKEN|RCB|KCLB|CLS|ICLC|BCRC|TKG|IZSLER|KCB|CCTCC)\b[\s;:,\-]*",
    re.IGNORECASE,
)


def _norm_cat(value: str) -> str:
    """Normalize a catalog code for comparison: drop separators, upper-case."""
    return re.sub(r"[\s\-;_.]+", "", value or "").upper()


def _catalog_code(q: str) -> str:
    """Strip a leading repository name so 'ATCC; CCL-2' -> 'CCL-2'."""
    return _REPO_PREFIX_RE.sub("", (q or "").strip()).strip()


def _catalog_search_forms(code: str) -> list[str]:
    """Query forms to surface the owning line. Cellosaurus stores catalog numbers
    hyphenated, so a user's 'ACC 305' must also be tried as 'ACC-305'."""
    code = code.strip()
    variants = {code, re.sub(r"\s+", "-", code), re.sub(r"[-\s]+", " ", code)}
    m = re.match(r"^([A-Za-z]+)[\s\-]*(\d.*)$", code)  # CCL2 -> CCL-2
    if m:
        variants.add(f"{m.group(1)}-{m.group(2)}")
    forms = [f"dr:{v}" for v in sorted(variants)]
    forms.append(code)  # plain relevance fallback
    return forms


def _xref_match(results: list[dict], target: str) -> Optional[dict]:
    """First result with a cross-reference accession normalizing to `target`."""
    for entry in results:
        for xref in entry.get("xref-list", []):
            if _norm_cat(xref.get("accession", "")) == target:
                return entry
    return None


async def _resolve_catalog(client: httpx.AsyncClient, q: str,
                           prefetched: list[dict]) -> Optional[dict]:
    """Resolve a catalog number to its owning line via an exact cross-reference
    match, tolerant of format (CCL-2 / CCL2 / 'ATCC CCL-2', space vs hyphen)."""
    code = _catalog_code(q)
    target = _norm_cat(code)
    if not target or not any(ch.isdigit() for ch in target):
        return None  # doesn't look like a catalog number

    hit = _xref_match(prefetched, target)
    if hit is not None:
        return hit
    for form in _catalog_search_forms(code):
        hit = _xref_match(await _search(client, form), target)
        if hit is not None:
            return hit
    return None


def _cache_key(q: str) -> str:
    """Normalized cache key so catalog variants share a cached result
    (CCL-2, ATCC CCL-2, CCL2 all -> the same key)."""
    return "cellosaurus:" + _norm_cat(_catalog_code(q)).lower()


# --- parsing -----------------------------------------------------------------

def _to_identity(entry: dict) -> Identity:
    names = entry.get("name-list", [])
    name = next((n["value"] for n in names if n.get("type") == "identifier"), None)
    synonyms = [n["value"] for n in names if n.get("type") == "synonym"]
    rrid = next(
        (a["value"] for a in entry.get("accession-list", []) if a.get("type") == "primary"),
        None,
    )
    species = _clean_species(
        next((s.get("label") for s in entry.get("species-list", []) if s.get("label")), None)
    )
    diseases = [d["label"] for d in entry.get("disease-list", []) if d.get("label")]
    return Identity(
        correct_name=name or rrid or "Unknown",
        rrid=rrid,
        true_origin=_compose_origin(diseases, _first_site(entry)),
        species=species,
        synonyms=synonyms,
        # source_lab is an optional LLM enrichment added by the caller (see
        # extract_source_lab), not part of the base identity. Cellosaurus has no
        # structured originating-lab field, so it's derived (grounded) from the
        # expanded-name synonym / comments.
        source_lab=None,
    )


def _clean_species(label: Optional[str]) -> Optional[str]:
    # "Homo sapiens (Human)" -> "Homo sapiens"
    return label.split(" (")[0].strip() if label else None


def _first_site(entry: dict) -> Optional[str]:
    for item in entry.get("derived-from-site-list", []):
        value = (item.get("site") or {}).get("value")
        if value:
            return value
    return None


def _compose_origin(diseases: list[str], site: Optional[str]) -> Optional[str]:
    diseases_text = "; ".join(diseases)
    if diseases_text and site:
        return f"{diseases_text} (derived from {site})"
    if diseases_text:
        return diseases_text
    if site:
        return f"Derived from {site}"
    return None


# --- source lab extraction (LLM, grounded) -----------------------------------

def _load_source_lab_prompt() -> str:
    global _source_lab_prompt
    if _source_lab_prompt is None:
        _source_lab_prompt = _SOURCE_LAB_PROMPT_PATH.read_text(encoding="utf-8")
    return _source_lab_prompt


def _source_lab_facts(entry: dict) -> str:
    """Grounding text: name + synonyms (the expanded name often names the institution)
    + comments. Only these are given to the LLM."""
    names = entry.get("name-list", [])
    name = next((n["value"] for n in names if n.get("type") == "identifier"), "")
    synonyms = [n["value"] for n in names if n.get("type") == "synonym"]
    comments = [
        f"[{c.get('category')}] {str(c.get('value'))[:200]}"
        for c in entry.get("comment-list", [])
    ]

    lines = [f"Cell line name: {name}",
             "Synonyms (may include the fully spelled-out name):"]
    lines += [f"  - {s}" for s in synonyms] or ["  (none)"]
    if comments:
        lines.append("Comments:")
        lines += [f"  - {c}" for c in comments]
    lines.append("")
    lines.append("Originating institution / laboratory (name only, or NONE):")
    return "\n".join(lines)


async def extract_source_lab(entry: dict) -> Optional[str]:
    """Derive the originating institution from Cellosaurus data via a grounded LLM
    call (cached per accession). Returns None if not clearly present or if the LLM is
    unavailable. Safe to run in parallel with other work (never raises)."""
    accession = next(
        (a["value"] for a in entry.get("accession-list", []) if a.get("type") == "primary"),
        None,
    )
    cache_key = f"source_lab:{accession}" if accession else None
    if cache_key is not None:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached or None  # "" is the cached-None sentinel

    try:
        client = get_llm_client()
        text = await client.complete(
            system=_load_source_lab_prompt(),
            prompt=_source_lab_facts(entry),
            max_tokens=40,
        )
    except Exception as exc:  # noqa: BLE001 — enrichment must not break identity lookup
        logger.warning("source_lab extraction unavailable (%s)", exc)
        return None  # transient failure — don't cache, so it can retry later

    result = (text or "").strip().strip('"').strip()
    if not result or result.upper() == "NONE" or len(result) > 120:
        result = None
    if cache_key is not None:
        cache.set(cache_key, result or "")  # cache the resolved answer, including None
    return result


def _cell_lines(resp: httpx.Response) -> list[dict]:
    return resp.json().get("Cellosaurus", {}).get("cell-line-list", []) or []
