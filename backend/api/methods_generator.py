"""Methods Section Generator — produce a publication-ready methods paragraph.

Flow: fetch the authoritative RRID/identity from Cellosaurus -> check the target
journal's reporting requirements -> LLM writes the paragraph grounded in the form
inputs + fetched identity.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from models.methods import ComplianceStatus, MethodsRequest, MethodsResponse
from models.quick_check import Identity
from services import demo_cache
from services.cellosaurus_client import CellosaurusError, get_cell_line
from services.journal_policies import missing_field_labels, resolve_policy
from services.methods_writer import write_methods

router = APIRouter()


@router.post("/methods-section", response_model=MethodsResponse)
async def methods_section(req: MethodsRequest):
    # RRID accuracy is guaranteed by resolving the line against Cellosaurus.
    try:
        identity = await get_cell_line(req.cell_line)
    except CellosaurusError as exc:
        return JSONResponse(
            status_code=503,
            content={"error": {
                "code": "UPSTREAM_SERVICE_UNAVAILABLE",
                "message": f"Cellosaurus is currently unavailable: {exc}",
                "details": None,
            }},
        )
    if identity is None:
        return JSONResponse(
            status_code=404,
            content={"error": {
                "code": "CELL_LINE_NOT_FOUND",
                "message": (
                    f"No cell line matching '{req.cell_line}' was found, so an accurate RRID "
                    "cannot be cited. Check the spelling, or try a catalog number or RRID."
                ),
                "details": None,
            }},
        )

    policy = resolve_policy(req.target_journal)
    missing = missing_field_labels(req, policy)
    compliance = ComplianceStatus(
        journal=policy.name,
        compliant=(len(missing) == 0),
        missing_fields=missing,
    )

    # DEMO_MODE: pin the LLM paragraph (compliance + RRID stay live/deterministic).
    paragraph = None
    if demo_cache.demo_mode_enabled():
        paragraph = demo_cache.methods_demo(identity.rrid, req.target_journal)
    if paragraph is None:
        paragraph = await write_methods(req, identity)

    return MethodsResponse(
        methods_paragraph=paragraph or _fallback_paragraph(req, identity),
        compliance_status=compliance,
        rrid_used=identity.rrid,
        sources=["cellosaurus", "journal_policy_reference"],
    )


def _fallback_paragraph(req: MethodsRequest, identity: Identity) -> str:
    rrid = f" (RRID:{identity.rrid})" if identity.rrid else ""
    parts = [f"The {identity.correct_name} cell line{rrid} was used in this study."]
    if req.source:
        parts.append(f"Cells were obtained from {req.source}.")
    if req.authentication_service:
        clause = f"Cell line identity was authenticated by {req.authentication_service}"
        if req.authentication_date:
            clause += f" on {req.authentication_date}"
        parts.append(clause + ".")
    if req.mycoplasma_test_date:
        parts.append(
            f"Cells were confirmed negative for mycoplasma contamination on {req.mycoplasma_test_date}."
        )
    if req.passage_range:
        parts.append(f"Experiments were performed using cells within passage range {req.passage_range}.")
    return " ".join(parts)
