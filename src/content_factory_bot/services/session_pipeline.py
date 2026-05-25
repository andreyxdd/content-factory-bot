"""Run research + draft rounds for a content session (bot + worker share this)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import ContentSession, Creator
from content_factory_bot.services.content_session import (
    aggregate_input_text,
    next_round_no,
    save_draft_round,
    set_research_brief,
    set_session_state,
    set_session_title,
)
from content_factory_bot.services.draft import DraftOrchestrator
from content_factory_bot.services.profile import format_profile_summary
from content_factory_bot.services.research import ResearchStep

logger = logging.getLogger(__name__)


async def title_from_input(text: str) -> str:
    line = text.strip().split("\n", 1)[0]
    return (line[:80] + "…") if len(line) > 80 else line or "Untitled"


async def process_session_input(
    db: AsyncSession,
    row: ContentSession,
    *,
    orchestrator: DraftOrchestrator | None = None,
    research: ResearchStep | None = None,
) -> tuple[int, list[str]]:
    """After text/media saved: research (optional) → first draft round. Returns (round_no, options)."""
    uid = row.telegram_user_id
    lang = "en"
    creator = await db.get(Creator, uid)
    if creator:
        lang = creator.primary_language

    input_text = await aggregate_input_text(db, row.id)
    if row.title == "Untitled" and input_text:
        await set_session_title(db, row, await title_from_input(input_text))

    profile = await format_profile_summary(db, uid, lang)

    if row.web_research:
        await set_session_state(db, row, "researching")
        step = research or ResearchStep()
        try:
            brief = await step.run(profile_summary=profile, input_text=input_text)
        except Exception:
            logger.exception("research failed session=%s", row.id)
            brief = "(Research unavailable — continuing without brief.)"
        await set_research_brief(db, row, brief)
    else:
        brief = None

    await set_session_state(db, row, "drafting")
    orch = orchestrator or DraftOrchestrator()
    options = await orch.generate_initial_round(
        profile_summary=profile,
        input_text=input_text,
        research_brief=row.research_brief or brief,
    )
    rnd = await next_round_no(db, row.id)
    await save_draft_round(db, row.id, round_no=rnd, options=options)
    await set_session_state(db, row, "awaiting_draft_choice")
    return rnd, options
