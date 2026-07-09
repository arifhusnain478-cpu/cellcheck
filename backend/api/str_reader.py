"""STR Test Reader — interpret an uploaded STR profile.

Flow: CLASTR similarity search -> deterministic match verdict + loci breakdown ->
LLM-phrased interpretation grounded in the CLASTR data.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.str_reader import (
    LociAnalysis,
    MatchedLine,
    STRReaderRequest,
    STRReaderResponse,
)
from services import demo_cache
from services.clastr_client import ClastrAnalysis, ClastrError, MATCH_THRESHOLD, analyze, search
from services.str_interpreter import interpret

router = APIRouter()


@router.post("/str-analysis", response_model=STRReaderResponse)
async def str_analysis(req: STRReaderRequest):
    if not req.str_profile:
        return JSONResponse(
            status_code=400,
            content={"error": {
                "code": "INVALID_STR_FORMAT",
                "message": "No STR markers provided. Paste at least a few locus:allele lines "
                           "(e.g. 'D5S818: 11,12').",
                "details": None,
            }},
        )

    try:
        results = await search(req.str_profile)
    except ClastrError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": {
                "code": "UPSTREAM_SERVICE_UNAVAILABLE",
                "message": f"CLASTR STR matching is currently unavailable: {exc}",
                "details": None,
            }},
        )

    analysis = analyze(results, req.claimed_identity)

    # DEMO_MODE: pin only the LLM interpretation (match %/loci come live from CLASTR).
    interpretation = None
    if demo_cache.demo_mode_enabled():
        interpretation = demo_cache.str_demo(req.claimed_identity, analysis.matched_accession)
    if interpretation is None:
        interpretation = await interpret(req.claimed_identity, analysis)

    return STRReaderResponse(
        match_verdict=analysis.match_verdict,
        match_percentage=round(analysis.match_percentage, 1),
        matched_line=MatchedLine(
            name=analysis.matched_name or "No confident match",
            rrid=analysis.matched_accession,
        ),
        loci_analysis=LociAnalysis(
            total_loci=analysis.total_loci,
            matching_loci=analysis.matching_loci,
            anomalous_loci=analysis.anomalous_loci,
        ),
        interpretation=interpretation or _fallback_interpretation(req.claimed_identity, analysis),
        recommendation=_recommendation(req.claimed_identity, analysis),
        sources=["clastr", "cellosaurus"],
    )


def _fallback_interpretation(claimed: str, a: ClastrAnalysis) -> str:
    pct = round(a.match_percentage)
    if a.match_verdict == "green":
        return (f"The submitted profile matches {a.matched_name} at {pct}% similarity, "
                f"consistent with the claimed identity {claimed}.")
    if a.match_verdict == "red":
        return (f"The submitted profile matches {a.matched_name} ({pct}%), not {claimed} — "
                f"the sample appears misidentified or cross-contaminated.")
    return (f"No reference profile matched above the {int(MATCH_THRESHOLD)}% threshold "
            f"(best {pct}%); the result is inconclusive.")


def _recommendation(claimed: str, a: ClastrAnalysis) -> str:
    if a.match_verdict == "green":
        base = "Consistent with the claimed identity. Safe to use; re-test from a low-passage stock for critical work."
        if a.anomalous_loci:
            base += " Minor locus differences may reflect passage-related drift."
        return base
    if a.match_verdict == "red":
        return (f"Do not use as {claimed} — the STR profile matches {a.matched_name}. "
                "Re-authenticate and trace the stock's origin before further use.")
    return ("Inconclusive. Re-run STR profiling on a fresh sample and check for "
            "contamination or a mixed-cell population.")
