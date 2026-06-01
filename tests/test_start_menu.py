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
async def test_start_first_time_shows_onboarding_and_settings_buttons() -> None:
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

    args, kwargs = message.answer.await_args
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert buttons == {"start:onboarding", "start:settings"}
    assert args[0] == "Run /onboarding to set up your personal profile first."


@pytest.mark.asyncio
async def test_start_returning_shows_full_direct_menu_buttons() -> None:
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
    assert "start:new" in buttons
    assert "start:sessions" in buttons
    assert "start:providers" in buttons
    assert "start:help" in buttons
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


@pytest.mark.asyncio
async def test_start_settings_edits_existing_message_with_language_picker() -> None:
    callback = AsyncMock()
    callback.data = "start:settings"
    callback.message = AsyncMock()
    state = AsyncMock()

    await on_start_menu(callback, state, **{UI_LANG_KEY: "en"})

    callback.message.edit_text.assert_awaited_once()
    args, kwargs = callback.message.edit_text.await_args
    assert args[0] == "Choose bot language:"
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert buttons == {"start:setlang:en", "start:setlang:ru"}


@pytest.mark.asyncio
async def test_start_setlang_edits_back_to_start_message() -> None:
    callback = AsyncMock()
    callback.data = "start:setlang:ru"
    callback.from_user.id = 11
    callback.message = AsyncMock()
    state = AsyncMock()

    with (
        patch("content_factory_bot.handlers.common._set_creator_language", new_callable=AsyncMock),
        patch(
            "content_factory_bot.handlers.common._start_message_payload",
            new_callable=AsyncMock,
            return_value=("Сначала /onboarding — настройка личного профиля.", MagicMock()),
        ) as payload,
    ):
        await on_start_menu(callback, state, **{UI_LANG_KEY: "en"})

    payload.assert_awaited_once_with(11, "ru")
    callback.message.edit_text.assert_awaited_once()
