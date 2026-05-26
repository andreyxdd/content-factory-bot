"""Send Telegram messages outside the polling dispatcher (e.g. OAuth callbacks)."""

import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from content_factory_bot.config import get_settings

logger = logging.getLogger(__name__)


async def notify_creator(telegram_user_id: int, text: str) -> bool:
    """DM the Creator. Returns False if BOT_TOKEN missing or send failed."""
    token = get_settings().bot_token.strip()
    if not token:
        logger.warning("notify_creator skipped: BOT_TOKEN not set")
        return False
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await bot.send_message(telegram_user_id, text)
        return True
    except Exception:
        logger.exception("notify_creator failed uid=%s", telegram_user_id)
        return False
    finally:
        await bot.session.close()
