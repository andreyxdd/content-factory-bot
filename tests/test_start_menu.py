from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.handlers.common import cmd_start, on_start_menu
from content_factory_bot.middleware.locale import UI_LANG_KEY


def _callback_data_set(markup) -> set[str]:
    out: set[str] = set()
    if markup is None:
        return out
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                out.add(btn.callback_data)
    return out


@pytest.mark.asyncio
async def test_start_first_time_shows_only_onboarding_button() -> None:
    message = AsyncMock()
    message.from_user.id = 11
    message.from_user.language_code = "en"

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch("content_factory_bot.handlers.common.session_scope", _session_scope),
        patch("content_factory_bot.handlers.common.ensure_creator", new_callable=AsyncMock),
        patch(
            "content_factory_bot.handlers.common.is_profile_ready",
            new_callable=AsyncMock,
            return_value=False,
        ),
    ):
        await cmd_start(message, **{UI_LANG_KEY: "en"})

    _, kwargs = message.answer.await_args
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert buttons == {"start:onboarding"}


@pytest.mark.asyncio
async def test_start_returning_shows_profile_and_other_buttons() -> None:
    message = AsyncMock()
    message.from_user.id = 22
    message.from_user.language_code = "ru"

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch("content_factory_bot.handlers.common.session_scope", _session_scope),
        patch("content_factory_bot.handlers.common.ensure_creator", new_callable=AsyncMock),
        patch(
            "content_factory_bot.handlers.common.is_profile_ready",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        await cmd_start(message, **{UI_LANG_KEY: "ru"})

    _, kwargs = message.answer.await_args
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert "start:profile" in buttons
    assert "start:other" in buttons
    assert "start:onboarding" not in buttons


@pytest.mark.asyncio
async def test_start_other_opens_quick_actions_menu() -> None:
    callback = AsyncMock()
    callback.data = "start:other"
    callback.message = AsyncMock()
    state = AsyncMock()

    await on_start_menu(callback, state, **{UI_LANG_KEY: "en"})

    _, kwargs = callback.message.answer.await_args
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert {"start:new", "start:sessions", "start:providers", "start:help", "start:back"} <= buttons
