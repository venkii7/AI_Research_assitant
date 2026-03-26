"""Server-Sent Events endpoint for job progress streaming."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from services.redis_client import get_redis, get_job_status
from api.dependencies import require_user_record
from core.config import get_settings
import asyncio
import json

router = APIRouter(prefix="/api/stream", tags=["stream"])
settings = get_settings()


@router.get("/{job_id}")
async def stream_job_progress(
    job_id: str,
    user: dict = Depends(require_user_record),
):
    """
    Server-Sent Events stream for agent progress on a specific job.

    Event types emitted:
    - connected       : SSE connection established
    - thought         : Agent's internal reasoning step
    - tool_call       : Agent called a tool
    - progress        : Percentage update with stage label
    - quality_check   : Self-evaluation result
    - done            : Processing complete, includes full brief JSON
    - failed          : Processing failed, includes error message
    - heartbeat       : Keep-alive (every 20s)

    The stream closes automatically on 'done' or 'failed' events.
    """

    async def event_generator():
        r = await get_redis()
        pubsub = r.pubsub()
        channel = f"job:{job_id}"
        await pubsub.subscribe(channel)

        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'job_id': job_id})}\n\n"

        # Check if job already finished (client reconnecting)
        existing = await get_job_status(job_id)
        if existing and existing.get("status") in ("done", "failed"):
            yield f"data: {json.dumps(existing)}\n\n"
            await pubsub.unsubscribe(channel)
            return

        try:
            deadline = (
                asyncio.get_event_loop().time()
                + settings.job_timeout_seconds
            )

            async for message in pubsub.listen():
                # Timeout check
                if asyncio.get_event_loop().time() > deadline:
                    yield f"data: {json.dumps({'type': 'failed', 'error': 'Agent timed out'})}\n\n"
                    break

                if message["type"] != "message":
                    continue

                payload = json.loads(message["data"])
                event_type = payload.get("type", "progress")

                yield f"data: {json.dumps(payload)}\n\n"

                # Close stream on terminal events
                if event_type in ("done", "failed"):
                    break

        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables Nginx buffering
            "Connection": "keep-alive",
        },
    )
