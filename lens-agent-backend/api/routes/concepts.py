"""Concept explanation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import require_user_record
from services.supabase_client import get_paper
from models.requests import ConceptRequest
from models.responses import ConceptExplanation

router = APIRouter(prefix="/api/concepts", tags=["concepts"])


@router.post("", response_model=ConceptExplanation)
async def get_concept_explanation(
    request: ConceptRequest,
    user: dict = Depends(require_user_record),
):
    """
    Get a concept explanation at a specified depth.
    Checks the concept cache first. Falls back to live generation.
    Free users: standard depth only.
    Pro users: all three depths.
    """
    # Enforce depth limit for free users
    if request.depth != "standard" and user.get("plan") == "free":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Simple and Expert depth require a Pro plan",
                "code": "plan_limit_reached",
                "details": {
                    "current_plan": "free",
                    "requested_depth": request.depth,
                },
            },
        )

    paper = await get_paper(request.paper_id, user["id"])
    if not paper:
        raise HTTPException(
            status_code=404, detail={"error": "Not found", "code": "not_found"}
        )

    # TODO: Integrate with actual concept explainer from agent
    # For now, return placeholder
    return ConceptExplanation(
        concept=request.concept,
        depth=request.depth,
        explanation="Concept explanation would be generated here",
        analogy="Comparative analogy would be here",
        sources=[],
        cached=False,
    )
