import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, ContentSession, Creator
from content_factory_bot.services.content_session import (
    close_active_sessions,
    get_active_session,
    start_session,
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=5, primary_language="en"))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_close_active_sessions(db_session: AsyncSession) -> None:
    await start_session(db_session, 5, web_research=False, cover_generation=False)
    await close_active_sessions(db_session, 5)
    active = await get_active_session(db_session, 5)
    assert active is None
    result = await db_session.execute(
        select(ContentSession).where(ContentSession.telegram_user_id == 5)
    )
    row = result.scalar_one()
    assert row.state == "closed"
    assert row.is_active is False
