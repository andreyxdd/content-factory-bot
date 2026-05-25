"""Per-provider publish adapters — real HTTP when configured, stub otherwise."""

import json
import logging
from dataclasses import dataclass

import httpx
from aiogram import Bot

from content_factory_bot.db.models import ProviderConnection, ProviderKind
from content_factory_bot.services.credentials import decrypt_credentials

logger = logging.getLogger(__name__)


@dataclass
class AdapterResult:
    url: str | None
    error: str | None = None


class TelegramPublishAdapter:
    def __init__(self, bot: Bot | None) -> None:
        self._bot = bot

    async def publish(
        self,
        *,
        draft_text: str,
        connection: ProviderConnection,
        session_id: int,
    ) -> AdapterResult:
        chat_id = connection.external_account_id
        if not chat_id:
            return AdapterResult(url=None, error="telegram channel not linked")
        if self._bot is None:
            return AdapterResult(
                url=f"https://t.me/c/stub/{session_id}",
                error=None,
            )
        try:
            msg = await self._bot.send_message(chat_id=chat_id, text=draft_text[:4096])
            if msg.chat.username:
                url = f"https://t.me/{msg.chat.username}/{msg.message_id}"
            else:
                url = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{msg.message_id}"
            return AdapterResult(url=url)
        except Exception as e:
            logger.exception("telegram publish failed")
            return AdapterResult(url=None, error=str(e))


class InstagramPublishAdapter:
    async def publish(
        self,
        *,
        draft_text: str,
        connection: ProviderConnection,
        session_id: int,
    ) -> AdapterResult:
        raw = decrypt_credentials(
            connection.credentials_encrypted or "{}",
            encryption_key=_encryption_key(),
        )
        try:
            creds = json.loads(raw) if raw.startswith("{") else {"access_token": raw}
        except json.JSONDecodeError:
            creds = {"access_token": raw}
        token = creds.get("access_token")
        if not token or str(token).startswith("stub:"):
            return AdapterResult(
                url=f"https://instagram.com/stub/p/{session_id}",
                error=None,
            )
        # Graph API container flow (simplified single-step stub for dev accounts)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Production: create container → publish — here verify token only
                r = await client.get(
                    "https://graph.facebook.com/v21.0/me",
                    params={"access_token": token, "fields": "id"},
                )
                if r.status_code >= 400:
                    return AdapterResult(url=None, error=r.text[:500])
                user_id = r.json().get("id", "me")
                return AdapterResult(
                    url=f"https://instagram.com/p/stub-{session_id}-{user_id}",
                )
        except Exception as e:
            return AdapterResult(url=None, error=str(e))


class LinkedInPublishAdapter:
    async def publish(
        self,
        *,
        draft_text: str,
        connection: ProviderConnection,
        session_id: int,
    ) -> AdapterResult:
        raw = decrypt_credentials(
            connection.credentials_encrypted or "{}",
            encryption_key=_encryption_key(),
        )
        try:
            creds = json.loads(raw) if raw.startswith("{") else {"access_token": raw}
        except json.JSONDecodeError:
            creds = {"access_token": raw}
        token = creds.get("access_token")
        if not token or str(token).startswith("stub:"):
            return AdapterResult(
                url=f"https://linkedin.com/feed/stub/{session_id}",
                error=None,
            )
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0",
                    },
                    json={
                        "author": f"urn:li:person:{creds.get('person_id', 'stub')}",
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {"text": draft_text[:3000]},
                                "shareMediaCategory": "NONE",
                            }
                        },
                        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                    },
                )
                if r.status_code >= 400:
                    return AdapterResult(url=None, error=r.text[:500])
                post_id = r.headers.get("x-restli-id", f"stub-{session_id}")
                return AdapterResult(url=f"https://linkedin.com/feed/update/{post_id}")
        except Exception as e:
            return AdapterResult(url=None, error=str(e))


def _encryption_key() -> str:
    try:
        from content_factory_bot.config import get_settings

        return get_settings().credentials_encryption_key
    except Exception:
        return ""


def get_adapter(provider: str, *, bot: Bot | None) -> (
    TelegramPublishAdapter | InstagramPublishAdapter | LinkedInPublishAdapter
):
    if provider == ProviderKind.TELEGRAM:
        return TelegramPublishAdapter(bot)
    if provider == ProviderKind.INSTAGRAM:
        return InstagramPublishAdapter()
    if provider == ProviderKind.LINKEDIN:
        return LinkedInPublishAdapter()
    raise ValueError(f"unknown provider {provider}")
