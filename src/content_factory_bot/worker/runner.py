import asyncio
import logging

from content_factory_bot.config import get_settings
from content_factory_bot.db.session import create_tables, init_db
from content_factory_bot.worker.jobs import handle_job
from content_factory_bot.worker.queue import JobQueue

logger = logging.getLogger(__name__)


async def _loop() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    await create_tables()
    q = JobQueue(settings.redis_url)
    await q.connect()
    logger.info("Worker listening on %s", q._queue_name)
    try:
        while True:
            job = await q.dequeue(timeout=5)
            if job:
                logger.info("job %s kind=%s", job.get("id"), job.get("kind"))
                try:
                    await handle_job(job)
                except Exception:
                    logger.exception("job failed id=%s", job.get("id"))
    finally:
        await q.close()


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_loop())
