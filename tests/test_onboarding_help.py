from unittest.mock import AsyncMock

import pytest

from content_factory_bot.handlers.onboarding import on_onboarding_callback
from content_factory_bot.middleware.locale import UI_LANG_KEY


@pytest.mark.asyncio
async def test_help_uses_current_step_context_in_english() -> None:
    callback = AsyncMock()
    callback.from_user.id = 77
    callback.data = "onb:nav:help"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s4_beliefs"})

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    args, _kwargs = callback.message.answer.await_args
    text = args[0].lower()
    assert "opinions you hold" in text
    assert "microservices" in text


@pytest.mark.asyncio
async def test_help_uses_current_step_context_in_russian() -> None:
    callback = AsyncMock()
    callback.from_user.id = 88
    callback.data = "onb:nav:help"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s4_contradictions"})

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "ru"})

    args, _kwargs = callback.message.answer.await_args
    text = args[0].lower()
    assert "внутренние противоречия" in text
