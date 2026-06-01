import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import (
    Base,
    Creator,
    PersonalityProfile,
    ProfileArtifactSet,
    SupportedLocale,
)
from content_factory_bot.services.content_session import save_text_input, start_session
from content_factory_bot.services.draft import DraftOrchestrator, StubChatClient
from content_factory_bot.services.onboarding_engine import required_answer_keys
from content_factory_bot.services.profile import mark_profile_ready, save_answer
from content_factory_bot.services.session_pipeline import process_session_input
from content_factory_bot.services.session_states import AWAITING_ANGLE_CHOICE

_ANGLES_JSON = json.dumps(
    {
        "angles": [
            {
                "id": "A",
                "format": "story",
                "hook": "H1",
                "preview": "P1",
            },
            {
                "id": "B",
                "format": "conflict",
                "hook": "H2",
                "preview": "P2",
            },
            {
                "id": "C",
                "format": "practice",
                "hook": "H3",
                "preview": "P3",
            },
        ]
    }
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        uid = 42
        session.add(SupportedLocale(code="en", display_name="English", is_active=True, is_default=True))
        session.add(SupportedLocale(code="ru", display_name="Russian", is_active=True, is_default=False))
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
    stub = StubChatClient(_ANGLES_JSON)
    rnd, angles = await process_session_input(
        db_session, row, orchestrator=DraftOrchestrator(client=stub)
    )
    assert rnd == 1
    assert len(angles) == 3
    assert angles[0].id == "A"
    await db_session.refresh(row)
    assert row.state == AWAITING_ANGLE_CHOICE
    assert row.title.startswith("Redis")


@pytest.mark.asyncio
async def test_process_input_prefers_localized_artifact_prompt(db_session: AsyncSession) -> None:
    uid = 42
    db_session.add(
        ProfileArtifactSet(
            telegram_user_id=uid,
            locale="en",
            profile_version=1,
            status="active",
            is_active=True,
            style_card_text="style",
            values_block_text="values",
            tribal_block_text="tribal",
            system_prompt_text="LOCALIZED_SYSTEM_PROMPT",
        )
    )
    await db_session.commit()
    row = await start_session(
        db_session, uid, web_research=False, cover_generation=False
    )
    await save_text_input(db_session, row.id, "Edge compute founders")
    stub = StubChatClient(_ANGLES_JSON)
    await process_session_input(
        db_session,
        row,
        orchestrator=DraftOrchestrator(client=stub),
    )
    assert "LOCALIZED_SYSTEM_PROMPT" in stub.last_system_message
