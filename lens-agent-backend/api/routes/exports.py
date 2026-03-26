"""Export generation endpoints for multiple formats."""
from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import require_user_record, require_pro
from services.supabase_client import get_paper, save_export
from models.requests import ExportRequest
from models.responses import ExportResponse
from datetime import datetime

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.post("", response_model=ExportResponse)
async def generate_export(
    request: ExportRequest,
    user: dict = Depends(require_pro),  # Pro users only
):
    """
    Generate a Smart Brief in a different format.
    Supported: podcast_script | tweet_thread | slide_deck | eli12 | investor_memo
    """
    paper = await get_paper(request.paper_id, user["id"])
    if not paper:
        raise HTTPException(
            status_code=404, detail={"error": "Not found", "code": "not_found"}
        )
    if paper.get("status") != "done":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Paper must be fully processed before exporting",
                "code": "processing_failed",
            },
        )

    brief = paper["smart_brief"]
    
    # TODO: Integrate with actual format generation from agent
    # For now, return placeholder content
    content = f"Export in {request.format} format for paper: {brief.get('title', '')}"

    # Persist the export
    export_record = await save_export(
        user_id=user["id"],
        paper_id=request.paper_id,
        format=request.format,
        content=content,
    )

    return ExportResponse(
        paper_id=request.paper_id,
        format=request.format,
        content=content,
        word_count=len(content.split()),
        created_at=datetime.utcnow(),
    )
