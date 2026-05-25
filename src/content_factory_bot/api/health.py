from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from content_factory_bot.config import Settings

CheckStatus = Literal["ok", "error"]


@dataclass(frozen=True)
class CheckResult:
    status: CheckStatus
    latency_ms: float | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"status": self.status}
        if self.latency_ms is not None:
            out["latency_ms"] = round(self.latency_ms, 2)
        if self.detail:
            out["detail"] = self.detail
        return out


@dataclass(frozen=True)
class HealthReport:
    status: Literal["ok", "unhealthy"]
    checks: dict[str, CheckResult]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": {name: check.as_dict() for name, check in self.checks.items()},
        }

    @property
    def http_status(self) -> int:
        return 200 if self.status == "ok" else 503


async def check_database(engine: AsyncEngine) -> CheckResult:
    start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return CheckResult(status="ok", latency_ms=latency_ms)
    except Exception as exc:
        return CheckResult(status="error", detail=str(exc))


async def check_redis(redis_url: str) -> CheckResult:
    start = time.perf_counter()
    client = redis.from_url(redis_url, decode_responses=True)
    try:
        pong = await client.ping()
        if not pong:
            return CheckResult(status="error", detail="redis PING returned false")
        latency_ms = (time.perf_counter() - start) * 1000
        return CheckResult(status="ok", latency_ms=latency_ms)
    except Exception as exc:
        return CheckResult(status="error", detail=str(exc))
    finally:
        await client.aclose()


def check_config(settings: Settings) -> CheckResult:
    missing: list[str] = []
    if not settings.public_base_url.strip():
        missing.append("PUBLIC_BASE_URL")
    if not settings.oauth_state_secret.strip():
        missing.append("OAUTH_STATE_SECRET")
    if missing:
        return CheckResult(status="error", detail=f"missing: {', '.join(missing)}")
    return CheckResult(status="ok")


async def run_health_checks(settings: Settings, engine: AsyncEngine) -> HealthReport:
    checks = {
        "database": await check_database(engine),
        "redis": await check_redis(settings.redis_url),
        "config": check_config(settings),
    }
    status: Literal["ok", "unhealthy"] = (
        "ok" if all(c.status == "ok" for c in checks.values()) else "unhealthy"
    )
    return HealthReport(status=status, checks=checks)
