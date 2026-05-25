"""Job kinds processed by cfbot-worker."""

import logging

from content_factory_bot.db.session import session_scope
from content_factory_bot.services.content_session import get_session_by_id
from content_factory_bot.services.session_pipeline import process_session_input

logger = logging.getLogger(__name__)


async def handle_job(job: dict) -> None:
    kind = job.get("kind")
    payload = job.get("payload") or {}
    if kind == "draft_round":
        await _draft_round(payload)
    else:
        logger.warning("unknown job kind=%s", kind)


async def _draft_round(payload: dict) -> None:
    session_id = int(payload["session_id"])
    telegram_user_id = int(payload["telegram_user_id"])
    async with session_scope() as db:
        row = await get_session_by_id(db, session_id, telegram_user_id)
        if row is None:
            logger.error("session not found id=%s", session_id)
            return
        await process_session_input(db, row)
