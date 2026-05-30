from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.models import Creator, SupportedLocale
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.locale_switch import switch_locale_with_pending_translation
from content_factory_bot.services.profile_artifacts import (
    has_translation_consent,
    record_translation_consent,
)

router = Router(name="settings")


def _label_for_locale(code: str, lang: str) -> str:
    if code == "en":
        return t("lang_en", lang)
    if code == "ru":
        return t("lang_ru", lang)
    return code.upper()


async def _supported_locale_codes() -> list[str]:
    async with session_scope() as session:
        rows = await session.execute(
            SupportedLocale.__table__.select().where(SupportedLocale.is_active.is_(True))
        )
        codes = [row.code for row in rows]
    return codes or ["en", "ru"]


@router.message(Command("settings"))
async def cmd_settings(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    codes = await _supported_locale_codes()
    buttons = [
        InlineKeyboardButton(
            text=_label_for_locale(code, lang),
            callback_data=f"settings:lang:{code}",
        )
        for code in codes
    ]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            buttons
        ]
    )
    await message.answer(t("settings_language", lang), reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("settings:lang:"))
async def set_language(callback: CallbackQuery, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    code = callback.data.split(":")[-1]
    codes = await _supported_locale_codes()
    if code not in codes:
        await callback.answer()
        return
    async with session_scope() as session:
        creator = await session.get(Creator, callback.from_user.id)
        current = creator.primary_language if creator else data.get(UI_LANG_KEY, "en")
        if creator is None:
            await callback.answer()
            return
        if code == current:
            await callback.message.answer(t("settings_saved", code))  # type: ignore[union-attr]
            await callback.answer()
            return
        if await has_translation_consent(
            session,
            telegram_user_id=callback.from_user.id,
            source_locale=current,
            target_locale=code,
        ):
            pass
        else:
            notice = t("settings_translation_consent_notice", current).format(
                source=current,
                target=code,
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=t("settings_translation_consent_yes", current),
                            callback_data=f"settings:consent:approve:{current}:{code}",
                        ),
                        InlineKeyboardButton(
                            text=t("settings_translation_consent_no", current),
                            callback_data=f"settings:consent:decline:{current}:{code}",
                        ),
                    ]
                ]
            )
            await callback.message.answer(notice, reply_markup=kb)  # type: ignore[union-attr]
            await callback.answer()
            return
    await switch_locale_with_pending_translation(
        telegram_user_id=callback.from_user.id,
        source_locale=current,
        target_locale=code,
    )
    await callback.message.answer(t("settings_translation_started", code))  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("settings:consent:"))
async def on_translation_consent(callback: CallbackQuery, **data) -> None:
    if not callback.from_user or not callback.data or not callback.message:
        return
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer()
        return
    _, _, decision, source, target = parts
    lang = data.get(UI_LANG_KEY, source)
    codes = await _supported_locale_codes()
    if source not in codes or target not in codes:
        await callback.answer()
        return
    if decision not in {"approve", "decline"}:
        await callback.answer()
        return
    approved = decision == "approve"
    async with session_scope() as session:
        await record_translation_consent(
            session,
            telegram_user_id=callback.from_user.id,
            source_locale=source,
            target_locale=target,
            approved=approved,
        )
    if not approved:
        await callback.message.answer(t("settings_translation_declined", lang))
        await callback.answer()
        return
    await switch_locale_with_pending_translation(
        telegram_user_id=callback.from_user.id,
        source_locale=source,
        target_locale=target,
    )
    await callback.message.answer(t("settings_translation_started", target))
    await callback.answer()
