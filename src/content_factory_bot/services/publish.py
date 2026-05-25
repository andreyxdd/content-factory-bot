"""Publish adapters — v1 stubs return synthetic URLs when credentials missing."""

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import ProviderConnection, ProviderKind, PublishedArtifact

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    provider: str
    url: str | None
    error: str | None = None


class PublishOrchestrator:
    async def publish_session(
        self,
        db: AsyncSession,
        *,
        session_id: int,
        telegram_user_id: int,
        draft_text: str,
        providers: list[str] | None = None,
    ) -> list[PublishResult]:
        target = providers or [
            ProviderKind.TELEGRAM,
            ProviderKind.INSTAGRAM,
            ProviderKind.LINKEDIN,
        ]
        results: list[PublishResult] = []
        for prov in target:
            conn = await self._get_connection(db, telegram_user_id, prov)
            if conn and conn.status == "active":
                url = f"https://example.com/{prov}/{session_id}"
                err = None
            else:
                url = f"https://stub.local/{prov}/session-{session_id}"
                err = None
            db.add(
                PublishedArtifact(
                    session_id=session_id,
                    provider=prov,
                    external_url=url,
                    error=err,
                )
            )
            results.append(PublishResult(provider=prov, url=url, error=err))
        await db.commit()
        return results

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
