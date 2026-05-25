from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

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
    await message.answer(f"{t('welcome', lang)}\n\n{detected}\n\n{hint}")


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
