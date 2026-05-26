import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from content_factory_bot.db.models import Base, ContentSession, Creator
from content_factory_bot.services.content_session import save_draft_round, set_session_state
from content_factory_bot.worker.wait import DraftJobFailedError, wait_for_draft_ready


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_wait_returns_options_when_session_ready(db_engine) -> None:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=1, primary_language="en"))
        row = ContentSession(
            telegram_user_id=1,
            state="drafting",
            is_active=True,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        sid = row.id

    async def _mark_ready():
        import asyncio

        await asyncio.sleep(0.05)
        async with factory() as session:
            row2 = await session.get(ContentSession, sid)
            assert row2 is not None
            await save_draft_round(
                session, sid, round_no=1, options=["A", "B", "C"]
            )
            await set_session_state(session, row2, "awaiting_draft_choice")

    import asyncio

    task = asyncio.create_task(_mark_ready())
    rnd, options = await wait_for_draft_ready(
        db_engine, session_id=sid, timeout_sec=2.0, poll_interval=0.02
    )
    await task
    assert rnd == 1
    assert options == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_wait_ignores_stale_round_until_new_round(db_engine) -> None:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=1, primary_language="en"))
        row = ContentSession(
            telegram_user_id=1,
            state="awaiting_draft_choice",
            is_active=True,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        sid = row.id
        await save_draft_round(session, sid, round_no=1, options=["Old", "Old", "Old"])

    async def _add_round_two():
        import asyncio

        await asyncio.sleep(0.05)
        async with factory() as session:
            row2 = await session.get(ContentSession, sid)
            assert row2 is not None
            await save_draft_round(
                session, sid, round_no=2, options=["N1", "N2", "N3"]
            )
            await set_session_state(session, row2, "awaiting_draft_choice")

    import asyncio

    task = asyncio.create_task(_add_round_two())
    rnd, options = await wait_for_draft_ready(
        db_engine,
        session_id=sid,
        min_round_no=1,
        timeout_sec=2.0,
        poll_interval=0.02,
    )
    await task
    assert rnd == 2
    assert options == ["N1", "N2", "N3"]


@pytest.mark.asyncio
async def test_wait_raises_on_draft_failed(db_engine) -> None:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Creator(telegram_user_id=1, primary_language="en"))
        row = ContentSession(
            telegram_user_id=1,
            state="draft_failed",
            is_active=True,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        sid = row.id

    with pytest.raises(DraftJobFailedError):
        await wait_for_draft_ready(
            db_engine, session_id=sid, timeout_sec=0.5, poll_interval=0.02
        )
