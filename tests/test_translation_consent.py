from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.handlers.settings import on_translation_consent
from content_factory_bot.middleware.locale import UI_LANG_KEY


@pytest.mark.asyncio
async def test_consent_approve_records_and_starts_translation() -> None:
    callback = AsyncMock()
    callback.from_user.id = 77
    callback.data = "settings:consent:approve:en:ru"
    callback.message = AsyncMock()
    session = MagicMock()

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
            "content_factory_bot.handlers.settings.record_translation_consent",
            AsyncMock(),
        ) as record_consent,
        patch(
            "content_factory_bot.handlers.settings.switch_locale_with_pending_translation",
            AsyncMock(),
        ) as switch_locale,
    ):
        await on_translation_consent(callback, **{UI_LANG_KEY: "en"})

    record_consent.assert_awaited_once()
    switch_locale.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_consent_decline_aborts_switch() -> None:
    callback = AsyncMock()
    callback.from_user.id = 77
    callback.data = "settings:consent:decline:en:ru"
    callback.message = AsyncMock()
    session = MagicMock()

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
            "content_factory_bot.handlers.settings.record_translation_consent",
            AsyncMock(),
        ) as record_consent,
        patch(
            "content_factory_bot.handlers.settings.switch_locale_with_pending_translation",
            AsyncMock(),
        ) as switch_locale,
    ):
        await on_translation_consent(callback, **{UI_LANG_KEY: "en"})

    record_consent.assert_awaited_once()
    switch_locale.assert_not_awaited()
    callback.answer.assert_awaited_once()
