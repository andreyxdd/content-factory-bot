from unittest.mock import AsyncMock, MagicMock

import pytest

from content_factory_bot.services.draft import AngleOption
from content_factory_bot.services.draft_delivery import deliver_angle_round


@pytest.mark.asyncio
async def test_deliver_angle_round_sends_separate_messages() -> None:
    message = MagicMock()
    message.answer = AsyncMock()
    session = MagicMock()
    session.get = AsyncMock(return_value=None)

    angles = [
        AngleOption(id="A", format="story", hook="h1", preview="p1"),
        AngleOption(id="B", format="conflict", hook="h2", preview="p2"),
        AngleOption(id="C", format="practice", hook="h3", preview="p3"),
    ]
    await deliver_angle_round(
        telegram_user_id=1,
        session_id=9,
        round_no=1,
        angles=angles,
        lang="en",
        session=session,
        message=message,
    )

    # intro + 3 angles + pick prompt with keyboard
    assert message.answer.await_count == 5
    last_call = message.answer.await_args_list[-1]
    assert last_call.kwargs.get("reply_markup") is not None
    assert "Pick A" in last_call.args[0] or "pick" in last_call.args[0].lower()
