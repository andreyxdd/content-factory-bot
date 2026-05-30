import logging

from sqlalchemy.exc import SQLAlchemyError

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import normalize_language
from content_factory_bot.locale.telegram import ui_lang_from_telegram
from content_factory_bot.services.creators import get_ui_language

logger = logging.getLogger(__name__)


async def resolve_ui_language(
    *,
    telegram_user_id: int | None,
    telegram_language_code: str | None,
) -> str:
    """Resolve effective UI language with DB preference and Telegram fallback."""
    fallback = ui_lang_from_telegram(telegram_language_code)
    if telegram_user_id is None:
        return fallback
    try:
        async with session_scope() as session:
            resolved = await get_ui_language(session, telegram_user_id, fallback)
    except (RuntimeError, SQLAlchemyError):
        # DB is not initialized in some unit-test contexts.
        logger.exception("locale resolver fallback to telegram locale")
        return fallback
    return normalize_language(resolved)
