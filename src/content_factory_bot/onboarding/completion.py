"""Post-onboarding handoff: profile ready + providers screen."""

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.profile import apply_creator_preferences, mark_profile_ready


async def finish_onboarding_handoff(
    event: Message | CallbackQuery,
    *,
    lang: str,
    uid: int,
    state: FSMContext | None = None,
) -> None:
    async with session_scope() as session:
        await apply_creator_preferences(session, uid)
        await mark_profile_ready(session, uid)

    target: Message = event if isinstance(event, Message) else event.message  # type: ignore[assignment]
    await target.answer(t("onboarding_complete", lang))
    from content_factory_bot.handlers.providers_screen import send_providers_screen

    await send_providers_screen(target, lang=lang, uid=uid, show_skip=True)

    if state is not None:
        await state.clear()
