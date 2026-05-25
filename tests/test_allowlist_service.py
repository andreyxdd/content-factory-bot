import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base
from content_factory_bot.services.allowlist import is_allowlisted, seed_allowlist


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_and_check(db_session: AsyncSession) -> None:
    n = await seed_allowlist(db_session, frozenset({111, 222}))
    assert n == 2
    assert await is_allowlisted(db_session, 111) is True
    assert await is_allowlisted(db_session, 999) is False

    n2 = await seed_allowlist(db_session, frozenset({111, 333}))
    assert n2 == 1
    assert await is_allowlisted(db_session, 333) is True
