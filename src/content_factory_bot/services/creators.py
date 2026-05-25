from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import Creator, PersonalityProfile
from content_factory_bot.locale.telegram import ui_lang_from_telegram


async def ensure_creator(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    language_code: str | None,
) -> Creator:
    """Create Creator + empty profile on first contact; seed language from Telegram."""
    creator = await session.get(Creator, telegram_user_id)
    if creator is None:
        lang = ui_lang_from_telegram(language_code)
        creator = Creator(telegram_user_id=telegram_user_id, primary_language=lang)
        session.add(creator)
        session.add(
            PersonalityProfile(telegram_user_id=telegram_user_id, ready=False, profile_version=1)
        )
        await session.flush()
        return creator

    return creator


async def get_ui_language(session: AsyncSession, telegram_user_id: int, fallback: str) -> str:
    """Prefer stored primary_language; use Telegram fallback before onboarding saves."""
    creator = await session.get(Creator, telegram_user_id)
    if creator and creator.primary_language:
        return creator.primary_language
    return fallback
