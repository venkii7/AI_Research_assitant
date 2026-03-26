"""Redis client for pub/sub and async operations."""
import redis.asyncio as aioredis
from core.config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the Redis connection."""
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = await aioredis.from_url(
            settings.upstash_redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _redis


async def publish_progress(job_id: str, payload: dict):
    """Publish a progress event to the SSE channel for this job."""
    import json

    r = await get_redis()
    await r.publish(f"job:{job_id}", json.dumps(payload))


async def set_job_status(job_id: str, status: dict, ttl: int = 3600):
    """Store job status in Redis with TTL."""
    import json

    r = await get_redis()
    await r.setex(f"status:{job_id}", ttl, json.dumps(status))


async def get_job_status(job_id: str) -> dict | None:
    """Retrieve job status from Redis."""
    import json

    r = await get_redis()
    raw = await r.get(f"status:{job_id}")
    return json.loads(raw) if raw else None
