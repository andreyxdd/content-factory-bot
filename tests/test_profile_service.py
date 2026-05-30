import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator, PersonalityProfile
from content_factory_bot.services.onboarding_engine import required_answer_keys
from content_factory_bot.services.profile import (
    apply_creator_preferences,
    is_profile_complete,
    save_answer,
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=1, primary_language="en"))
        session.add(PersonalityProfile(telegram_user_id=1, ready=False))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_save_answer_and_completion(db_session: AsyncSession) -> None:
    uid = 1
    for key in required_answer_keys():
        await save_answer(
            db_session,
            telegram_user_id=uid,
            question_key=key,
            answer_text="value",
            option_index=None,
            is_custom=True,
        )
    assert await is_profile_complete(db_session, uid) is True


@pytest.mark.asyncio
async def test_apply_creator_preferences_from_toggles(db_session: AsyncSession) -> None:
    uid = 1
    await save_answer(db_session, uid, "web_research", "No", 1, False)
    await save_answer(db_session, uid, "review_agent", "No", 1, False)
    await apply_creator_preferences(db_session, uid)
    creator = await db_session.get(Creator, uid)
    assert creator is not None
    assert creator.research_default_enabled is False
    assert creator.review_enabled is False
