"""Publish to all session destinations with per-provider retry."""

import json
import logging
from dataclasses import dataclass

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import ContentSession, ProviderConnection, ProviderKind, PublishedArtifact
from content_factory_bot.services.publish.adapters import AdapterResult, get_adapter

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    provider: str
    url: str | None
    error: str | None = None


class PublishOrchestrator:
    def __init__(self, bot: Bot | None = None) -> None:
        self._bot = bot

    async def publish_session(
        self,
        db: AsyncSession,
        *,
        session_id: int,
        telegram_user_id: int,
        draft_text: str,
        providers: list[str] | None = None,
    ) -> list[PublishResult]:
        row = await db.get(ContentSession, session_id)
        target = providers or _destinations_from_session(row)
        if not target:
            target = await self._list_active_providers(db, telegram_user_id)

        results: list[PublishResult] = []
        for prov in target:
            conn = await self._get_connection(db, telegram_user_id, prov)
            adapter = get_adapter(prov, bot=self._bot)
            if conn is None or conn.status != "active":
                ar = AdapterResult(
                    url=f"https://stub.local/{prov}/session-{session_id}",
                    error="provider not connected",
                )
            else:
                ar = await adapter.publish(
                    draft_text=draft_text,
                    connection=conn,
                    session_id=session_id,
                )
                if ar.error:
                    ar = await adapter.publish(
                        draft_text=draft_text,
                        connection=conn,
                        session_id=session_id,
                    )
            db.add(
                PublishedArtifact(
                    session_id=session_id,
                    provider=prov,
                    external_url=ar.url,
                    error=ar.error,
                )
            )
            results.append(
                PublishResult(provider=prov, url=ar.url, error=ar.error)
            )
        await db.commit()
        return results

    async def _list_active_providers(
        self, db: AsyncSession, telegram_user_id: int
    ) -> list[str]:
        result = await db.execute(
            select(ProviderConnection.provider).where(
                ProviderConnection.telegram_user_id == telegram_user_id,
                ProviderConnection.status == "active",
            )
        )
        return list(result.scalars().all())

    async def _get_connection(
        self, db: AsyncSession, telegram_user_id: int, provider: str
    ) -> ProviderConnection | None:
        result = await db.execute(
            select(ProviderConnection).where(
                ProviderConnection.telegram_user_id == telegram_user_id,
                ProviderConnection.provider == provider,
            )
        )
        return result.scalar_one_or_none()


def _destinations_from_session(row: ContentSession | None) -> list[str]:
    if row is None or not row.destinations_json:
        return []
    try:
        data = json.loads(row.destinations_json)
        return list(data) if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
