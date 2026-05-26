from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from content_factory_bot.api.app import app


@pytest.mark.asyncio
async def test_linkedin_callback_redirects_to_tme() -> None:
    db = MagicMock()

    @asynccontextmanager
    async def _session_scope():
        yield db

    with (
        patch("content_factory_bot.api.app.get_engine", return_value=MagicMock()),
        patch("content_factory_bot.api.app.ensure_schema", new_callable=AsyncMock),
        patch(
            "content_factory_bot.api.oauth.telegram_bot_open_url",
            return_value="https://t.me/yours_content_bot",
        ),
        patch(
            "content_factory_bot.api.oauth._notify_oauth_result",
            new_callable=AsyncMock,
        ),
        patch(
            "content_factory_bot.db.session.session_scope",
            _session_scope,
        ),
        patch(
            "content_factory_bot.services.providers.upsert_provider_connection",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/oauth/linkedin/callback",
                params={"code": "abc123", "state": "1805972786"},
                follow_redirects=False,
            )

    assert response.status_code == 302
    assert response.headers["location"] == "https://t.me/yours_content_bot"
    upsert.assert_awaited_once()
