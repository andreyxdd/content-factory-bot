"""Send draft-round UI to Creator (inline handler or worker notify)."""

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import Creator
from content_factory_bot.keyboards.draft import draft_options_keyboard
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.profile import format_profile_summary
from content_factory_bot.services.review import ReviewStep
from content_factory_bot.services.telegram_notify import notify_creator, notify_creator_markup


async def deliver_draft_round(
    *,
    telegram_user_id: int,
    session_id: int,
    round_no: int,
    options: list[str],
    lang: str,
    session: AsyncSession,
    message: Message | None = None,
) -> None:
    creator = await session.get(Creator, telegram_user_id)
    if creator and creator.review_enabled:
        try:
            profile = await format_profile_summary(session, telegram_user_id, lang)
            critique = await ReviewStep().critique(
                draft_options=options, profile_summary=profile
            )
            review_text = t("session_review", lang).format(text=critique[:3500])
            if message is not None:
                await message.answer(review_text)
            else:
                await notify_creator(telegram_user_id, review_text)
        except Exception:
            pass

    body = t("session_pick_draft", lang)
    markup = draft_options_keyboard(session_id, round_no, options, lang)
    if message is not None:
        await message.answer(body, reply_markup=markup)
    else:
        await notify_creator_markup(telegram_user_id, body, markup)
