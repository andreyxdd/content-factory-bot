"""Job kinds processed by cfbot-worker."""

import logging

from content_factory_bot.db.models import Creator
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.content_session import get_session_by_id, set_session_state
from content_factory_bot.services.draft_delivery import deliver_angle_round
from content_factory_bot.services.session_pipeline import process_session_input
from content_factory_bot.services.telegram_notify import notify_creator

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
    lang = "en"
    try:
        async with session_scope() as db:
            row = await get_session_by_id(db, session_id, telegram_user_id)
            if row is None:
                logger.error("session not found id=%s", session_id)
                return
            creator = await db.get(Creator, telegram_user_id)
            if creator:
                lang = creator.primary_language
            await notify_creator(
                telegram_user_id, t("session_stage_angles", lang)
            )
            rnd, angles = await process_session_input(db, row)
            await deliver_angle_round(
                telegram_user_id=telegram_user_id,
                session_id=session_id,
                round_no=rnd,
                angles=angles,
                lang=lang,
                session=db,
                message=None,
            )
    except Exception:
        logger.exception("draft_round failed session=%s", session_id)
        async with session_scope() as db:
            row = await get_session_by_id(db, session_id, telegram_user_id)
            if row is not None:
                await set_session_state(db, row, "draft_failed")
        await notify_creator(telegram_user_id, t("session_drafting_failed", lang))
