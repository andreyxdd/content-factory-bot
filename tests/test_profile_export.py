from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.handlers.profile import cmd_export_system_prompt
from content_factory_bot.middleware.locale import UI_LANG_KEY


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.profile.get_active_artifact_set", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.profile.is_profile_ready", new_callable=AsyncMock)
async def test_export_system_prompt_sends_markdown_from_active_artifact(
    mock_ready: AsyncMock,
    mock_active: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 55
    message.from_user.language_code = "en"
    mock_ready.return_value = True
    mock_active.return_value = SimpleNamespace(system_prompt_text="PROMPT FROM ACTIVE")

    session = MagicMock()
    session.get = AsyncMock(return_value=None)

    @asynccontextmanager
    async def _session_scope():
        yield session

    with (
        patch("content_factory_bot.handlers.profile.session_scope", _session_scope),
        patch(
            "content_factory_bot.handlers.profile.get_system_prompt_addition",
            AsyncMock(return_value=None),
        ),
    ):
        await cmd_export_system_prompt(message, **{UI_LANG_KEY: "en"})

    message.answer_document.assert_awaited_once()
    args, kwargs = message.answer_document.await_args
    payload = args[0]
    assert payload.filename == "system-prompt-55-en.md"
    assert kwargs["caption"] == "System Prompt exported."


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.profile.get_active_artifact_set", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.profile.is_profile_ready", new_callable=AsyncMock)
async def test_export_system_prompt_uses_profile_fallback(
    mock_ready: AsyncMock,
    mock_active: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 56
    message.from_user.language_code = "en"
    mock_ready.return_value = True
    mock_active.return_value = None

    session = MagicMock()
    session.get = AsyncMock(return_value=SimpleNamespace(system_prompt_text="PROMPT FROM PROFILE"))

    @asynccontextmanager
    async def _session_scope():
        yield session

    with (
        patch("content_factory_bot.handlers.profile.session_scope", _session_scope),
        patch(
            "content_factory_bot.handlers.profile.get_system_prompt_addition",
            AsyncMock(return_value=None),
        ),
    ):
        await cmd_export_system_prompt(message, **{UI_LANG_KEY: "en"})

    message.answer_document.assert_awaited_once()


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.profile.get_active_artifact_set", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.profile.is_profile_ready", new_callable=AsyncMock)
async def test_export_system_prompt_not_ready_when_missing(
    mock_ready: AsyncMock,
    mock_active: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 57
    message.from_user.language_code = "en"
    mock_ready.return_value = True
    mock_active.return_value = None

    session = MagicMock()
    session.get = AsyncMock(return_value=SimpleNamespace(system_prompt_text=""))

    @asynccontextmanager
    async def _session_scope():
        yield session

    with (
        patch("content_factory_bot.handlers.profile.session_scope", _session_scope),
        patch(
            "content_factory_bot.handlers.profile.get_system_prompt_addition",
            AsyncMock(return_value=None),
        ),
    ):
        await cmd_export_system_prompt(message, **{UI_LANG_KEY: "en"})

    message.answer_document.assert_not_called()
    args, _ = message.answer.await_args
    assert "not ready yet" in args[0].lower()
