from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.onboarding.loader import load_questions
from content_factory_bot.onboarding.presenter import show_question


@pytest.mark.asyncio
async def test_show_question_when_all_answered_calls_handoff() -> None:
    event = AsyncMock()
    event.from_user.id = 42
    state = AsyncMock()

    @asynccontextmanager
    async def _session_scope():
        yield MagicMock()

    with (
        patch(
            "content_factory_bot.onboarding.presenter.session_scope",
            _session_scope,
        ),
        patch(
            "content_factory_bot.onboarding.presenter.get_answered_keys",
            new_callable=AsyncMock,
            return_value={q.key for q in load_questions()},
        ),
        patch(
            "content_factory_bot.onboarding.presenter.finish_onboarding_handoff",
            new_callable=AsyncMock,
        ) as handoff,
    ):
        await show_question(event, lang="en", state=state)

    handoff.assert_awaited_once_with(event, lang="en", uid=42, state=state)
