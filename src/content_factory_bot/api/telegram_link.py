"""Build t.me deep links back to the Telegram bot after OAuth."""

from functools import lru_cache

import httpx

from content_factory_bot.config import get_settings


@lru_cache(maxsize=4)
def _username_from_getme(bot_token: str) -> str:
    response = httpx.get(
        f"https://api.telegram.org/bot{bot_token}/getMe",
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError("Telegram getMe failed")
    username = data.get("result", {}).get("username") or ""
    if not username:
        raise RuntimeError("Telegram getMe returned no username")
    return username


def resolve_bot_username() -> str:
    settings = get_settings()
    configured = settings.bot_username.strip().lstrip("@")
    if configured:
        return configured
    token = settings.bot_token.strip()
    if token:
        return _username_from_getme(token)
    return ""


def telegram_bot_open_url(*, start: str | None = None) -> str:
    username = resolve_bot_username()
    if not username:
        raise RuntimeError(
            "Set BOT_USERNAME or BOT_TOKEN so OAuth can redirect to Telegram"
        )
    url = f"https://t.me/{username}"
    if start:
        url = f"{url}?start={start}"
    return url
