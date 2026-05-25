from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import AllowlistEntry


async def is_allowlisted(session: AsyncSession, telegram_user_id: int) -> bool:
    result = await session.execute(
        select(AllowlistEntry.telegram_user_id).where(
            AllowlistEntry.telegram_user_id == telegram_user_id
        )
    )
    return result.scalar_one_or_none() is not None


async def seed_allowlist(
    session: AsyncSession,
    telegram_user_ids: frozenset[int],
    *,
    added_by: str = "env:ALLOWLIST_TELEGRAM_IDS",
) -> int:
    """Insert ids from deploy env; skip existing. Returns count of new rows."""
    if not telegram_user_ids:
        return 0
    added = 0
    for user_id in telegram_user_ids:
        existing = await session.get(AllowlistEntry, user_id)
        if existing is None:
            session.add(
                AllowlistEntry(
                    telegram_user_id=user_id,
                    added_by=added_by,
                )
            )
            added += 1
    await session.commit()
    return added
