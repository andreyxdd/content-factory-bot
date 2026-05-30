import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, PersonalityProfile
from content_factory_bot.services.profile import save_profile_artifacts


@pytest.mark.asyncio
async def test_profile_artifacts_saved() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:  # type: AsyncSession
        await save_profile_artifacts(
            session,
            42,
            style_card_text="style",
            values_block_text="values",
            tribal_block_text="tribal",
            system_prompt_text="prompt",
        )
        row = await session.get(PersonalityProfile, 42)
        assert row is not None
        assert row.style_card_text == "style"
        assert row.system_prompt_text == "prompt"
    await engine.dispose()
