import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, ProviderConnection, ProviderKind
from content_factory_bot.services.publish.adapters import (
    InstagramPublishAdapter,
    TelegramPublishAdapter,
)


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
async def test_telegram_adapter_uses_chat_id(db_session: AsyncSession) -> None:
    conn = ProviderConnection(
        telegram_user_id=1,
        provider=ProviderKind.TELEGRAM,
        status="active",
        external_account_id="-100123",
        credentials_encrypted='{"mode":"stub"}',
    )
    db_session.add(conn)
    await db_session.commit()
    adapter = TelegramPublishAdapter(bot=None)
    result = await adapter.publish(
        draft_text="Post body",
        connection=conn,
        session_id=9,
    )
    assert result.url
    assert "t.me" in (result.url or "")


@pytest.mark.asyncio
async def test_instagram_adapter_with_token(db_session: AsyncSession) -> None:
    conn = ProviderConnection(
        telegram_user_id=1,
        provider=ProviderKind.INSTAGRAM,
        status="active",
        credentials_encrypted='{"access_token":"stub:ig-token"}',
    )
    adapter = InstagramPublishAdapter()
    result = await adapter.publish(
        draft_text="Caption",
        connection=conn,
        session_id=1,
    )
    assert result.url
    assert result.error is None
