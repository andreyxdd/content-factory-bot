from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.handlers.settings import cmd_settings, set_language
from content_factory_bot.middleware.locale import UI_LANG_KEY


@pytest.mark.asyncio
async def test_cmd_settings_shows_language_buttons() -> None:
    message = AsyncMock()
    message.from_user.id = 77

    session = MagicMock()

    @asynccontextmanager
    async def _session_scope():
        yield session

    with (
        patch(
            "content_factory_bot.handlers.settings._supported_locale_codes",
            AsyncMock(return_value=["en", "ru"]),
        ),
        patch("content_factory_bot.handlers.settings.session_scope", _session_scope),
        patch(
            "content_factory_bot.handlers.settings.get_system_prompt_addition",
            AsyncMock(return_value=None),
        ),
    ):
        await cmd_settings(message, **{UI_LANG_KEY: "en"})

    _, kwargs = message.answer.await_args
    markup = kwargs.get("reply_markup")
    callback_ids = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert "settings:lang:en" in callback_ids
    assert "settings:lang:ru" in callback_ids


@pytest.mark.asyncio
async def test_set_language_requests_consent_before_translation() -> None:
    callback = AsyncMock()
    callback.from_user.id = 77
    callback.data = "settings:lang:ru"
    callback.message = AsyncMock()
    creator = SimpleNamespace(primary_language="en")
    session = MagicMock()
    session.get = AsyncMock(return_value=creator)

    @asynccontextmanager
    async def _session_scope():
        yield session

    with (
        patch("content_factory_bot.handlers.settings.session_scope", _session_scope),
        patch(
            "content_factory_bot.handlers.settings._supported_locale_codes",
            AsyncMock(return_value=["en", "ru"]),
        ),
        patch(
            "content_factory_bot.handlers.settings.has_translation_consent",
            AsyncMock(return_value=False),
        ),
        patch(
            "content_factory_bot.handlers.settings.switch_locale_with_pending_translation",
            AsyncMock(),
        ) as switch_locale,
    ):
        await set_language(callback, **{UI_LANG_KEY: "en"})

    switch_locale.assert_not_awaited()
    callback.message.answer.assert_awaited_once()
    args, _ = callback.message.answer.await_args
    assert "allow secure translation" in args[0]
    callback.answer.assert_awaited_once()
