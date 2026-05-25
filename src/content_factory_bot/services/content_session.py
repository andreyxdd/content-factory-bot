import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import ContentSession


async def get_active_session(
    session: AsyncSession, telegram_user_id: int
) -> ContentSession | None:
    result = await session.execute(
        select(ContentSession).where(
            ContentSession.telegram_user_id == telegram_user_id,
            ContentSession.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def close_active_sessions(session: AsyncSession, telegram_user_id: int) -> None:
    await session.execute(
        update(ContentSession)
        .where(
            ContentSession.telegram_user_id == telegram_user_id,
            ContentSession.is_active.is_(True),
        )
        .values(is_active=False, state="closed")
    )
    await session.commit()


async def start_session(
    session: AsyncSession,
    telegram_user_id: int,
    *,
    web_research: bool,
    cover_generation: bool,
    destinations: list[str] | None = None,
) -> ContentSession:
    await close_active_sessions(session, telegram_user_id)
    row = ContentSession(
        telegram_user_id=telegram_user_id,
        state="awaiting_input",
        is_active=True,
        web_research=web_research,
        cover_generation=cover_generation,
        destinations_json=json.dumps(destinations or []),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
