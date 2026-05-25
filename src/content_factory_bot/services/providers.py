"""Provider connection persistence (OAuth callbacks)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.config import get_settings
from content_factory_bot.db.models import ProviderConnection
from content_factory_bot.services.credentials import encrypt_credentials


async def upsert_provider_connection(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    provider: str,
    credentials: str,
    external_account_id: str | None = None,
    status: str = "active",
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
