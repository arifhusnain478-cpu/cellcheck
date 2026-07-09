"""Methods Section Generator — produce a publication-ready methods paragraph."""
from fastapi import APIRouter

from models.methods import ComplianceStatus, MethodsRequest, MethodsResponse

router = APIRouter()


@router.post("/methods-section", response_model=MethodsResponse)
async def methods_section(req: MethodsRequest) -> MethodsResponse:
    # TODO: resolve the correct RRID via Cellosaurus, check journal policy, then
    # have Claude draft a methods paragraph in the correct academic style.
    return MethodsResponse(
        methods_paragraph="(mock) not yet implemented",
        compliance_status=ComplianceStatus(
            journal=req.target_journal,
            compliant=False,
            missing_fields=[],
        ),
        rrid_used=None,
        sources=[],
    )
