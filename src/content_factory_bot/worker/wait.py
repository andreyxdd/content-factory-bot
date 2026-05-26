"""Poll DB until worker (or inline) finishes draft_round."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from content_factory_bot.db.models import ContentSession
from content_factory_bot.services.content_session import (
    get_latest_draft_round,
    parse_options,
)

logger = logging.getLogger(__name__)


class DraftJobFailedError(Exception):
    """Worker marked the session draft_failed."""


async def wait_for_draft_ready(
    engine: AsyncEngine,
    *,
    session_id: int,
    min_round_no: int = 0,
    timeout_sec: float = 120.0,
    poll_interval: float = 1.0,
) -> tuple[int, list[str]]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    deadline = asyncio.get_event_loop().time() + timeout_sec
    while asyncio.get_event_loop().time() < deadline:
        async with factory() as session:
            row = await session.get(ContentSession, session_id)
            if row is None:
                await asyncio.sleep(poll_interval)
                continue
            if row.state == "draft_failed":
                raise DraftJobFailedError(
                    f"draft_round failed for session {session_id}"
                )
            if row.state == "awaiting_draft_choice":
                dr = await get_latest_draft_round(session, session_id)
                if dr and dr.round_no > min_round_no:
                    return dr.round_no, parse_options(dr)
        await asyncio.sleep(poll_interval)
    raise TimeoutError(f"draft_round not ready for session {session_id}")
