from unittest.mock import AsyncMock, patch

import pytest

from content_factory_bot.handlers.onboarding import on_onboarding_callback, on_onboarding_text
from content_factory_bot.middleware.locale import UI_LANG_KEY


def _callback_data_set(markup) -> set[str]:
    out: set[str] = set()
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                out.add(btn.callback_data)
    return out


@pytest.mark.asyncio
async def test_s2_confirm_edit_shows_fork_not_full_field_list() -> None:
    callback = AsyncMock()
    callback.from_user.id = 7
    callback.data = "onb:s2_confirm:edit"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s2_confirm", "answers": {}, "flow_stack": []})

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    _, kwargs = callback.message.answer.await_args
    callbacks = _callback_data_set(kwargs["reply_markup"])
    assert "onb:s2_confirm:edit_fields" in callbacks
    assert "onb:s2_confirm:continue_questions" in callbacks
    assert "onb:edit:s4_beliefs" not in callbacks
    assert "onb:edit:s5_reader_phrase" not in callbacks


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._advance_from_confirm", new_callable=AsyncMock)
async def test_s2_confirm_continue_questions_advances(mock_advance: AsyncMock) -> None:
    callback = AsyncMock()
    callback.from_user.id = 9
    callback.data = "onb:s2_confirm:continue_questions"
    callback.message = AsyncMock()
    state = AsyncMock()
    fsm = {"current_step": "s2_confirm", "flow_stack": ["s2_avoid_topics"]}
    state.get_data = AsyncMock(return_value=fsm)

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    mock_advance.assert_awaited_once_with(callback.message, state, "en", 9, "s2_confirm", fsm)


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._persist_answer", new_callable=AsyncMock)
@patch("content_factory_bot.handlers.onboarding._show_confirm_blocks", new_callable=AsyncMock)
async def test_pending_edit_returns_to_origin_confirm(
    mock_show_confirm: AsyncMock,
    _mock_persist: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 13
    message.text = "Updated belief"
    state = AsyncMock()
    state.get_data = AsyncMock(
        return_value={
            "current_step": "s4_beliefs",
            "pending_edit_key": "s4_beliefs",
            "pending_edit_confirm_step": "s4_confirm",
            "answers": {"s4_beliefs": "old"},
            "flow_stack": [],
        }
    )

    await on_onboarding_text(message, state, **{UI_LANG_KEY: "en"})

    assert any(
        call.kwargs.get("current_step") == "s4_confirm"
        and call.kwargs.get("pending_edit_key") is None
        and call.kwargs.get("pending_edit_confirm_step") is None
        for call in state.update_data.await_args_list
    )
    mock_show_confirm.assert_awaited_once_with(message, state, "s4_confirm", "en")


@pytest.mark.asyncio
async def test_s3_sample_saved_ack_includes_analyze_button() -> None:
    message = AsyncMock()
    message.from_user.id = 21
    message.text = "Some sample post"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s3_samples", "samples": []})

    await on_onboarding_text(message, state, **{UI_LANG_KEY: "en"})

    args, kwargs = message.answer.await_args
    assert args[0] == "Sample saved (1)."
    callbacks = _callback_data_set(kwargs["reply_markup"])
    assert "onb:sample:analyze" in callbacks


@pytest.mark.asyncio
async def test_nav_cancel_pauses_and_moves_to_latest_confirm_checkpoint() -> None:
    callback = AsyncMock()
    callback.from_user.id = 31
    callback.data = "onb:nav:cancel"
    callback.message = AsyncMock()
    state = AsyncMock()
    state.get_data = AsyncMock(
        return_value={
            "current_step": "s4_beliefs",
            "style_card_text": "YOUR STYLE CARD",
            "answers": {
                "s2_about": "A",
                "s2_audience": "B",
            },
        }
    )

    await on_onboarding_callback(callback, state, **{UI_LANG_KEY: "en"})

    state.update_data.assert_awaited_once_with(current_step="s3_confirm")
    args, _ = callback.message.answer.await_args
    assert "Onboarding paused" in args[0]
