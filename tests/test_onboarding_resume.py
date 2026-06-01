from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.handlers.onboarding import _goal_selection_from_answer, _resume_step_from_answers, cmd_onboarding
from content_factory_bot.middleware.locale import UI_LANG_KEY


def test_resume_step_from_answers_picks_first_missing_key() -> None:
    step = _resume_step_from_answers(
        {
            "s2_about": "A",
            "s2_audience": "B",
        }
    )
    assert step == "s2_platforms"


def test_resume_step_from_answers_goes_to_toggle_when_profile_core_filled() -> None:
    step = _resume_step_from_answers(
        {
            "s2_about": "A",
            "s2_audience": "B",
            "s2_platforms": "C",
            "s2_goals": "a, c",
            "s2_reader_feel": "D",
            "s2_avoid_topics": "E",
            "s4_beliefs": "F",
            "s4_contradictions": "G",
            "s4_boundaries": "H",
            "s4_evolution": "I",
            "s5_reader_phrase": "J",
            "s5_voice_betrayal": "K",
            "web_research": "Yes",
        }
    )
    assert step == "toggle_review"


def test_goal_selection_from_answer_parses_letters_with_other_suffix() -> None:
    selected = _goal_selection_from_answer("a, c; other: custom idea")
    assert selected == ["a", "c"]


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._send_prompt", new_callable=AsyncMock)
async def test_cmd_onboarding_resumes_from_saved_answers(mock_send_prompt: AsyncMock) -> None:
    message = AsyncMock()
    message.from_user.id = 501
    message.from_user.language_code = "en"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch("content_factory_bot.handlers.onboarding.session_scope", _session_scope),
        patch("content_factory_bot.handlers.onboarding.ensure_creator", new_callable=AsyncMock),
        patch(
            "content_factory_bot.handlers.onboarding.get_profile_answers_map",
            new_callable=AsyncMock,
            return_value={"s2_about": "Builder", "s2_audience": "Founders"},
        ),
    ):
        await cmd_onboarding(message, state, **{UI_LANG_KEY: "en"})

    update_kwargs = state.update_data.await_args.kwargs
    assert update_kwargs["current_step"] == "s2_platforms"
    assert update_kwargs["answers"]["s2_about"] == "Builder"
    mock_send_prompt.assert_awaited_once_with(message, state, "en", "s2_platforms")


@pytest.mark.asyncio
async def test_cmd_onboarding_resume_s6_confirm_does_not_crash() -> None:
    message = AsyncMock()
    message.from_user.id = 777
    message.from_user.language_code = "en"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={})

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    all_answers = {
        "s2_about": "A",
        "s2_audience": "B",
        "s2_platforms": "C",
        "s2_goals": "a,b",
        "s2_reader_feel": "D",
        "s2_avoid_topics": "E",
        "s4_beliefs": "F",
        "s4_contradictions": "G",
        "s4_boundaries": "H",
        "s4_evolution": "I",
        "s5_reader_phrase": "J",
        "s5_voice_betrayal": "K",
        "web_research": "Yes",
        "review_agent": "No",
    }

    with (
        patch("content_factory_bot.handlers.onboarding.session_scope", _session_scope),
        patch("content_factory_bot.handlers.onboarding.ensure_creator", new_callable=AsyncMock),
        patch(
            "content_factory_bot.handlers.onboarding.get_profile_answers_map",
            new_callable=AsyncMock,
            return_value=all_answers,
        ),
    ):
        await cmd_onboarding(message, state, **{UI_LANG_KEY: "en"})

    update_kwargs = state.update_data.await_args.kwargs
    assert update_kwargs["current_step"] == "s6_confirm"
    assert message.answer.await_count >= 2
