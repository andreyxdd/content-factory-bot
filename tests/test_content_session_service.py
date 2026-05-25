import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator
from content_factory_bot.services.content_session import (
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
        session.add(Creator(telegram_user_id=99, primary_language="en"))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_only_one_active_session(db_session: AsyncSession) -> None:
    uid = 99
    await start_session(db_session, uid, web_research=True, cover_generation=False)
    await start_session(db_session, uid, web_research=False, cover_generation=True)
    active = await get_active_session(db_session, uid)
    assert active is not None
    assert active.web_research is False
    assert active.cover_generation is True
