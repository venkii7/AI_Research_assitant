"""Job queue management using Redis."""
import json
import uuid
from datetime import datetime
from services.redis_client import get_redis

PAPER_QUEUE = "bull:paper-jobs:wait"


async def enqueue_paper_job(paper_id: str, user_id: str, preferences: dict) -> str:
    """
    Push a paper processing job onto the queue.
    Returns the job_id.
    """
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "paper_id": paper_id,
        "user_id": user_id,
        "preferences": preferences,
        "enqueued_at": datetime.utcnow().isoformat(),
        "attempts": 0,
    }
    r = await get_redis()
    await r.lpush(PAPER_QUEUE, json.dumps(job))
    await r.setex(f"job:{job_id}:status", 7200, "queued")
    return job_id


async def get_queue_depth() -> int:
    """Get the number of jobs waiting in the queue."""
    r = await get_redis()
    return await r.llen(PAPER_QUEUE)
