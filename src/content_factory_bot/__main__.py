import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from content_factory_bot.config import get_settings
from content_factory_bot.db.session import create_tables, init_db, session_scope
from content_factory_bot.handlers import setup_routers
from content_factory_bot.middleware.allowlist import AllowlistMiddleware
from content_factory_bot.middleware.locale import LocaleMiddleware
from content_factory_bot.services.allowlist import seed_allowlist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    await create_tables()
    async with session_scope() as session:
        n = await seed_allowlist(session, settings.parsed_allowlist())
    if n:
        logger.info("Seeded %s new allowlist entries from env", n)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.message.middleware(LocaleMiddleware())
    dp.callback_query.middleware(LocaleMiddleware())
    dp.message.middleware(AllowlistMiddleware())
    dp.callback_query.middleware(AllowlistMiddleware())
    setup_routers(dp)

    logger.info("Starting Content Factory bot (polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
