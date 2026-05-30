from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.keyboards.draft import sessions_list_keyboard
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.content_session import (
    close_active_sessions,
    get_active_session,
    list_recent_sessions,
)
from content_factory_bot.services.creators import ensure_creator
from content_factory_bot.services.profile import is_profile_ready

router = Router(name="common")


def _start_first_time_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("start_btn_onboarding", lang),
                    callback_data="start:onboarding",
                )
            ]
        ]
    )


def _start_returning_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("start_btn_profile", lang),
                    callback_data="start:profile",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("start_btn_other_commands", lang),
                    callback_data="start:other",
                )
            ],
        ]
    )


def _start_other_commands_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("start_btn_new", lang), callback_data="start:new")],
            [
                InlineKeyboardButton(
                    text=t("start_btn_sessions", lang), callback_data="start:sessions"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("start_btn_providers", lang), callback_data="start:providers"
                )
            ],
            [InlineKeyboardButton(text=t("start_btn_help", lang), callback_data="start:help")],
            [InlineKeyboardButton(text=t("start_btn_back", lang), callback_data="start:back")],
        ]
    )


def _lang(message: Message, data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


@router.message(Command("start"))
async def cmd_start(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = _lang(message, data)
    uid = message.from_user.id

    async with session_scope() as session:
        await ensure_creator(
            session,
            telegram_user_id=uid,
            language_code=message.from_user.language_code,
        )

    detected = (
        t("locale_detected_ru", lang) if lang == "ru" else t("locale_detected_en", lang)
    )
    async with session_scope() as session:
        ready = await is_profile_ready(session, uid)
    hint = t("start_body", lang) if ready else t("start_need_onboarding", lang)
    locale_hint = t("start_change_language_hint", lang)
    kb = _start_returning_keyboard(lang) if ready else _start_first_time_keyboard(lang)
    await message.answer(
        f"{t('welcome', lang)}\n\n{detected}\n\n{hint}\n\n{locale_hint}",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("start:"))
async def on_start_menu(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    lang = data.get(UI_LANG_KEY, "en")
    action = callback.data.split(":", 1)[1]

    if action == "onboarding":
        from content_factory_bot.handlers.onboarding import cmd_onboarding

        await cmd_onboarding(callback.message, state, **data)  # type: ignore[arg-type]
        await callback.answer()
        return
    if action == "profile":
        from content_factory_bot.handlers.profile import cmd_profile

        await cmd_profile(callback.message, state, **data)  # type: ignore[arg-type]
        await callback.answer()
        return
    if action == "other":
        await callback.message.answer(
            t("start_other_commands_title", lang),
            reply_markup=_start_other_commands_keyboard(lang),
        )
        await callback.answer()
        return
    if action == "new":
        from content_factory_bot.handlers.content_session import cmd_new

        await cmd_new(callback.message, state, **data)  # type: ignore[arg-type]
        await callback.answer()
        return
    if action == "sessions":
        await cmd_sessions(callback.message, **data)  # type: ignore[arg-type]
        await callback.answer()
        return
    if action == "providers":
        from content_factory_bot.handlers.providers import cmd_providers

        await cmd_providers(callback.message, **data)  # type: ignore[arg-type]
        await callback.answer()
        return
    if action == "help":
        await cmd_help(callback.message, **data)  # type: ignore[arg-type]
        await callback.answer()
        return
    if action == "back":
        await callback.message.answer(
            t("start_returning_title", lang),
            reply_markup=_start_returning_keyboard(lang),
        )
        await callback.answer()
        return

    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, **data) -> None:
    await message.answer(t("help", _lang(message, data)))


@router.message(Command("sessions"))
async def cmd_sessions(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = _lang(message, data)
    uid = message.from_user.id
    async with session_scope() as session:
        rows = await list_recent_sessions(session, uid, limit=10)
    if not rows:
        await message.answer(t("sessions_empty", lang))
        return
    pairs = [(r.id, r.title, r.state) for r in rows]
    await message.answer(
        t("sessions_list", lang),
        reply_markup=sessions_list_keyboard(pairs, lang),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    lang = _lang(message, data)
    uid = message.from_user.id
    had_fsm = await state.get_state() is not None
    await state.clear()
    async with session_scope() as session:
        active = await get_active_session(session, uid)
        if active:
            await close_active_sessions(session, uid)
            await message.answer(t("cancel_session_closed", lang))
            return
    if had_fsm:
        await message.answer(t("cancel_fsm_cleared", lang))
        return
    await message.answer(t("cancel_idle", lang))
