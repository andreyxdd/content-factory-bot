from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.models import ProviderKind
from content_factory_bot.db.session import session_scope
from content_factory_bot.handlers.providers_screen import send_providers_screen
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.providers import (
    disconnect_provider,
    parse_disconnect_arg,
    upsert_provider_connection,
)

router = Router(name="providers")


@router.message(Command("providers"))
async def cmd_providers(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    await send_providers_screen(
        message,
        lang=lang,
        uid=message.from_user.id,
        show_skip=False,
        intro_key="providers_intro",
    )


@router.message(Command("disconnect"))
async def cmd_disconnect(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = data.get(UI_LANG_KEY, "en")
    provider = parse_disconnect_arg(message.text)
    if provider is None:
        await message.answer(t("providers_disconnect_usage", lang))
        return
    uid = message.from_user.id
    async with session_scope() as session:
        ok = await disconnect_provider(session, telegram_user_id=uid, provider=provider)
    if ok:
        await message.answer(t("providers_disconnected", lang).format(provider=provider))
    else:
        await message.answer(t("providers_not_connected", lang).format(provider=provider))
    await send_providers_screen(message, lang=lang, uid=uid, show_skip=False)


@router.callback_query(F.data == "pv:skip")
async def on_skip(callback: CallbackQuery, **data) -> None:
    lang = data.get(UI_LANG_KEY, "en")
    await callback.message.answer(t("providers_skipped", lang))  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "pv:tg:link")
async def on_tg_link(callback: CallbackQuery, **data) -> None:
    lang = data.get(UI_LANG_KEY, "en")
    await callback.message.answer(t("providers_tg_forward", lang))  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("pv:dc:"))
async def on_disconnect_prompt(callback: CallbackQuery, **data) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return
    lang = data.get(UI_LANG_KEY, "en")
    parts = callback.data.split(":")
    if len(parts) == 4 and parts[3] == "yes":
        provider = parts[2]
        uid = callback.from_user.id if callback.from_user else 0
        async with session_scope() as session:
            ok = await disconnect_provider(
                session, telegram_user_id=uid, provider=provider
            )
        if ok:
            await callback.message.answer(
                t("providers_disconnected", lang).format(provider=provider)
            )
        await send_providers_screen(
            callback.message, lang=lang, uid=uid, show_skip=False  # type: ignore[arg-type]
        )
        await callback.answer()
        return

    if len(parts) != 3:
        await callback.answer()
        return
    provider = parts[2]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("providers_disconnect_confirm", lang),
                    callback_data=f"pv:dc:{provider}:yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("providers_disconnect_cancel", lang),
                    callback_data="pv:dc:cancel",
                )
            ],
        ]
    )
    await callback.message.answer(
        t("providers_disconnect_prompt", lang).format(provider=provider),
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "pv:dc:cancel")
async def on_disconnect_cancel(callback: CallbackQuery) -> None:
    await callback.answer(t("providers_disconnect_cancelled", "en"), show_alert=False)


async def _bot_is_admin(bot: Bot, chat_id: int) -> bool:
    me = await bot.get_me()
    member = await bot.get_chat_member(chat_id, me.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR)


@router.message(F.forward_from_chat)
async def on_forward_channel(message: Message, **data) -> None:
    if not message.from_user or not message.forward_from_chat:
        return
    chat = message.forward_from_chat
    if chat.type not in ("channel", "supergroup", "group"):
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = message.from_user.id
    if not message.bot or not await _bot_is_admin(message.bot, chat.id):
        await message.answer(t("providers_tg_not_admin", lang))
        return
    async with session_scope() as session:
        await upsert_provider_connection(
            session,
            telegram_user_id=uid,
            provider=ProviderKind.TELEGRAM,
            credentials='{"mode":"channel"}',
            external_account_id=str(chat.id),
            status="active",
        )
    await message.answer(
        t("providers_tg_linked", lang).format(title=chat.title or chat.id)
    )
    await send_providers_screen(message, lang=lang, uid=uid, show_skip=False)
