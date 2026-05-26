from unittest.mock import AsyncMock, patch

import pytest

from content_factory_bot.services.telegram_notify import notify_creator, notify_creator_markup


@pytest.mark.asyncio
async def test_notify_creator_sends_when_token_set() -> None:
    with (
        patch("content_factory_bot.services.telegram_notify.get_settings") as gs,
        patch("content_factory_bot.services.telegram_notify.Bot") as BotCls,
    ):
        gs.return_value.bot_token = "123:ABC"
        bot = AsyncMock()
        BotCls.return_value = bot
        bot.session.close = AsyncMock()
        ok = await notify_creator(99, "hello")
        assert ok is True
        bot.send_message.assert_awaited_once_with(99, "hello")
        bot.session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_notify_creator_markup_sends_keyboard() -> None:
    from aiogram.types import InlineKeyboardMarkup

    markup = InlineKeyboardMarkup(inline_keyboard=[])
    with (
        patch("content_factory_bot.services.telegram_notify.get_settings") as gs,
        patch("content_factory_bot.services.telegram_notify.Bot") as BotCls,
    ):
        gs.return_value.bot_token = "123:ABC"
        bot = AsyncMock()
        BotCls.return_value = bot
        bot.session.close = AsyncMock()
        ok = await notify_creator_markup(42, "pick", markup)
        assert ok is True
        bot.send_message.assert_awaited_once_with(42, "pick", reply_markup=markup)


@pytest.mark.asyncio
async def test_notify_creator_skips_without_token() -> None:
    with patch("content_factory_bot.services.telegram_notify.get_settings") as gs:
        gs.return_value.bot_token = ""
        ok = await notify_creator(99, "hello")
        assert ok is False
