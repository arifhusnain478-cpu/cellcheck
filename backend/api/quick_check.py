"""Quick Check — search a cell line and get a traffic-light verdict.

Flow: Cellosaurus identity -> ICLAC misidentification check -> verdict.
Retractions are left empty for now (Semantic Scholar is a later slice); next_steps
is a small static list grounded in the verdict.
"""
import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.quick_check import QuickCheckRequest, QuickCheckResponse
from services import demo_cache
from services.cellosaurus_client import (
    CellosaurusError,
    extract_source_lab,
    get_cell_line_with_entry,
)
from services.iclac_service import (
    ICLACStatus,
    check_misidentification,
    compute_verdict,
)
from services.crossref_client import find_related_papers
from services.verdict_explainer import explain

router = APIRouter()


@router.post("/quick", response_model=QuickCheckResponse)
async def quick(req: QuickCheckRequest):
    try:
        resolved = await get_cell_line_with_entry(req.query)
    except CellosaurusError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": {
                "code": "UPSTREAM_SERVICE_UNAVAILABLE",
                "message": f"Cellosaurus is currently unavailable: {exc}",
                "details": None,
            }},
        )

    if resolved is None:
        return JSONResponse(
            status_code=404,
            content={"error": {
                "code": "CELL_LINE_NOT_FOUND",
                "message": (
                    f"No cell line matching '{req.query}' was found. "
                    "Check the spelling, or try a catalog number or RRID (e.g. CVCL_0031)."
                ),
                "details": None,
            }},
        )

    identity, entry = resolved
    if identity.rrid:
        status = check_misidentification(identity.rrid)
    else:
        status = ICLACStatus(accession="", on_register=False, status="not_listed")
    verdict = compute_verdict(status, identity_found=True)

    # DEMO_MODE: pin the two LLM-generated fields to pre-approved text for a
    # byte-stable recording. The verdict, identity, and retractions still run live.
    demo = demo_cache.quick_demo(identity.rrid) if demo_cache.demo_mode_enabled() else None
    if demo is not None:
        source_lab, explanation = demo.get("source_lab"), demo.get("explanation")
    else:
        # source_lab (from Cellosaurus data) and the verdict explanation are two
        # independent, grounded LLM calls — run them together to cut cold-path latency.
        # Both are best-effort (return None on LLM failure); the verdict stands regardless.
        source_lab, explanation = await asyncio.gather(
            extract_source_lab(entry),
            explain(req.query, identity, status, verdict),
        )
    identity = identity.model_copy(update={"source_lab": source_lab})

    # Only red lines get a Semantic Scholar lookup (saves API calls + latency).
    sources = ["cellosaurus", "iclac"]
    retractions: list = []
    if verdict == "red":
        retractions = await find_related_papers(identity.correct_name)
        if retractions:
            sources.append("crossref")

    return QuickCheckResponse(
        query=req.query,
        verdict=verdict,
        identity=identity,
        explanation=explanation,
        retractions=retractions,
        next_steps=_next_steps(verdict),
        sources=sources,
    )


def _next_steps(verdict: str) -> list[str]:
    steps = ["Order STR profiling before publication"]
    if verdict == "red":
        steps.append(
            "This line has documented misidentification — do not use without further verification"
        )
    elif verdict == "yellow":
        steps.append(
            "Authentic stock may exist — confirm your stock's provenance before use"
        )
    return steps
