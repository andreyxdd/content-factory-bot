"""Deliver angle round / legacy draft round UI to Creator."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import Creator
from content_factory_bot.keyboards.draft import draft_options_keyboard
from content_factory_bot.keyboards.session_flow import angle_choice_keyboard
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.draft import AngleOption
from content_factory_bot.services.profile import format_profile_summary
from content_factory_bot.services.review import ReviewStep
from content_factory_bot.services.telegram_notify import notify_creator, notify_creator_markup


async def _send_creator_message(
    *,
    telegram_user_id: int,
    text: str,
    message: Message | None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if message is not None:
        if reply_markup is not None:
            await message.answer(text, reply_markup=reply_markup)
        else:
            await message.answer(text)
        return
    if reply_markup is not None:
        await notify_creator_markup(telegram_user_id, text, reply_markup)
    else:
        await notify_creator(telegram_user_id, text)


def _angle_message(angle: AngleOption, lang: str) -> str:
    sep = "═" * 43
    return f"{sep}\n{angle.display_block(lang)}\n{sep}"


async def deliver_angle_round(
    *,
    telegram_user_id: int,
    session_id: int,
    round_no: int,
    angles: list[AngleOption],
    lang: str,
    session: AsyncSession,
    message: Message | None = None,
) -> None:
    creator = await session.get(Creator, telegram_user_id)
    if creator and creator.review_enabled:
        try:
            profile = await format_profile_summary(session, telegram_user_id, lang)
            opts = [f"{a.hook}\n{a.preview}" for a in angles]
            review_text = await ReviewStep().critique(
                draft_options=opts, profile_summary=profile, lang=lang
            )
            await _send_creator_message(
                telegram_user_id=telegram_user_id,
                text=review_text,
                message=message,
            )
        except Exception:
            pass

    await _send_creator_message(
        telegram_user_id=telegram_user_id,
        text=t("session_angles_intro", lang),
        message=message,
    )
    for angle in angles[:3]:
        await _send_creator_message(
            telegram_user_id=telegram_user_id,
            text=_angle_message(angle, lang),
            message=message,
        )
    await _send_creator_message(
        telegram_user_id=telegram_user_id,
        text=t("session_pick_angle", lang),
        message=message,
        reply_markup=angle_choice_keyboard(session_id, lang),
    )


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
    """Legacy three-option draft menu."""
    creator = await session.get(Creator, telegram_user_id)
    if creator and creator.review_enabled:
        try:
            profile = await format_profile_summary(session, telegram_user_id, lang)
            review_text = await ReviewStep().critique(
                draft_options=options, profile_summary=profile, lang=lang
            )
            await _send_creator_message(
                telegram_user_id=telegram_user_id,
                text=review_text,
                message=message,
            )
        except Exception:
            pass

    body = t("session_pick_draft", lang)
    markup = draft_options_keyboard(session_id, round_no, options, lang)
    await _send_creator_message(
        telegram_user_id=telegram_user_id,
        text=body,
        message=message,
        reply_markup=markup,
    )
