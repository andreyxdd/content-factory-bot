"""Persist per-creator additions to the writing system prompt."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import Creator
from content_factory_bot.services.system_prompt import validate_system_prompt_addition


async def get_system_prompt_addition(
    session: AsyncSession, telegram_user_id: int
) -> str | None:
    creator = await session.get(Creator, telegram_user_id)
    if creator is None or not creator.system_prompt_addition:
        return None
    text = creator.system_prompt_addition.strip()
    return text or None


async def set_system_prompt_addition(
    session: AsyncSession,
    telegram_user_id: int,
    text: str,
) -> str | None:
    """
    Save addition (empty clears). Returns error key or None on success.
    """
    cleaned = text.strip()
    if cleaned:
        err = validate_system_prompt_addition(cleaned)
        if err:
            return err
    creator = await session.get(Creator, telegram_user_id)
    if creator is None:
        return "no_creator"
    creator.system_prompt_addition = cleaned or None
    await session.commit()
    return None


async def clear_system_prompt_addition(
    session: AsyncSession, telegram_user_id: int
) -> bool:
    creator = await session.get(Creator, telegram_user_id)
    if creator is None:
        return False
    creator.system_prompt_addition = None
    await session.commit()
    return True
