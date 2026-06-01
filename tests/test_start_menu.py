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


def _callback_text_map(markup) -> dict[str, str]:
    out: dict[str, str] = {}
    if markup is None:
        return out
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                out[btn.callback_data] = btn.text
    return out


@pytest.mark.asyncio
async def test_start_first_time_shows_onboarding_and_settings_buttons() -> None:
    message = AsyncMock()
    message.from_user.id = 11
    message.from_user.language_code = "en"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})

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
        patch(
            "content_factory_bot.handlers.common.get_profile_answers_map",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        await cmd_start(message, state, **{UI_LANG_KEY: "en"})

    args, kwargs = message.answer.await_args
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert buttons == {"start:onboarding", "start:settings"}
    assert args[0] == "Run /onboarding to set up your personal profile first."


@pytest.mark.asyncio
async def test_start_returning_shows_full_direct_menu_buttons() -> None:
    message = AsyncMock()
    message.from_user.id = 22
    message.from_user.language_code = "ru"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})

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
        patch(
            "content_factory_bot.handlers.common.get_profile_answers_map",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        await cmd_start(message, state, **{UI_LANG_KEY: "ru"})

    _, kwargs = message.answer.await_args
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert "start:profile" in buttons
    assert "start:new" in buttons
    assert "start:sessions" in buttons
    assert "start:providers" in buttons
    assert "start:help" in buttons
    assert "start:onboarding" not in buttons


@pytest.mark.asyncio
async def test_start_partial_shows_resume_onboarding_state() -> None:
    message = AsyncMock()
    message.from_user.id = 33
    message.from_user.language_code = "en"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})

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
        patch(
            "content_factory_bot.handlers.common.get_profile_answers_map",
            new_callable=AsyncMock,
            return_value={"s2_about": "I write about product"},
        ),
    ):
        await cmd_start(message, state, **{UI_LANG_KEY: "en"})

    args, kwargs = message.answer.await_args
    assert args[0] == "You have unfinished onboarding. Run /onboarding to resume from where you stopped."
    labels = _callback_text_map(kwargs.get("reply_markup"))
    assert labels["start:onboarding"] == "🚀 Resume onboarding"


@pytest.mark.asyncio
async def test_start_with_fsm_progress_shows_resume_onboarding_state() -> None:
    message = AsyncMock()
    message.from_user.id = 44
    message.from_user.language_code = "en"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s2_audience"})

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch("content_factory_bot.handlers.common.session_scope", _session_scope),
        patch("content_factory_bot.handlers.common.ensure_creator", new_callable=AsyncMock),
    ):
        await cmd_start(message, state, **{UI_LANG_KEY: "en"})

    args, kwargs = message.answer.await_args
    assert args[0] == "You have unfinished onboarding. Run /onboarding to resume from where you stopped."
    buttons = _callback_data_set(kwargs.get("reply_markup"))
    assert buttons == {"start:onboarding", "start:settings"}


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


@pytest.mark.asyncio
async def test_start_onboarding_callback_uses_callback_actor_identity() -> None:
    callback = AsyncMock()
    callback.data = "start:onboarding"
    callback.from_user.id = 1805972786
    callback.from_user.language_code = "ru"
    callback.message = AsyncMock()
    callback.message.from_user.id = 999999999
    state = AsyncMock()

    with patch(
        "content_factory_bot.handlers.onboarding.start_onboarding",
        new_callable=AsyncMock,
    ) as start_onboarding:
        await on_start_menu(callback, state, **{UI_LANG_KEY: "en"})

    start_onboarding.assert_awaited_once_with(
        callback.message,
        state,
        uid=1805972786,
        language_code="ru",
        lang="en",
    )


@pytest.mark.asyncio
async def test_start_profile_callback_uses_callback_actor_identity() -> None:
    callback = AsyncMock()
    callback.data = "start:profile"
    callback.from_user.id = 1805972786
    callback.message = AsyncMock()
    callback.message.from_user.id = 999999999
    state = AsyncMock()

    with patch(
        "content_factory_bot.handlers.profile.show_profile",
        new_callable=AsyncMock,
    ) as show_profile:
        await on_start_menu(callback, state, **{UI_LANG_KEY: "en"})

    show_profile.assert_awaited_once_with(
        callback.message,
        state,
        uid=1805972786,
        lang="en",
    )
