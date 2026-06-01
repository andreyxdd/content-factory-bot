from unittest.mock import AsyncMock, patch

import pytest

from content_factory_bot.handlers.onboarding import _optional_text_kb, on_onboarding_callback
from content_factory_bot.middleware.locale import UI_LANG_KEY


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._persist_answer", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.onboarding._send_prompt", new_callable=AsyncMock)
async def test_skip_optional_step_advances(
    mock_send_prompt: AsyncMock,
    mock_persist_answer: AsyncMock,
) -> None:
    callback = AsyncMock()
    callback.from_user.id = 100
    callback.data = "onb:nav:skip"
    callback.message = AsyncMock()
    state = AsyncMock()
    fsm = {
        "current_step": "s2_platforms",
        "flow_stack": ["s2_audience"],
        "answers": {"s2_about": "A", "s2_audience": "B"},
    }
    state.get_data = AsyncMock(return_value=fsm)

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    mock_persist_answer.assert_awaited_once_with(100, "s2_platforms", "", None)
    assert any(
        call.kwargs.get("current_step") == "s2_voice_tone"
        for call in state.update_data.await_args_list
    )
    mock_send_prompt.assert_awaited_once_with(callback.message, state, "en", "s2_voice_tone")


@pytest.mark.asyncio
async def test_skip_required_step_shows_alert() -> None:
    callback = AsyncMock()
    callback.from_user.id = 101
    callback.data = "onb:nav:skip"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s2_about"})

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    callback.answer.assert_awaited_once()
    _, kwargs = callback.answer.await_args
    assert kwargs.get("show_alert") is True


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._persist_answer", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.onboarding._send_prompt", new_callable=AsyncMock)
async def test_skip_toggle_research_does_not_persist_and_moves_to_review(
    mock_send_prompt: AsyncMock,
    mock_persist_answer: AsyncMock,
) -> None:
    callback = AsyncMock()
    callback.from_user.id = 102
    callback.data = "onb:nav:skip"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "toggle_research", "flow_stack": []})

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    mock_persist_answer.assert_awaited_once_with(102, "web_research", "Yes", 0)
    assert any(
        call.kwargs.get("current_step") == "toggle_review"
        for call in state.update_data.await_args_list
    )
    mock_send_prompt.assert_awaited_once_with(callback.message, state, "en", "toggle_review")


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._persist_answer", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.onboarding._show_confirm_blocks", new_callable=AsyncMock)
async def test_skip_samples_persists_style_card_checkpoint(
    mock_show_confirm: AsyncMock,
    mock_persist: AsyncMock,
) -> None:
    callback = AsyncMock()
    callback.from_user.id = 103
    callback.data = "onb:nav:skip"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s3_samples", "flow_stack": []})

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    assert any(
        call.args[1] == "s3_style_card"
        for call in mock_persist.await_args_list
    )
    mock_show_confirm.assert_awaited_once_with(callback.message, state, "s3_confirm", "en")


def test_optional_step_keyboard_has_help_row_and_nav_skip() -> None:
    kb = _optional_text_kb("s4_boundaries", "en")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "onb:nav:help" in callbacks
    assert "onb:nav:skip" in callbacks

