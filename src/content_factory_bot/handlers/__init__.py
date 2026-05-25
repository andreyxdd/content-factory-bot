from aiogram import Dispatcher

from content_factory_bot.handlers.common import router as common_router
from content_factory_bot.handlers.content_session import router as session_router
from content_factory_bot.handlers.onboarding import router as onboarding_router
from content_factory_bot.handlers.profile import router as profile_router
from content_factory_bot.handlers.providers import router as providers_router
from content_factory_bot.handlers.settings import router as settings_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(onboarding_router)
    dp.include_router(profile_router)
    dp.include_router(settings_router)
    dp.include_router(session_router)
    dp.include_router(common_router)
    dp.include_router(providers_router)
