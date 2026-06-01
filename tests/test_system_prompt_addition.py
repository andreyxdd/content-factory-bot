import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator, PersonalityProfile, ProfileArtifactSet
from content_factory_bot.services.content_session import start_session
from content_factory_bot.services.creator_prompt_addition import (
    clear_system_prompt_addition,
    get_system_prompt_addition,
    set_system_prompt_addition,
)
from content_factory_bot.services.system_prompt import (
    MAX_SYSTEM_PROMPT_ADDITION_LEN,
    compose_system_prompt,
    validate_system_prompt_addition,
)
from content_factory_bot.services.writing_context import resolve_writing_context


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=7, primary_language="en"))
        session.add(PersonalityProfile(telegram_user_id=7, ready=True))
        session.add(
            ProfileArtifactSet(
                telegram_user_id=7,
                locale="en",
                profile_version=1,
                status="active",
                is_active=True,
                system_prompt_text="BASE_PROMPT",
            )
        )
        await session.commit()
        yield session
    await engine.dispose()


def test_compose_system_prompt_stacks_creator_and_session() -> None:
    out = compose_system_prompt(
        "BASE",
        creator_addition="Always cite sources.",
        session_addition="Focus on the PR conflict.",
    )
    assert "BASE" in out
    assert "# CREATOR ADDITIONS" in out
    assert "Always cite sources." in out
    assert "# SESSION ADDITIONS" in out
    assert "Focus on the PR conflict." in out
    assert out.index("# CREATOR ADDITIONS") < out.index("# SESSION ADDITIONS")


def test_compose_system_prompt_skips_empty() -> None:
    assert compose_system_prompt("BASE") == "BASE"
    assert compose_system_prompt("BASE", creator_addition="   ") == "BASE"


def test_validate_rejects_long_addition() -> None:
    assert validate_system_prompt_addition("x" * (MAX_SYSTEM_PROMPT_ADDITION_LEN + 1)) == "too_long"


@pytest.mark.asyncio
async def test_set_and_clear_creator_addition(db_session: AsyncSession) -> None:
    assert await get_system_prompt_addition(db_session, 7) is None
    assert await set_system_prompt_addition(db_session, 7, "Use emojis sparingly.") is None
    assert await get_system_prompt_addition(db_session, 7) == "Use emojis sparingly."
    await clear_system_prompt_addition(db_session, 7)
    assert await get_system_prompt_addition(db_session, 7) is None


@pytest.mark.asyncio
async def test_resolve_writing_context_includes_creator_addition(
    db_session: AsyncSession,
) -> None:
    await set_system_prompt_addition(db_session, 7, "End posts with a question.")
    ctx = await resolve_writing_context(db_session, telegram_user_id=7, locale="en")
    assert "BASE_PROMPT" in ctx.system_prompt
    assert "End posts with a question." in ctx.system_prompt
    assert "# CREATOR ADDITIONS" in ctx.system_prompt


@pytest.mark.asyncio
async def test_resolve_writing_context_includes_session_addition(
    db_session: AsyncSession,
) -> None:
    row = await start_session(
        db_session,
        7,
        web_research=False,
        cover_generation=False,
        session_prompt_addition="Mention the 1000x engineer.",
    )
    await set_system_prompt_addition(db_session, 7, "Global rule.")
    ctx = await resolve_writing_context(
        db_session, telegram_user_id=7, locale="en", content_session=row
    )
    assert "Global rule." in ctx.system_prompt
    assert "Mention the 1000x engineer." in ctx.system_prompt
    assert ctx.system_prompt.index("Global rule.") < ctx.system_prompt.index(
        "Mention the 1000x engineer."
    )
