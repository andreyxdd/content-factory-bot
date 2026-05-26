import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator, ProviderConnection, ProviderKind
from content_factory_bot.services.providers import (
    disconnect_provider,
    is_setup_complete,
    list_active_providers,
    parse_disconnect_arg,
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=42, primary_language="en"))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_setup_complete_requires_active_connection(db_session: AsyncSession) -> None:
    assert await is_setup_complete(db_session, 42) is False
    db_session.add(
        ProviderConnection(
            telegram_user_id=42,
            provider=ProviderKind.TELEGRAM,
            status="active",
            credentials_encrypted="x",
            external_account_id="-100",
        )
    )
    await db_session.commit()
    assert await is_setup_complete(db_session, 42) is True
    assert await list_active_providers(db_session, 42) == [ProviderKind.TELEGRAM]


@pytest.mark.asyncio
async def test_disconnect_removes_row(db_session: AsyncSession) -> None:
    db_session.add(
        ProviderConnection(
            telegram_user_id=42,
            provider=ProviderKind.LINKEDIN,
            status="active",
            credentials_encrypted="x",
        )
    )
    await db_session.commit()
    ok = await disconnect_provider(db_session, telegram_user_id=42, provider=ProviderKind.LINKEDIN)
    assert ok is True
    assert await is_setup_complete(db_session, 42) is False


def test_parse_disconnect_arg() -> None:
    assert parse_disconnect_arg("/disconnect telegram") == ProviderKind.TELEGRAM
    assert parse_disconnect_arg("/disconnect ig") == ProviderKind.INSTAGRAM
    assert parse_disconnect_arg("/disconnect") is None
