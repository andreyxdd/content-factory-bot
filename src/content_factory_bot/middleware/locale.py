from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from content_factory_bot.services.locale_resolver import resolve_ui_language

UI_LANG_KEY = "ui_lang"


class LocaleMiddleware(BaseMiddleware):
    """Set effective UI language before handlers run."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = _extract_user(event)
        data[UI_LANG_KEY] = await resolve_ui_language(
            telegram_user_id=user.id if user else None,
            telegram_language_code=user.language_code if user else None,
        )
        return await handler(event, data)


def _extract_user(event: TelegramObject) -> User | None:
    if isinstance(event, Message):
        return event.from_user
    if isinstance(event, CallbackQuery):
        return event.from_user
    return None
