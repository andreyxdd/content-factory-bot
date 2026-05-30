import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator, ProfileArtifactSet
from content_factory_bot.services.profile_artifacts import (
    activate_artifact_set,
    get_active_artifact_set,
    has_translation_consent,
    record_translation_consent,
)


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
async def test_activate_artifact_set_keeps_single_active_row(db_session: AsyncSession) -> None:
    await activate_artifact_set(
        db_session,
        telegram_user_id=1,
        locale="en",
        profile_version=1,
        style_card_text="s1",
        values_block_text="v1",
        tribal_block_text="t1",
        system_prompt_text="p1",
    )
    await db_session.commit()
    await activate_artifact_set(
        db_session,
        telegram_user_id=1,
        locale="en",
        profile_version=2,
        style_card_text="s2",
        values_block_text="v2",
        tribal_block_text="t2",
        system_prompt_text="p2",
    )
    await db_session.commit()

    active = await get_active_artifact_set(db_session, 1, "en")
    assert active is not None
    assert active.profile_version == 2
    rows = await db_session.execute(
        select(ProfileArtifactSet).where(
            ProfileArtifactSet.telegram_user_id == 1,
            ProfileArtifactSet.locale == "en",
        )
    )
    all_rows = rows.scalars().all()
    assert len(all_rows) == 2
    assert sum(1 for row in all_rows if row.is_active) == 1


@pytest.mark.asyncio
async def test_translation_consent_persists_forever_scope(db_session: AsyncSession) -> None:
    await record_translation_consent(
        db_session,
        telegram_user_id=1,
        source_locale="en",
        target_locale="ru",
        approved=True,
    )
    await db_session.commit()
    assert await has_translation_consent(
        db_session,
        telegram_user_id=1,
        source_locale="en",
        target_locale="ru",
    )
