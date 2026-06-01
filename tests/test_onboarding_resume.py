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
    assert step == "s2_occupation"


def test_resume_step_from_answers_goes_to_toggle_when_profile_core_filled() -> None:
    step = _resume_step_from_answers(
        {
            "s2_about": "A",
            "occupation": "Founder",
            "s2_audience": "B",
            "audience": "B",
            "s2_platforms": "C",
            "voice_tone": "Direct",
            "formats": "Short posts",
            "niche_topics": "2-3 themes",
            "s2_goals": "a, c",
            "content_goals": "a, c",
            "signature_themes": "Personal stories",
            "personal_angle": "Career arc",
            "human_design": "No",
            "cadence": "Few times/week",
            "s2_reader_feel": "D",
            "s2_avoid_topics": "E",
            "hard_limits": "E",
            "s2_anti_markers": "important to note",
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
    assert update_kwargs["current_step"] == "s2_occupation"
    assert update_kwargs["answers"]["s2_about"] == "Builder"
    mock_send_prompt.assert_awaited_once_with(message, state, "en", "s2_occupation")


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._send_prompt", new_callable=AsyncMock)
async def test_cmd_onboarding_prefers_furthest_resume_step_over_stale_fsm(
    mock_send_prompt: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 502
    message.from_user.language_code = "en"
    state = AsyncMock()
    state.get_data = AsyncMock(return_value={"current_step": "s2_about", "answers": {}})

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch("content_factory_bot.handlers.onboarding.session_scope", _session_scope),
        patch("content_factory_bot.handlers.onboarding.ensure_creator", new_callable=AsyncMock),
        patch(
            "content_factory_bot.handlers.onboarding.get_profile_answers_map",
            new_callable=AsyncMock,
            return_value={
                "s2_about": "Builder",
                "occupation": "Founder",
                "s2_audience": "Founders",
                "audience": "Founders",
                "s2_platforms": "Telegram",
                "voice_tone": "Direct",
                "formats": "Short posts",
                "niche_topics": "2-3 themes",
                "s2_goals": "a,b",
                "content_goals": "a,b",
                "signature_themes": "Stories",
                "personal_angle": "Career arc",
                "human_design": "No",
                "cadence": "Weekly",
                "s2_reader_feel": "Relief",
                "s2_avoid_topics": "Politics",
                "hard_limits": "Politics",
            },
        ),
    ):
        await cmd_onboarding(message, state, **{UI_LANG_KEY: "en"})

    update_kwargs = state.update_data.await_args.kwargs
    assert update_kwargs["current_step"] == "s2_anti_markers"
    mock_send_prompt.assert_awaited_once_with(message, state, "en", "s2_anti_markers")


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._send_prompt", new_callable=AsyncMock)
async def test_cmd_onboarding_resumes_s3_samples_when_samples_persisted(
    mock_send_prompt: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 503
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
            return_value={
                "s2_about": "A",
                "s2_audience": "B",
                "s3_samples": "[\"post 1\", \"post 2\"]",
            },
        ),
    ):
        await cmd_onboarding(message, state, **{UI_LANG_KEY: "en"})

    update_kwargs = state.update_data.await_args.kwargs
    assert update_kwargs["current_step"] == "s3_samples"
    assert update_kwargs["samples"] == ["post 1", "post 2"]
    mock_send_prompt.assert_awaited_once_with(message, state, "en", "s3_samples")


@pytest.mark.asyncio
@patch("content_factory_bot.handlers.onboarding._send_prompt", new_callable=AsyncMock)
async def test_cmd_onboarding_resumes_s3_confirm_when_style_card_persisted(
    mock_send_prompt: AsyncMock,
) -> None:
    message = AsyncMock()
    message.from_user.id = 504
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
            return_value={
                "s2_about": "A",
                "s2_audience": "B",
                "s3_samples": "[\"post 1\"]",
                "s3_style_card": "STYLE CARD",
            },
        ),
    ):
        await cmd_onboarding(message, state, **{UI_LANG_KEY: "en"})

    update_kwargs = state.update_data.await_args.kwargs
    assert update_kwargs["current_step"] == "s3_confirm"
    assert update_kwargs["style_card_text"] == "STYLE CARD"
    mock_send_prompt.assert_awaited_once_with(message, state, "en", "s3_confirm")


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
        "occupation": "Founder",
        "s2_audience": "B",
        "audience": "B",
        "s2_platforms": "C",
        "voice_tone": "Direct",
        "formats": "Short posts",
        "niche_topics": "2-3 themes",
        "s2_goals": "a,b",
        "content_goals": "a,b",
        "signature_themes": "Stories",
        "personal_angle": "Career arc",
        "human_design": "No",
        "cadence": "Weekly",
        "s2_reader_feel": "D",
        "s2_avoid_topics": "E",
        "hard_limits": "E",
        "s2_anti_markers": "important to note",
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
