from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.models import Creator
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.content_session import get_active_session, start_session
from content_factory_bot.services.profile import is_profile_ready

router = Router(name="content_session")


class NewSessionStates(StatesGroup):
    setup = State()


def _setup_keyboard(lang: str, *, research: bool, cover: bool) -> InlineKeyboardMarkup:
    r = "✅ " if research else ""
    c = "✅ " if cover else ""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{r}{t('session_research', lang)}",
                    callback_data="cs:toggle:research",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{c}{t('session_cover', lang)}",
                    callback_data="cs:toggle:cover",
                )
            ],
            [InlineKeyboardButton(text=t("session_start", lang), callback_data="cs:start")],
        ]
    )


@router.message(Command("new"))
async def cmd_new(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = message.from_user.id
    async with session_scope() as session:
        if not await is_profile_ready(session, uid):
            await message.answer(t("onboarding_required", lang))
            return
        if await get_active_session(session, uid):
            await message.answer(t("session_active_exists", lang))
            return
        creator = await session.get(Creator, uid)
        research = creator.research_default_enabled if creator else True

    await state.set_state(NewSessionStates.setup)
    await state.update_data(research=research, cover=False)
    await message.answer(
        t("session_setup_intro", lang),
        reply_markup=_setup_keyboard(lang, research=research, cover=False),
    )


@router.callback_query(NewSessionStates.setup, F.data.startswith("cs:"))
async def on_session_setup(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = callback.from_user.id
    fsm = await state.get_data()
    research = bool(fsm.get("research", True))
    cover = bool(fsm.get("cover", False))

    if callback.data == "cs:toggle:research":
        research = not research
        await state.update_data(research=research)
        await callback.message.edit_reply_markup(  # type: ignore[union-attr]
            reply_markup=_setup_keyboard(lang, research=research, cover=cover)
        )
        await callback.answer()
        return

    if callback.data == "cs:toggle:cover":
        cover = not cover
        await state.update_data(cover=cover)
        await callback.message.edit_reply_markup(  # type: ignore[union-attr]
            reply_markup=_setup_keyboard(lang, research=research, cover=cover)
        )
        await callback.answer()
        return

    if callback.data == "cs:start":
        async with session_scope() as session:
            row = await start_session(
                session,
                uid,
                web_research=research,
                cover_generation=cover,
            )
        await state.clear()
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_send_input", lang).format(id=row.id)
        )
        await callback.answer()
        return

    await callback.answer()
