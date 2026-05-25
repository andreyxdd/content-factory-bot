from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.allowlist import is_allowlisted


class AllowlistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _extract_user_id(event)
        if user_id is None:
            return await handler(event, data)

        async with session_scope() as session:
            allowed = await is_allowlisted(session, user_id)

        if not allowed:
            lang = data.get(UI_LANG_KEY, "en")
            if isinstance(event, Message):
                await event.answer(t("not_allowlisted", lang))
            elif isinstance(event, CallbackQuery):
                await event.answer(t("not_authorized", lang), show_alert=True)
            return None
        return await handler(event, data)


def _extract_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    return None
