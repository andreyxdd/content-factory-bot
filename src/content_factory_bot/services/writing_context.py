"""Resolved system prompt + style card for writing steps."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import ContentSession
from content_factory_bot.services.creator_prompt_addition import get_system_prompt_addition
from content_factory_bot.services.profile import format_profile_summary
from content_factory_bot.services.profile_artifacts import (
    current_prompt_context,
    get_active_artifact_set,
)
from content_factory_bot.services.system_prompt import compose_system_prompt


@dataclass(frozen=True)
class WritingContext:
    system_prompt: str
    style_card: str
    status: str


async def resolve_writing_context(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    locale: str,
    content_session: ContentSession | None = None,
) -> WritingContext:
    fallback = await format_profile_summary(session, telegram_user_id, locale)
    system_prompt, status = await current_prompt_context(
        session,
        telegram_user_id=telegram_user_id,
        locale=locale,
        fallback_summary=fallback,
    )
    artifact = await get_active_artifact_set(session, telegram_user_id, locale)
    style_card = ""
    if artifact and artifact.style_card_text:
        style_card = artifact.style_card_text
    creator_addition = await get_system_prompt_addition(session, telegram_user_id)
    session_addition: str | None = None
    if content_session and content_session.session_prompt_addition:
        session_addition = content_session.session_prompt_addition.strip() or None
    return WritingContext(
        system_prompt=compose_system_prompt(
            system_prompt,
            creator_addition=creator_addition,
            session_addition=session_addition,
        ),
        style_card=style_card,
        status=status,
    )
