"""Agent memory inspection endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from api.dependencies import require_user_record

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("")
async def get_memory_stats(user: dict = Depends(require_user_record)):
    """
    Return the agent's long-term memory stats.
    Includes total episodes stored, top concepts cached, recent domain insights.
    """
    # TODO: Integrate with actual memory service from agent
    return {
        "total_episodes": 0,
        "top_concepts": [],
        "recent_insights": [],
        "memory_types": {
            "paper_pattern": 0,
            "concept": 0,
            "domain_insight": 0,
            "failure_pattern": 0,
        },
    }


@router.get("/search")
async def search_memory(
    query: str = Query(..., min_length=1),
    memory_type: str | None = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    user: dict = Depends(require_user_record),
):
    """
    Semantic search over the agent's memory.
    Returns similar past experiences and useful patterns.
    """
    # TODO: Integrate with actual semantic search from memory service
    return {"results": [], "query": query}
