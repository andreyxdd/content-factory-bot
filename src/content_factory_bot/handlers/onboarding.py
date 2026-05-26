from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.onboarding.format import parse_text_answer
from content_factory_bot.onboarding.loader import get_question, load_questions
from content_factory_bot.onboarding.presenter import show_question
from content_factory_bot.services.creators import ensure_creator
from content_factory_bot.services.profile import (
    apply_creator_preferences,
    get_answered_keys,
    mark_profile_ready,
    save_answer,
)

router = Router(name="onboarding")


class OnboardingStates(StatesGroup):
    in_progress = State()


async def _lang(event: Message | CallbackQuery, data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


async def _after_answer(
    event: Message | CallbackQuery,
    state: FSMContext,
    *,
    lang: str,
    uid: int,
) -> None:
    async with session_scope() as session:
        answered = await get_answered_keys(session, uid)
        required = {q.key for q in load_questions()}
        fsm = await state.get_data()

        if fsm.get("edit_key"):
            await apply_creator_preferences(session, uid)
            await mark_profile_ready(session, uid)
            await state.clear()
            text = t("profile_updated", lang)
            if isinstance(event, CallbackQuery):
                await event.message.answer(text)  # type: ignore[union-attr]
            else:
                await event.answer(text)
            return

        if required.issubset(answered):
            await apply_creator_preferences(session, uid)
            await mark_profile_ready(session, uid)
            await state.clear()
            text = t("onboarding_complete", lang)
            if isinstance(event, CallbackQuery):
                await event.message.answer(text)  # type: ignore[union-attr]
            else:
                await event.answer(text)
            return

    await state.set_state(OnboardingStates.in_progress)
    await show_question(event, lang=lang, state=state)


@router.message(Command("onboarding"))
async def cmd_onboarding(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    lang = await _lang(message, data)
    async with session_scope() as session:
        await ensure_creator(
            session,
            telegram_user_id=message.from_user.id,
            language_code=message.from_user.language_code,
        )
    await state.set_state(OnboardingStates.in_progress)
    await state.update_data(edit_key=None)
    await show_question(message, lang=lang, state=state)


@router.callback_query(F.data.startswith("ob:"))
async def on_option(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    lang = await _lang(callback, data)
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    _, key, choice = parts
    q = get_question(key)
    if q is None:
        await callback.answer()
        return

    idx = int(choice)
    label = q.option_label(lang, idx)
    uid = callback.from_user.id
    async with session_scope() as session:
        await save_answer(session, uid, key, label, idx, False)

    await _after_answer(callback, state, lang=lang, uid=uid)
    await callback.answer()


@router.message(OnboardingStates.in_progress, F.text)
async def on_text_answer(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user or not message.text:
        return
    if message.text.startswith("/"):
        return

    lang = await _lang(message, data)
    fsm = await state.get_data()
    key = fsm.get("current_question_key")
    if not key:
        return

    q = get_question(key)
    if q is None:
        return

    parsed = parse_text_answer(q, lang, message.text)
    if parsed is None:
        return

    label, idx, is_custom = parsed
    uid = message.from_user.id
    async with session_scope() as session:
        await save_answer(session, uid, key, label, idx, is_custom)

    await _after_answer(message, state, lang=lang, uid=uid)
