"""Q&A chat endpoint for querying papers."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.dependencies import require_user_record
from services.supabase_client import get_paper
from models.requests import QueryRequest
from models.responses import QueryResponse
from core.config import get_settings
import json

router = APIRouter(prefix="/api/query", tags=["query"])
settings = get_settings()

QUERY_SYSTEM_PROMPT = """You are a helpful research assistant with full access to a
specific academic paper. Answer the user's question accurately and concisely using
only information from the paper. If the answer is not in the paper, say so clearly.
Always cite which section your answer comes from. Be specific — include numbers,
method names, and exact results when relevant."""


@router.post("")
async def query_paper(
    request: QueryRequest,
    user: dict = Depends(require_user_record),
):
    """
    Ask a natural-language question about a paper.
    Streams the answer token-by-token via SSE.
    Uses the paper's Smart Brief + full cleaned text as context.
    """
    paper = await get_paper(request.paper_id, user["id"])
    if not paper:
        raise HTTPException(
            status_code=404,
            detail={"error": "Paper not found", "code": "not_found"},
        )
    if paper.get("status") != "done":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Paper is still being processed",
                "code": "processing_failed",
                "details": {"status": paper.get("status")},
            },
        )

    brief = paper.get("smart_brief", {})
    # Build context from Smart Brief — efficient, no need to re-read full PDF
    context = f"""
Paper: {brief.get('title', '')}
Authors: {brief.get('authors', '')}
Year: {brief.get('year', '')}

TL;DR: {brief.get('tldr', '')}

The problem: {brief.get('story', {}).get('problem', '')}
Method: {brief.get('story', {}).get('method', '')}
Results: {brief.get('story', {}).get('results', '')}
Significance: {brief.get('story', {}).get('significance', '')}
"""

    messages = [
        *request.conversation_history,
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {request.question}",
        },
    ]

    async def stream_answer():
        # TODO: Integrate with actual LLM streaming router
        # For now, return placeholder
        yield f"data: {json.dumps({'type': 'token', 'content': 'Answer would stream here'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        stream_answer(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
