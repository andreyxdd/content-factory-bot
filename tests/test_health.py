from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from content_factory_bot.api.app import app
from content_factory_bot.api.health import CheckResult, HealthReport


@pytest.mark.asyncio
async def test_health_ok_when_all_checks_pass() -> None:
    report = HealthReport(
        status="ok",
        checks={
            "database": CheckResult(status="ok", latency_ms=1.0),
            "redis": CheckResult(status="ok", latency_ms=0.5),
            "config": CheckResult(status="ok"),
        },
    )
    with (
        patch("content_factory_bot.api.app.get_engine", return_value=MagicMock()),
        patch(
            "content_factory_bot.api.app.run_health_checks",
            new=AsyncMock(return_value=report),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_503_when_database_unhealthy() -> None:
    report = HealthReport(
        status="unhealthy",
        checks={
            "database": CheckResult(status="error", detail="connection refused"),
            "redis": CheckResult(status="ok", latency_ms=0.5),
            "config": CheckResult(status="ok"),
        },
    )
    with (
        patch("content_factory_bot.api.app.get_engine", return_value=MagicMock()),
        patch(
            "content_factory_bot.api.app.run_health_checks",
            new=AsyncMock(return_value=report),
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_check_config_requires_oauth_env() -> None:
    from content_factory_bot.api.health import check_config
    from content_factory_bot.config import Settings

    settings = Settings(
        BOT_TOKEN="x",
        PUBLIC_BASE_URL="",
        OAUTH_STATE_SECRET="",
    )
    result = check_config(settings)
    assert result.status == "error"
    assert "PUBLIC_BASE_URL" in (result.detail or "")
