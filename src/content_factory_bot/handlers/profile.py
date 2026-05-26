from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.onboarding.loader import load_questions
from content_factory_bot.services.profile import format_profile_summary, is_profile_ready

router = Router(name="profile")


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = message.from_user.id
    async with session_scope() as session:
        if not await is_profile_ready(session, uid):
            await message.answer(t("onboarding_required", lang))
            return
        summary = await format_profile_summary(session, uid, lang)

    rows = [
        [
            InlineKeyboardButton(
                text=(q.prompt(lang)[:40] + "…") if len(q.prompt(lang)) > 40 else q.prompt(lang),
                callback_data=f"profile:edit:{q.key}",
            )
        ]
        for q in load_questions()
    ]
    await message.answer(
        f"<b>{t('profile_title', lang)}</b>\n\n{summary}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("profile:edit:"))
async def edit_answer(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    lang = data.get(UI_LANG_KEY, "en")
    key = callback.data.split(":", 2)[2]
    from content_factory_bot.handlers.onboarding import OnboardingStates
    from content_factory_bot.onboarding.presenter import show_question

    await state.set_state(OnboardingStates.in_progress)
    await state.update_data(edit_key=key, custom_key=None)
    await show_question(callback, lang=lang, question_key=key, state=state)
    await callback.answer()
