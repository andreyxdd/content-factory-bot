from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.api.oauth_signing import build_start_url
from content_factory_bot.config import get_settings
from content_factory_bot.db.models import ProviderKind
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.providers import upsert_provider_connection

router = Router(name="providers")


async def _provider_status_lines(uid: int) -> list[str]:
    from sqlalchemy import select

    from content_factory_bot.db.models import ProviderConnection

    lines = []
    async with session_scope() as session:
        result = await session.execute(
            select(ProviderConnection).where(
                ProviderConnection.telegram_user_id == uid
            )
        )
        conns = {c.provider: c for c in result.scalars().all()}
    for prov in (ProviderKind.TELEGRAM, ProviderKind.INSTAGRAM, ProviderKind.LINKEDIN):
        c = conns.get(prov)
        status = c.status if c else "not connected"
        lines.append(f"• <b>{prov}</b>: {status}")
    return lines


@router.message(Command("providers"))
async def cmd_providers(message: Message, **data) -> None:
    if not message.from_user:
        return
    settings = get_settings()
    uid = message.from_user.id
    lang = data.get(UI_LANG_KEY, "en")

    lines = await _provider_status_lines(uid)
    body = "<b>Providers</b>\n\n" + "\n".join(lines) + "\n\n"

    if not settings.public_base_url or not settings.oauth_state_secret:
        await message.answer(
            body + t("providers_need_oauth_env", lang),
        )
        return

    ig_url = build_start_url(
        public_base_url=settings.public_base_url,
        secret=settings.oauth_state_secret,
        telegram_user_id=uid,
        provider=ProviderKind.INSTAGRAM,
    )
    li_url = build_start_url(
        public_base_url=settings.public_base_url,
        secret=settings.oauth_state_secret,
        telegram_user_id=uid,
        provider=ProviderKind.LINKEDIN,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Connect Instagram", url=ig_url)],
            [InlineKeyboardButton(text="Connect LinkedIn", url=li_url)],
            [
                InlineKeyboardButton(
                    text=t("providers_connect_telegram", lang),
                    callback_data="pv:tg:link",
                )
            ],
        ]
    )
    await message.answer(body + t("providers_help", lang), reply_markup=keyboard)


@router.callback_query(F.data == "pv:tg:link")
async def on_tg_link(callback: CallbackQuery, **data) -> None:
    lang = data.get(UI_LANG_KEY, "en")
    await callback.message.answer(t("providers_tg_forward", lang))  # type: ignore[union-attr]
    await callback.answer()


@router.message(F.forward_from_chat)
async def on_forward_channel(message: Message, **data) -> None:
    if not message.from_user or not message.forward_from_chat:
        return
    chat = message.forward_from_chat
    if chat.type not in ("channel", "supergroup", "group"):
        return
    lang = data.get(UI_LANG_KEY, "en")
    uid = message.from_user.id
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
