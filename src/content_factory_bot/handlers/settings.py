from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.models import Creator
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY

router = Router(name="settings")


@router.message(Command("settings"))
async def cmd_settings(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("lang_en", lang), callback_data="settings:lang:en"),
                InlineKeyboardButton(text=t("lang_ru", lang), callback_data="settings:lang:ru"),
            ]
        ]
    )
    await message.answer(t("settings_language", lang), reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("settings:lang:"))
async def set_language(callback, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    code = callback.data.split(":")[-1]
    if code not in ("en", "ru"):
        await callback.answer()
        return
    async with session_scope() as session:
        creator = await session.get(Creator, callback.from_user.id)
        if creator:
            creator.primary_language = code
            await session.commit()
    lang = code
    await callback.message.answer(t("settings_saved", lang))  # type: ignore[union-attr]
    await callback.answer()
