import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, ContentSession, Creator
from content_factory_bot.services.publish import PublishOrchestrator
from content_factory_bot.db.models import ProviderConnection, ProviderKind


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=7, primary_language="en"))
        session.add(
            ContentSession(
                telegram_user_id=7,
                state="awaiting_publish",
                is_active=True,
            )
        )
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_publish_creates_artifacts_for_three_providers(db_session: AsyncSession) -> None:
    row = (await db_session.execute(select(ContentSession).limit(1))).scalar_one()
    for prov in (ProviderKind.TELEGRAM, ProviderKind.INSTAGRAM, ProviderKind.LINKEDIN):
        db_session.add(
            ProviderConnection(
                telegram_user_id=7,
                provider=prov,
                status="active",
                credentials_encrypted='{"access_token":"stub:tok"}',
                external_account_id="-1001" if prov == ProviderKind.TELEGRAM else None,
            )
        )
    await db_session.commit()
    results = await PublishOrchestrator().publish_session(
        db_session,
        session_id=row.id,
        telegram_user_id=7,
        draft_text="Hello world",
    )
    assert len(results) == 3
    assert all(r.url for r in results)
