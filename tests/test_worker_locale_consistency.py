from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_factory_bot.worker.jobs import _draft_round


@pytest.mark.asyncio
async def test_draft_round_uses_creator_primary_language_for_delivery() -> None:
    db = MagicMock()
    db.get = AsyncMock(return_value=SimpleNamespace(primary_language="ru"))
    row = SimpleNamespace(id=10)

    @asynccontextmanager
    async def _session_scope():
        yield db

    with (
        patch("content_factory_bot.worker.jobs.session_scope", _session_scope),
        patch(
            "content_factory_bot.worker.jobs.get_session_by_id",
            AsyncMock(return_value=row),
        ),
        patch(
            "content_factory_bot.worker.jobs.process_session_input",
            AsyncMock(return_value=(1, [])),
        ),
        patch("content_factory_bot.worker.jobs.notify_creator", AsyncMock()),
        patch("content_factory_bot.worker.jobs.deliver_angle_round", AsyncMock()) as deliver,
    ):
        await _draft_round({"session_id": 10, "telegram_user_id": 42})

    deliver.assert_awaited_once()
    assert deliver.await_args.kwargs["lang"] == "ru"
