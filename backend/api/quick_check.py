"""Quick Check — search a cell line and get a traffic-light verdict."""
from fastapi import APIRouter

from models.quick_check import Identity, QuickCheckRequest, QuickCheckResponse

router = APIRouter()


@router.post("/quick", response_model=QuickCheckResponse)
async def quick(req: QuickCheckRequest) -> QuickCheckResponse:
    # TODO: resolve identity via Cellosaurus, cross-check ICLAC, find retractions
    # via Semantic Scholar, then reason with Claude to produce the verdict.
    return QuickCheckResponse(
        query=req.query,
        verdict="yellow",
        identity=Identity(correct_name=req.query),
        retractions=[],
        next_steps=["(mock) not yet implemented"],
        sources=[],
    )
