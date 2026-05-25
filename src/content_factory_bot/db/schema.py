from content_factory_bot.config import get_settings
from content_factory_bot.db.session import create_tables


async def ensure_schema() -> None:
    """Apply schema in dev when AUTO_CREATE_TABLES=true; prod uses cfbot-migrate."""
    if get_settings().auto_create_tables:
        await create_tables()
