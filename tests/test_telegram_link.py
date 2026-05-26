from content_factory_bot.api.telegram_link import telegram_bot_open_url


def test_telegram_bot_open_url_with_configured_username(monkeypatch) -> None:
    from content_factory_bot.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("BOT_USERNAME", "yours_content_bot")
    monkeypatch.setenv("BOT_TOKEN", "")
    get_settings.cache_clear()

    assert telegram_bot_open_url() == "https://t.me/yours_content_bot"

    get_settings.cache_clear()
