import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator, PersonalityProfile
from content_factory_bot.services.content_session import save_text_input, start_session
from content_factory_bot.services.draft import DraftOrchestrator, StubChatClient
from content_factory_bot.services.onboarding_engine import required_answer_keys
from content_factory_bot.services.profile import mark_profile_ready, save_answer
from content_factory_bot.services.session_pipeline import process_session_input


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        uid = 42
        session.add(Creator(telegram_user_id=uid, primary_language="en"))
        session.add(PersonalityProfile(telegram_user_id=uid, ready=True))
        for key in required_answer_keys():
            await save_answer(
                session,
                uid,
                key,
                "value",
                None,
                True,
            )
        await mark_profile_ready(session, uid)
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_process_input_creates_draft_round(db_session: AsyncSession) -> None:
    uid = 42
    row = await start_session(
        db_session, uid, web_research=False, cover_generation=False
    )
    await save_text_input(db_session, row.id, "Redis queues for Telegram bots")
    stub = StubChatClient(json.dumps({"options": ["A", "B", "C"]}))
    rnd, options = await process_session_input(
        db_session, row, orchestrator=DraftOrchestrator(client=stub)
    )
    assert rnd == 1
    assert options == ["A", "B", "C"]
    await db_session.refresh(row)
    assert row.state == "awaiting_draft_choice"
    assert row.title.startswith("Redis")
