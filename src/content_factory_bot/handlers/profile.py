from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.models import PersonalityProfile
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.onboarding_engine import EDITABLE_FIELDS
from content_factory_bot.services.profile_artifacts import get_active_artifact_set
from content_factory_bot.services.profile import format_profile_summary, is_profile_ready

router = Router(name="profile")


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    await show_profile(
        message,
        state,
        uid=message.from_user.id,
        lang=data.get(UI_LANG_KEY, "en"),
    )


@router.message(Command("export_system_prompt"))
async def cmd_export_system_prompt(message: Message, **data) -> None:
    if not message.from_user:
        return
    uid = message.from_user.id
    lang = data.get(UI_LANG_KEY, "en")

    async with session_scope() as session:
        if not await is_profile_ready(session, uid):
            await message.answer(t("onboarding_required", lang))
            return
        active = await get_active_artifact_set(session, uid, lang)
        prompt_text = (active.system_prompt_text if active else "") or ""
        if not prompt_text.strip():
            profile = await session.get(PersonalityProfile, uid)
            prompt_text = (profile.system_prompt_text if profile else "") or ""

    if not prompt_text.strip():
        await message.answer(
            "System Prompt is not ready yet. Finish onboarding and retry /export_system_prompt."
            if lang != "ru"
            else "System Prompt пока не готов. Заверши онбординг и снова вызови /export_system_prompt."
        )
        return

    markdown = "# System Prompt\n\n" + prompt_text.strip() + "\n"
    filename = f"system-prompt-{uid}-{lang}.md"
    payload = BufferedInputFile(markdown.encode("utf-8"), filename=filename)
    await message.answer_document(
        payload,
        caption=(
            "System Prompt exported."
            if lang != "ru"
            else "System Prompt экспортирован."
        ),
    )


async def show_profile(
    target: Message,
    state: FSMContext,
    *,
    uid: int,
    lang: str,
) -> None:
    async with session_scope() as session:
        if not await is_profile_ready(session, uid):
            await target.answer(t("onboarding_required", lang))
            return
        summary = await format_profile_summary(session, uid, lang)

    rows = [
        [
            InlineKeyboardButton(
                text=(f.label(lang)[:40] + "…") if len(f.label(lang)) > 40 else f.label(lang),
                callback_data=f"profile:edit:{f.key}",
            )
        ]
        for f in EDITABLE_FIELDS
    ]
    await target.answer(
        f"<b>{t('profile_title', lang)}</b>\n\n{summary}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("profile:edit:"))
async def edit_answer(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    lang = data.get(UI_LANG_KEY, "en")
    key = callback.data.split(":", 2)[2]
    from content_factory_bot.handlers.onboarding import OnboardingStates, _send_prompt

    await state.set_state(OnboardingStates.in_progress)
    await state.update_data(current_step=key, pending_edit_key=key)
    await _send_prompt(callback.message, state, lang, key)  # type: ignore[arg-type]
    await callback.answer()
