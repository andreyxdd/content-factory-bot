from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

import pytest

from content_factory_bot.services.locale_resolver import resolve_ui_language


@pytest.mark.asyncio
async def test_resolve_ui_language_uses_telegram_fallback_without_user() -> None:
    lang = await resolve_ui_language(
        telegram_user_id=None,
        telegram_language_code="ru-RU",
    )
    assert lang == "ru"


@pytest.mark.asyncio
async def test_resolve_ui_language_prefers_stored_creator_language() -> None:
    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch("content_factory_bot.services.locale_resolver.session_scope", _session_scope),
        patch(
            "content_factory_bot.services.locale_resolver.get_ui_language",
            autospec=True,
            return_value="ru",
        ) as get_ui_language,
    ):
        lang = await resolve_ui_language(
            telegram_user_id=123,
            telegram_language_code="en",
        )

    assert lang == "ru"
    assert get_ui_language.await_count == 1


@pytest.mark.asyncio
async def test_resolve_ui_language_falls_back_when_db_errors() -> None:
    @asynccontextmanager
    async def _broken_scope():
        raise RuntimeError("db unavailable")
        yield

    with patch("content_factory_bot.services.locale_resolver.session_scope", _broken_scope):
        lang = await resolve_ui_language(
            telegram_user_id=123,
            telegram_language_code="ru-RU",
        )

    assert lang == "ru"
