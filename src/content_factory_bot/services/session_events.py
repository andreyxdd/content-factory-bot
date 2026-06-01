"""Structured session telemetry (agent-first observability)."""

from __future__ import annotations

import logging

logger = logging.getLogger("content_factory.session_events")


def emit(event: str, *, session_id: int, telegram_user_id: int, **fields: object) -> None:
    extra = " ".join(f"{k}={v!r}" for k, v in sorted(fields.items()))
    logger.info(
        "session_event event=%s session_id=%s uid=%s %s",
        event,
        session_id,
        telegram_user_id,
        extra,
    )
