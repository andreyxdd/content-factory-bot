from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.models import Creator, SupportedLocale
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.creator_prompt_addition import (
    clear_system_prompt_addition,
    get_system_prompt_addition,
    set_system_prompt_addition,
)
from content_factory_bot.services.locale_switch import switch_locale_with_pending_translation
from content_factory_bot.services.profile_artifacts import (
    has_translation_consent,
    record_translation_consent,
)
from content_factory_bot.services.system_prompt import MAX_SYSTEM_PROMPT_ADDITION_LEN

router = Router(name="settings")


class SettingsStates(StatesGroup):
    waiting_prompt_addition = State()


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


def _settings_keyboard(lang: str, *, has_addition: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.append(
        [
            InlineKeyboardButton(
                text=t("settings_prompt_addition_edit", lang),
                callback_data="settings:prompt_addition",
            )
        ]
    )
    if has_addition:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("settings_prompt_addition_clear", lang),
                    callback_data="settings:prompt_clear",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _settings_message_text(uid: int, lang: str) -> str:
    async with session_scope() as session:
        addition = await get_system_prompt_addition(session, uid)
    text = t("settings_language", lang) + "\n\n" + t("settings_prompt_addition_hint", lang)
    if addition:
        preview = addition[:160] + ("…" if len(addition) > 160 else "")
        text += "\n\n" + t("settings_prompt_addition_current", lang).format(
            preview=preview
        )
    return text


@router.message(Command("settings"))
async def cmd_settings(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = message.from_user.id
    codes = await _supported_locale_codes()
    lang_buttons = [
        InlineKeyboardButton(
            text=_label_for_locale(code, lang),
            callback_data=f"settings:lang:{code}",
        )
        for code in codes
    ]
    async with session_scope() as session:
        has_addition = bool(await get_system_prompt_addition(session, uid))
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            lang_buttons,
            *_settings_keyboard(lang, has_addition=has_addition).inline_keyboard,
        ]
    )
    await message.answer(await _settings_message_text(uid, lang), reply_markup=kb)


@router.callback_query(F.data == "settings:prompt_addition")
async def start_prompt_addition(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.message:
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = callback.from_user.id
    async with session_scope() as session:
        current = await get_system_prompt_addition(session, uid)
    prompt = t("settings_prompt_addition_prompt", lang).format(
        max_len=MAX_SYSTEM_PROMPT_ADDITION_LEN
    )
    if current:
        preview = current[:300] + ("…" if len(current) > 300 else "")
        prompt += "\n\n" + t("settings_prompt_addition_current", lang).format(
            preview=preview
        )
    await state.set_state(SettingsStates.waiting_prompt_addition)
    await callback.message.answer(prompt)
    await callback.answer()


@router.message(SettingsStates.waiting_prompt_addition, F.text)
async def save_prompt_addition(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user or not message.text:
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = message.from_user.id
    text = message.text.strip()
    if text.startswith("/"):
        if text.split()[0] == "/cancel":
            await state.clear()
            await message.answer(t("cancel_fsm_cleared", lang))
        return
    async with session_scope() as session:
        err = await set_system_prompt_addition(session, uid, text)
    await state.clear()
    if err == "too_long":
        await message.answer(
            t("settings_prompt_addition_too_long", lang).format(
                max_len=MAX_SYSTEM_PROMPT_ADDITION_LEN
            )
        )
        return
    if err == "no_creator":
        await message.answer(t("onboarding_required", lang))
        return
    await message.answer(t("settings_prompt_addition_saved", lang))


@router.callback_query(F.data == "settings:prompt_clear")
async def clear_prompt_addition(callback: CallbackQuery, **data) -> None:
    if not callback.from_user or not callback.message:
        return
    lang = data.get(UI_LANG_KEY, "en")
    async with session_scope() as session:
        await clear_system_prompt_addition(session, callback.from_user.id)
    await callback.message.answer(t("settings_prompt_addition_cleared", lang))
    await callback.answer()


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
