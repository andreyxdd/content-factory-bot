from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.api.oauth_signing import build_start_url
from content_factory_bot.config import get_settings
from content_factory_bot.db.models import ProviderKind

router = Router(name="providers")


@router.message(Command("providers"))
async def cmd_providers(message: Message) -> None:
    if not message.from_user:
        return
    settings = get_settings()
    uid = message.from_user.id

    if not settings.public_base_url or not settings.oauth_state_secret:
        await message.answer(
            "Provider connections need <code>PUBLIC_BASE_URL</code> and "
            "<code>OAUTH_STATE_SECRET</code> configured.\n"
            "See .planning/OAUTH-SETUP.md"
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
                    text="Connect Telegram channel (in-bot, Phase 4)",
                    callback_data="pv:tg:pending",
                )
            ],
        ]
    )
    await message.answer(
        "<b>Providers</b>\n\n"
        "Instagram / LinkedIn: open link, sign in, return here.\n"
        "Telegram: add bot as admin to your channel, then pick channel in Phase 4.\n\n"
        "v1 requires all three providers.",
        reply_markup=keyboard,
    )
