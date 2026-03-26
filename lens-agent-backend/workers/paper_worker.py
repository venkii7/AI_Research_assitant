"""Paper processing worker — processes queued paper jobs."""
import asyncio
import json
import logging
from services.job_queue import PAPER_QUEUE
from services.redis_client import get_redis, publish_progress
from services.supabase_client import update_paper

logger = logging.getLogger("lens.worker")


async def process_paper_job(job: dict):
    """
    Process a single paper job from the queue.
    This is where the agent pipeline would be invoked.
    """
    job_id = job["id"]
    paper_id = job["paper_id"]
    user_id = job["user_id"]

    try:
        await publish_progress(
            job_id,
            {
                "type": "progress",
                "step": 1,
                "status": "initializing",
                "message": "Paper job initialized",
            },
        )

        # TODO: Integrate agent pipeline here
        # For now, simulate processing
        await asyncio.sleep(2)

        # Publish done event
        await publish_progress(
            job_id,
            {
                "type": "done",
                "paper_id": paper_id,
                "brief": {
                    "title": "Sample Paper",
                    "authors": "Example Authors",
                    "year": "2024",
                    "paper_category": "ML",
                    "tldr": "A sample brief.",
                    "stat_cards": [],
                    "story": {
                        "problem": "",
                        "method": "",
                        "results": "",
                        "significance": "",
                    },
                    "concepts": [],
                    "removed_sections": [],
                },
            },
        )

        # Update paper status in database
        await update_paper(paper_id, {"status": "done"})

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        await publish_progress(
            job_id, {"type": "failed", "error": str(e)}
        )
        await update_paper(paper_id, {"status": "failed"})


async def run_worker():
    """Main worker loop — continuously process jobs from the queue."""
    r = await get_redis()
    logger.info("Paper worker started")

    while True:
        try:
            # Blocking pop from queue with timeout
            job_json = await r.brpop(PAPER_QUEUE, timeout=5)
            if job_json:
                _, job_str = job_json  # (queue_name, job_data)
                job = json.loads(job_str)
                await process_paper_job(job)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())
