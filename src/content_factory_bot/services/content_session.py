import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import ContentSession, DraftRound, SessionInput


async def get_active_session(
    session: AsyncSession, telegram_user_id: int
) -> ContentSession | None:
    result = await session.execute(
        select(ContentSession).where(
            ContentSession.telegram_user_id == telegram_user_id,
            ContentSession.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def get_session_by_id(
    session: AsyncSession, session_id: int, telegram_user_id: int
) -> ContentSession | None:
    row = await session.get(ContentSession, session_id)
    if row is None or row.telegram_user_id != telegram_user_id:
        return None
    return row


async def close_active_sessions(session: AsyncSession, telegram_user_id: int) -> None:
    await session.execute(
        update(ContentSession)
        .where(
            ContentSession.telegram_user_id == telegram_user_id,
            ContentSession.is_active.is_(True),
        )
        .values(is_active=False, state="closed")
    )
    await session.commit()


async def start_session(
    session: AsyncSession,
    telegram_user_id: int,
    *,
    web_research: bool,
    cover_generation: bool,
    destinations: list[str] | None = None,
    session_prompt_addition: str | None = None,
) -> ContentSession:
    await close_active_sessions(session, telegram_user_id)
    addition = (session_prompt_addition or "").strip() or None
    row = ContentSession(
        telegram_user_id=telegram_user_id,
        state="awaiting_input",
        is_active=True,
        web_research=web_research,
        cover_generation=cover_generation,
        destinations_json=json.dumps(destinations or []),
        session_trace_json=None,
        session_prompt_addition=addition,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def set_session_state(
    session: AsyncSession, row: ContentSession, state: str
) -> None:
    row.state = state
    await session.commit()


async def set_session_title(
    session: AsyncSession, row: ContentSession, title: str
) -> None:
    row.title = title[:255]
    await session.commit()


async def save_text_input(
    session: AsyncSession, session_id: int, text: str
) -> SessionInput:
    inp = SessionInput(session_id=session_id, input_type="text", transcript=text)
    session.add(inp)
    await session.commit()
    await session.refresh(inp)
    return inp


async def save_media_input(
    session: AsyncSession,
    session_id: int,
    *,
    input_type: str,
    transcript: str | None,
    storage_ref: str | None,
) -> SessionInput:
    inp = SessionInput(
        session_id=session_id,
        input_type=input_type,
        transcript=transcript,
        storage_ref=storage_ref,
    )
    session.add(inp)
    await session.commit()
    await session.refresh(inp)
    return inp


async def aggregate_input_text(session: AsyncSession, session_id: int) -> str:
    result = await session.execute(
        select(SessionInput)
        .where(SessionInput.session_id == session_id)
        .order_by(SessionInput.id)
    )
    parts: list[str] = []
    for row in result.scalars().all():
        if row.transcript:
            parts.append(row.transcript)
        elif row.storage_ref:
            parts.append(f"[{row.input_type}:{row.storage_ref}]")
    return "\n\n".join(parts) if parts else ""


async def set_research_brief(
    session: AsyncSession, row: ContentSession, brief: str
) -> None:
    row.research_brief = brief
    await session.commit()


async def next_round_no(session: AsyncSession, session_id: int) -> int:
    result = await session.execute(
        select(DraftRound.round_no)
        .where(DraftRound.session_id == session_id)
        .order_by(DraftRound.round_no.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    return (last or 0) + 1


async def save_draft_round(
    session: AsyncSession,
    session_id: int,
    *,
    round_no: int,
    options: list[str],
    is_refinement: bool = False,
) -> DraftRound:
    row = DraftRound(
        session_id=session_id,
        round_no=round_no,
        options_json=json.dumps(options),
        is_refinement=is_refinement,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_latest_draft_round(
    session: AsyncSession, session_id: int
) -> DraftRound | None:
    result = await session.execute(
        select(DraftRound)
        .where(DraftRound.session_id == session_id)
        .order_by(DraftRound.round_no.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def select_draft_option(
    session: AsyncSession, draft_round: DraftRound, index: int
) -> None:
    draft_round.selected_index = index
    await session.commit()


def parse_options(draft_round: DraftRound) -> list[str]:
    return json.loads(draft_round.options_json)


async def set_final_draft(
    session: AsyncSession, row: ContentSession, text: str
) -> None:
    row.final_draft_text = text
    row.state = "confirmed"
    await session.commit()


async def list_recent_sessions(
    session: AsyncSession, telegram_user_id: int, *, limit: int = 10
) -> list[ContentSession]:
    result = await session.execute(
        select(ContentSession)
        .where(
            ContentSession.telegram_user_id == telegram_user_id,
            ContentSession.state != "deleted",
        )
        .order_by(ContentSession.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_session(
    session: AsyncSession, session_id: int, telegram_user_id: int
) -> ContentSession | None:
    row = await get_session_by_id(session, session_id, telegram_user_id)
    if row is None or row.state == "deleted":
        return None
    row.state = "deleted"
    row.is_active = False
    await session.commit()
    await session.refresh(row)
    return row


async def save_for_later(
    session: AsyncSession,
    row: ContentSession,
    *,
    final_text: str,
    trace_json: str | None = None,
) -> None:
    row.final_draft_text = final_text
    if trace_json is not None:
        row.session_trace_json = trace_json
    row.state = "ready_to_publish_later"
    row.is_active = False
    await session.commit()


async def set_destinations(
    session: AsyncSession, row: ContentSession, destinations: list[str]
) -> None:
    row.destinations_json = json.dumps(destinations)
    await session.commit()


async def resume_session(
    session: AsyncSession, session_id: int, telegram_user_id: int
) -> ContentSession | None:
    row = await get_session_by_id(session, session_id, telegram_user_id)
    if row is None or row.state in ("closed", "published", "deleted"):
        return None
    if row.state == "ready_to_publish_later":
        row.is_active = True
        await session.commit()
        await session.refresh(row)
        return row
    await close_active_sessions(session, telegram_user_id)
    row.is_active = True
    await session.commit()
    await session.refresh(row)
    return row
