import asyncio
import logging

from content_factory_bot.config import get_settings
from content_factory_bot.worker.queue import JobQueue

logger = logging.getLogger(__name__)


async def _loop() -> None:
    settings = get_settings()
    q = JobQueue(settings.redis_url)
    await q.connect()
    logger.info("Worker listening on %s", q._queue_name)
    try:
        while True:
            job = await q.dequeue(timeout=5)
            if job:
                logger.info("job %s kind=%s", job.get("id"), job.get("kind"))
    finally:
        await q.close()


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_loop())
