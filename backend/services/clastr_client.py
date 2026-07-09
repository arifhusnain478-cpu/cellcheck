"""Client for CLASTR — the Cellosaurus STR similarity search.

CLASTR compares a submitted STR profile against Cellosaurus reference profiles.

API (reverse-engineered from the CLASTR web app):
    POST https://www.cellosaurus.org/str-search/api/query
    JSON body is a FLAT dict: marker name -> comma-joined allele string
    (e.g. {"D16S539": "11,12"}), plus outputFormat/species/algorithm/... params.
    Response: {"results": [{accession, name, bestScore, problematic, profiles:[...]}]}.

Public interface:
    await search(str_profile) -> list[dict]        # raw CLASTR results (ranked)
    analyze(results, claimed_identity) -> ClastrAnalysis
"""
import re
from typing import Optional

import httpx
from pydantic import BaseModel

from models.quick_check import Verdict  # "green" | "yellow" | "red"
from utils.logger import get_logger

logger = get_logger("cellcheck.clastr")

CLASTR_URL = "https://www.cellosaurus.org/str-search/api/query"
DEFAULT_SPECIES = "Homo sapiens (Human)"
TIMEOUT = 60.0
# ANSI ASN-0002 / ICLAC convention: Tanabe score >= 80% indicates the same line.
MATCH_THRESHOLD = 80.0


class ClastrError(RuntimeError):
    """CLASTR was unreachable or returned an unexpected response."""


class ClastrAnalysis(BaseModel):
    match_verdict: Verdict
    match_percentage: float
    matched_name: Optional[str] = None
    matched_accession: Optional[str] = None
    matched_consistent: bool = False  # does the matched line agree with the claimed identity?
    total_loci: int = 0
    matching_loci: int = 0
    anomalous_loci: list[str] = []


async def search(
    str_profile: dict[str, list[str]],
    *,
    species: str = DEFAULT_SPECIES,
    score_filter: int = 60,
    max_results: int = 10,
) -> list[dict]:
    """Submit an STR profile to CLASTR and return the ranked result list."""
    markers = {}
    for locus, alleles in str_profile.items():
        value = ",".join(a.strip() for a in alleles if a and a.strip())
        if value:
            markers[locus.strip()] = value
    if not markers:
        return []

    payload = {
        "outputFormat": "json",
        "species": species,
        "algorithm": "1",        # 1 = Tanabe (default)
        "scoringMode": "1",
        "scoreFilter": str(score_filter),
        "minMarkers": str(min(8, len(markers))),
        "maxResults": str(max_results),
        "includeAmelogenin": False,
        **markers,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                CLASTR_URL, json=payload,
                headers={"User-Agent": "CellCheck", "Content-Type": "application/json"},
            )
    except httpx.RequestError as exc:
        raise ClastrError(f"Network error contacting CLASTR: {exc}") from exc
    if resp.status_code != 200:
        raise ClastrError(f"CLASTR returned HTTP {resp.status_code}")
    try:
        return resp.json().get("results", []) or []
    except ValueError as exc:
        raise ClastrError("CLASTR returned a non-JSON response") from exc


def analyze(results: list[dict], claimed_identity: str) -> ClastrAnalysis:
    """Turn ranked CLASTR results into a verdict + loci breakdown.

    green  — top match >= 80% AND the top line agrees with the claimed identity
    red    — top match >= 80% but it is a DIFFERENT line than claimed (misID/contam)
    yellow — no confident match (top < 80%)
    """
    if not results:
        return ClastrAnalysis(match_verdict="yellow", match_percentage=0.0)

    top = results[0]
    top_score = float(top.get("bestScore") or 0.0)
    top_consistent = _consistent(claimed_identity, top.get("name", ""))

    if top_score >= MATCH_THRESHOLD:
        verdict: Verdict = "green" if top_consistent else "red"
    else:
        verdict = "yellow"

    # For a confirmed match, report the line that best equals the claim (prefer the
    # canonical line over a derivative); otherwise report the top hit (the contaminant).
    chosen = (_exact_match(results, claimed_identity) or top) if verdict == "green" else top
    total, matching, anomalous = _loci(chosen)

    return ClastrAnalysis(
        match_verdict=verdict,
        match_percentage=float(chosen.get("bestScore") or top_score),
        matched_name=chosen.get("name"),
        matched_accession=chosen.get("accession"),
        matched_consistent=_consistent(claimed_identity, chosen.get("name", "")),
        total_loci=total,
        matching_loci=matching,
        anomalous_loci=anomalous,
    )


# --- helpers -----------------------------------------------------------------

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _consistent(claimed: str, name: str) -> bool:
    c, n = _norm(claimed), _norm(name)
    return bool(c) and (c in n or n in c)


def _exact_match(results: list[dict], claimed: str) -> Optional[dict]:
    c = _norm(claimed)
    return next((r for r in results if _norm(r.get("name", "")) == c), None)


def _loci(result: dict) -> tuple[int, int, list[str]]:
    profiles = result.get("profiles") or []
    if not profiles:
        return 0, 0, []
    markers = profiles[0].get("markers") or []
    # scoring loci = markers that were in the query, excluding the Amelogenin sex marker
    scoring = [m for m in markers if m.get("searched") and m.get("name") != "Amelogenin"]
    anomalous = [
        m.get("name") for m in scoring
        if not all(a.get("matched") for a in (m.get("alleles") or []))
    ]
    total = len(scoring)
    return total, total - len(anomalous), [a for a in anomalous if a]
