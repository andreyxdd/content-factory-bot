from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.onboarding.format import format_question_body
from content_factory_bot.onboarding.keyboards import question_keyboard
from content_factory_bot.onboarding.loader import get_question, next_unanswered
from content_factory_bot.services.profile import get_answered_keys


async def show_question(
    event: Message | CallbackQuery,
    *,
    lang: str,
    question_key: str | None = None,
    state: FSMContext | None = None,
) -> None:
    uid = event.from_user.id  # type: ignore[union-attr]
    async with session_scope() as session:
        answered = await get_answered_keys(session, uid)

    q = get_question(question_key) if question_key else next_unanswered(answered)
    if q is None:
        text = t("onboarding_complete", lang)
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.message.answer(text)  # type: ignore[union-attr]
        return

    if state is not None:
        await state.update_data(current_question_key=q.key)

    body = format_question_body(q, lang)
    kb = question_keyboard(q, lang)
    if isinstance(event, Message):
        await event.answer(body, reply_markup=kb)
    else:
        await event.message.edit_text(body, reply_markup=kb)  # type: ignore[union-attr]
