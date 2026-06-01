"""Run research + linear angle generation for a content session."""

from __future__ import annotations

import json
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
from content_factory_bot.services.draft import AngleOption, DraftOrchestrator
from content_factory_bot.services.quality_gate import apply_quality_gate
from content_factory_bot.services.research import ResearchStep
from content_factory_bot.services.session_events import emit
from content_factory_bot.services.session_states import AWAITING_ANGLE_CHOICE, EXPANDING_POST
from content_factory_bot.services.writing_context import resolve_writing_context

logger = logging.getLogger(__name__)


async def title_from_input(text: str) -> str:
    line = text.strip().split("\n", 1)[0]
    return (line[:80] + "…") if len(line) > 80 else line or "Untitled"


def angles_to_storage(angles: list[AngleOption]) -> list[str]:
    return [json.dumps(a.__dict__, ensure_ascii=False) for a in angles]


def angles_from_storage(options: list[str]) -> list[AngleOption]:
    out: list[AngleOption] = []
    for raw in options:
        data = json.loads(raw)
        out.append(
            AngleOption(
                id=data["id"],
                format=data["format"],
                hook=data["hook"],
                preview=data["preview"],
            )
        )
    return out


async def process_session_input(
    db: AsyncSession,
    row: ContentSession,
    *,
    orchestrator: DraftOrchestrator | None = None,
    research: ResearchStep | None = None,
) -> tuple[int, list[AngleOption]]:
    """After input saved: research (optional) → three angles. Returns (round_no, angles)."""
    uid = row.telegram_user_id
    lang = "en"
    creator = await db.get(Creator, uid)
    if creator:
        lang = creator.primary_language

    input_text = await aggregate_input_text(db, row.id)
    if row.title == "Untitled" and input_text:
        await set_session_title(db, row, await title_from_input(input_text))

    ctx = await resolve_writing_context(
        db, telegram_user_id=uid, locale=lang, content_session=row
    )

    brief = None
    if row.web_research:
        await set_session_state(db, row, "researching")
        step = research or ResearchStep()
        try:
            brief = await step.run(profile_summary=ctx.system_prompt, input_text=input_text)
        except Exception:
            logger.exception("research failed session=%s", row.id)
            brief = "(Research unavailable — continuing without brief.)"
        await set_research_brief(db, row, brief)

    await set_session_state(db, row, "drafting")
    orch = orchestrator or DraftOrchestrator()
    angles = await orch.generate_three_angles(
        system_prompt=ctx.system_prompt,
        style_card=ctx.style_card,
        content_language=lang,
        input_text=input_text,
        research_brief=row.research_brief or brief,
    )
    rnd = await next_round_no(db, row.id)
    await save_draft_round(
        db, row.id, round_no=rnd, options=angles_to_storage(angles)
    )
    await set_session_state(db, row, AWAITING_ANGLE_CHOICE)
    emit("angle_generated", session_id=row.id, telegram_user_id=uid, round_no=rnd)
    return rnd, angles


async def expand_angle_to_post(
    db: AsyncSession,
    row: ContentSession,
    angle: AngleOption,
    *,
    orchestrator: DraftOrchestrator | None = None,
) -> str:
    uid = row.telegram_user_id
    lang = "en"
    creator = await db.get(Creator, uid)
    if creator:
        lang = creator.primary_language
    ctx = await resolve_writing_context(
        db, telegram_user_id=uid, locale=lang, content_session=row
    )
    input_text = await aggregate_input_text(db, row.id)
    await set_session_state(db, row, EXPANDING_POST)
    orch = orchestrator or DraftOrchestrator()
    draft = await orch.expand_selected_angle_to_full_post(
        system_prompt=ctx.system_prompt,
        style_card=ctx.style_card,
        content_language=lang,
        input_text=input_text,
        angle=angle,
    )
    draft, retries = await apply_quality_gate(
        system_prompt=ctx.system_prompt,
        draft_text=draft,
        style_card=ctx.style_card,
        content_language=lang,
    )
    if retries:
        emit(
            "quality_gate_retry",
            session_id=row.id,
            telegram_user_id=uid,
            retries=retries,
        )
    emit("full_post_generated", session_id=row.id, telegram_user_id=uid)
    return draft
