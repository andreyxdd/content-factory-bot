"""Provider connection persistence and queries."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.config import get_settings
from content_factory_bot.db.models import ProviderConnection, ProviderKind
from content_factory_bot.services.credentials import encrypt_credentials

ACTIVE = "active"


async def upsert_provider_connection(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    provider: str,
    credentials: str,
    external_account_id: str | None = None,
    status: str = ACTIVE,
) -> ProviderConnection:
    result = await session.execute(
        select(ProviderConnection).where(
            ProviderConnection.telegram_user_id == telegram_user_id,
            ProviderConnection.provider == provider,
        )
    )
    row = result.scalar_one_or_none()
    key = get_settings().credentials_encryption_key
    stored = encrypt_credentials(credentials, encryption_key=key)
    if row is None:
        row = ProviderConnection(
            telegram_user_id=telegram_user_id,
            provider=provider,
            status=status,
            credentials_encrypted=stored,
            external_account_id=external_account_id,
        )
        session.add(row)
    else:
        row.status = status
        row.credentials_encrypted = stored
        row.external_account_id = external_account_id
    await session.commit()
    await session.refresh(row)
    return row


async def get_connections_map(
    session: AsyncSession, telegram_user_id: int
) -> dict[str, ProviderConnection]:
    result = await session.execute(
        select(ProviderConnection).where(
            ProviderConnection.telegram_user_id == telegram_user_id
        )
    )
    return {c.provider: c for c in result.scalars().all()}


async def list_active_providers(
    session: AsyncSession, telegram_user_id: int
) -> list[str]:
    conns = await get_connections_map(session, telegram_user_id)
    return [
        prov
        for prov in (ProviderKind.TELEGRAM, ProviderKind.INSTAGRAM, ProviderKind.LINKEDIN)
        if (c := conns.get(prov)) is not None and c.status == ACTIVE
    ]


async def count_active_providers(session: AsyncSession, telegram_user_id: int) -> int:
    return len(await list_active_providers(session, telegram_user_id))


async def is_setup_complete(session: AsyncSession, telegram_user_id: int) -> bool:
    return await count_active_providers(session, telegram_user_id) >= 1


async def disconnect_provider(
    session: AsyncSession, *, telegram_user_id: int, provider: str
) -> bool:
    if provider not in (
        ProviderKind.TELEGRAM,
        ProviderKind.INSTAGRAM,
        ProviderKind.LINKEDIN,
    ):
        return False
    result = await session.execute(
        delete(ProviderConnection).where(
            ProviderConnection.telegram_user_id == telegram_user_id,
            ProviderConnection.provider == provider,
        )
    )
    await session.commit()
    return result.rowcount > 0


def parse_disconnect_arg(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    raw = parts[1].strip().lower()
    aliases = {
        "tg": ProviderKind.TELEGRAM,
        "telegram": ProviderKind.TELEGRAM,
        "ig": ProviderKind.INSTAGRAM,
        "instagram": ProviderKind.INSTAGRAM,
        "li": ProviderKind.LINKEDIN,
        "linkedin": ProviderKind.LINKEDIN,
    }
    return aliases.get(raw)
