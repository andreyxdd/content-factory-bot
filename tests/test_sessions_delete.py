import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, Creator
from content_factory_bot.keyboards.draft import (
    session_delete_confirm_keyboard,
    sessions_list_keyboard,
)
from content_factory_bot.handlers.content_session import _session_delete_confirm_text
from content_factory_bot.services.content_session import (
    delete_session,
    list_recent_sessions,
    start_session,
)


@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=5, primary_language="en"))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_delete_session_hides_from_list(db_session: AsyncSession) -> None:
    row = await start_session(db_session, 5, web_research=False, cover_generation=False)
    deleted = await delete_session(db_session, row.id, 5)
    assert deleted is not None
    assert deleted.state == "deleted"
    assert deleted.is_active is False
    rows = await list_recent_sessions(db_session, 5)
    assert rows == []


def test_sessions_list_keyboard_has_delete_callback() -> None:
    kb = sessions_list_keyboard([(1, "My post", "closed")], "en")
    row = kb.inline_keyboard[0]
    assert row[0].callback_data == "cs:resume:1"
    assert row[1].callback_data == "cs:del:1"


@pytest.mark.asyncio
async def test_session_delete_confirm_text_includes_title(db_session: AsyncSession) -> None:
    row = await start_session(db_session, 5, web_research=False, cover_generation=False)
    row.title = "My draft post"
    await db_session.commit()
    text = _session_delete_confirm_text(row, "en")
    assert "My draft post" in text
    assert f"#{row.id}" in text


def test_session_delete_confirm_keyboard() -> None:
    kb = session_delete_confirm_keyboard(42, "en")
    row = kb.inline_keyboard[0]
    assert row[0].callback_data == "cs:delok:42"
    assert row[1].callback_data == "cs:dellist"
