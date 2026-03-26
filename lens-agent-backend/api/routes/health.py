"""Health check endpoint."""
from fastapi import APIRouter
from services.redis_client import get_redis
from services.supabase_client import supabase
from models.responses import HealthResponse
from core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check all dependent services are reachable."""
    redis_status = "ok"
    supabase_status = "ok"

    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        redis_status = f"error: {e}"

    try:
        supabase.table("papers").select("id").limit(1).execute()
    except Exception as e:
        supabase_status = f"error: {e}"

    overall = (
        "ok"
        if redis_status == "ok" and supabase_status == "ok"
        else "degraded"
    )

    return HealthResponse(
        status=overall,
        environment=settings.environment,
        redis=redis_status,
        supabase=supabase_status,
    )
