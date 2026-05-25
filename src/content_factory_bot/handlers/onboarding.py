from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.onboarding.loader import get_question, load_questions
from content_factory_bot.onboarding.presenter import show_question
from content_factory_bot.services.creators import ensure_creator
from content_factory_bot.services.profile import (
    apply_creator_preferences,
    get_answered_keys,
    is_profile_ready,
    mark_profile_ready,
    save_answer,
)

router = Router(name="onboarding")


class OnboardingStates(StatesGroup):
    in_progress = State()
    custom_reply = State()


async def _lang(event: Message | CallbackQuery, data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


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
    await show_question(message, lang=lang)


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

    if choice == "custom":
        await state.set_state(OnboardingStates.custom_reply)
        await state.update_data(custom_key=key)
        await callback.message.answer(t("onboarding_custom_prompt", lang))  # type: ignore[union-attr]
        await callback.answer()
        return

    idx = int(choice)
    label = q.option_label(lang, idx)
    uid = callback.from_user.id
    async with session_scope() as session:
        await save_answer(session, uid, key, label, idx, False)
        answered = await get_answered_keys(session, uid)
        required = {q.key for q in load_questions()}

        fsm = await state.get_data()
        if fsm.get("edit_key"):
            await apply_creator_preferences(session, uid)
            await mark_profile_ready(session, uid)
            await state.clear()
            await callback.message.answer(t("profile_updated", lang))  # type: ignore[union-attr]
            await callback.answer()
            return

        if required.issubset(answered):
            await apply_creator_preferences(session, uid)
            await mark_profile_ready(session, uid)
            await state.clear()
            await callback.message.answer(t("onboarding_complete", lang))  # type: ignore[union-attr]
            await callback.answer()
            return

    await show_question(callback, lang=lang)
    await callback.answer()


@router.message(OnboardingStates.custom_reply)
async def on_custom_text(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user or not message.text:
        return
    lang = await _lang(message, data)
    fsm = await state.get_data()
    key = fsm.get("custom_key")
    if not key:
        return
    uid = message.from_user.id
    async with session_scope() as session:
        await save_answer(session, uid, key, message.text, None, True)
        answered = await get_answered_keys(session, uid)
        required = {q.key for q in load_questions()}

        if fsm.get("edit_key"):
            await apply_creator_preferences(session, uid)
            await mark_profile_ready(session, uid)
            await state.clear()
            await message.answer(t("profile_updated", lang))
            return

        if required.issubset(answered):
            await apply_creator_preferences(session, uid)
            await mark_profile_ready(session, uid)
            await state.clear()
            await message.answer(t("onboarding_complete", lang))
            return

    await state.set_state(OnboardingStates.in_progress)
    await show_question(message, lang=lang)


