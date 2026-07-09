"""Client for the Crossref REST API — find retracted / related papers.

Used for red-verdict lines in Quick Check: searches for papers about the line's
misidentification (more relevant than papers that merely used the line). Crossref is
free, needs no API key, and includes Retraction Watch data. Set CROSSREF_MAILTO to use
the faster "polite pool".

Never raises — returns [] on error or no results, so /quick never fails because of it.
Docs: https://api.crossref.org/
"""
import asyncio
import html
import os
import re
from typing import Optional

import httpx

from utils import cache
from utils.logger import get_logger

logger = get_logger("cellcheck.crossref")

WORKS_URL = "https://api.crossref.org/works"
SELECT = "title,container-title,published,issued,URL,DOI,type,update-to"
TIMEOUT = 20.0
MAX_RESULTS = 10
QUERY_DELAY = 0.5  # seconds between the two queries

REASON_RETRACTED = "Retracted"
REASON_RELATED = "Related to cell line misidentification"

# Crossref work types that are noise for this purpose.
_SKIP_TYPES = {"reference-entry", "component", "dataset", "peer-review", "grant",
               "book", "book-set", "book-series"}
_RETRACT_UPDATE_TYPES = {"retraction", "removal", "withdrawal"}
_RELEVANT_RE = re.compile(r"misidentif|retract|contaminat", re.IGNORECASE)
_RETRACT_TITLE_RE = re.compile(r"^\s*(retraction|retracted|withdrawal)\b", re.IGNORECASE)


async def find_related_papers(cell_line_name: str) -> list[dict]:
    """Return up to 10 retracted/related papers for a (red-verdict) cell line.

    Each paper: {"title", "journal", "year", "reason", "url"}. Returns [] on any
    failure or no results — never raises.
    """
    name = (cell_line_name or "").strip()
    if not name:
        return []

    key = f"crossref:{name.casefold()}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    queries = [f"{name} misidentified", f"{name} retracted"]
    seen: dict[str, dict] = {}
    all_ok = True

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i, query in enumerate(queries):
            if i > 0:
                await asyncio.sleep(QUERY_DELAY)
            ok, items = await _search(client, query)
            all_ok &= ok
            for item in items:
                parsed = _parse(item)
                if parsed is None:
                    continue
                dedup_key = _norm_title(parsed["title"])
                if dedup_key and dedup_key not in seen:
                    seen[dedup_key] = parsed

    results = list(seen.values())
    # retracted first, then papers explicitly about misID/retraction/contamination,
    # then most recent.
    results.sort(key=lambda p: (
        p["reason"] != REASON_RETRACTED,
        not _RELEVANT_RE.search(p["title"] or ""),
        -(p.get("year") or 0),
    ))
    results = results[:MAX_RESULTS]

    if all_ok:
        cache.set(key, results)
    return results


async def _search(client: httpx.AsyncClient, query: str) -> tuple[bool, list[dict]]:
    params = {"query": query, "rows": MAX_RESULTS, "select": SELECT}
    mailto = os.getenv("CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    headers = {"User-Agent": f"CellCheck/0.1 (mailto:{mailto})" if mailto else "CellCheck/0.1"}
    try:
        resp = await client.get(WORKS_URL, params=params, headers=headers)
    except httpx.RequestError as exc:
        logger.warning("Crossref network error for %r: %s", query, exc)
        return False, []
    if resp.status_code != 200:
        logger.warning("Crossref HTTP %s for %r", resp.status_code, query)
        return False, []
    try:
        return True, (resp.json().get("message", {}).get("items") or [])
    except ValueError:
        return False, []


def _parse(item: dict) -> Optional[dict]:
    if item.get("type") in _SKIP_TYPES:
        return None
    titles = item.get("title") or []
    title = _clean(titles[0]) if titles else ""
    if not title:
        return None
    journals = item.get("container-title") or []
    journal_name = _clean(journals[0]) if journals else None
    updates = item.get("update-to") or []
    retracted = (
        any((u.get("type") or "").lower() in _RETRACT_UPDATE_TYPES for u in updates)
        or bool(_RETRACT_TITLE_RE.match(title))
    )
    doi = item.get("DOI")
    return {
        "title": title,
        "journal": journal_name or None,
        "year": _year(item),
        "reason": REASON_RETRACTED if retracted else REASON_RELATED,
        "url": item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
    }


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)   # strip inline markup (<i>, <sub>, ...)
    text = html.unescape(text)            # &amp; -> &
    return re.sub(r"\s+", " ", text).strip()


def _year(item: dict) -> Optional[int]:
    for field in ("published", "issued", "published-print", "published-online"):
        parts = (item.get(field) or {}).get("date-parts")
        if parts and parts[0] and parts[0][0]:
            return parts[0][0]
    return None


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())
