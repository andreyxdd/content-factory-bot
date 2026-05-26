import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, ContentSession, Creator
from content_factory_bot.services.content_session import start_session


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=1, primary_language="en"))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_start_session_stores_destinations(db_session: AsyncSession) -> None:
    row = await start_session(
        db_session,
        1,
        web_research=False,
        cover_generation=False,
        destinations=["telegram", "linkedin"],
    )
    data = json.loads(row.destinations_json or "[]")
    assert data == ["telegram", "linkedin"]
