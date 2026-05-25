from aiogram import Dispatcher

from content_factory_bot.handlers.common import router as common_router
from content_factory_bot.handlers.providers import router as providers_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(common_router)
    dp.include_router(providers_router)
