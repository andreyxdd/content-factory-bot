"""Schema migration and boot DDL behavior (TDD pins for db-migrations phase)."""

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from content_factory_bot.config import get_settings
from content_factory_bot.db.migrate import _alembic_config, run_upgrade_head
from content_factory_bot.db.models import Base
from content_factory_bot.db.schema import ensure_schema

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_REVISION = "20260525_0001"
EXPECTED_TABLES = frozenset(Base.metadata.tables.keys())


@pytest.fixture
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ensure_schema_skips_create_tables_when_auto_create_disabled(
    clear_settings_cache: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTO_CREATE_TABLES", "false")
    get_settings.cache_clear()
    with patch(
        "content_factory_bot.db.schema.create_tables",
        new_callable=AsyncMock,
    ) as mock_create:
        await ensure_schema()
    mock_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_schema_runs_create_tables_when_auto_create_enabled(
    clear_settings_cache: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")
    get_settings.cache_clear()
    with patch(
        "content_factory_bot.db.schema.create_tables",
        new_callable=AsyncMock,
    ) as mock_create:
        await ensure_schema()
    mock_create.assert_awaited_once()


def test_alembic_config_points_at_repo_alembic_directory() -> None:
    cfg = _alembic_config()
    script_location = Path(cfg.get_main_option("script_location"))
    assert script_location.is_dir()
    assert (script_location / "env.py").is_file()
    assert (script_location / "versions" / "20260525_0001_baseline_schema.py").is_file()


def test_run_upgrade_head_invokes_alembic_upgrade() -> None:
    with patch("content_factory_bot.db.migrate.command.upgrade") as mock_upgrade:
        run_upgrade_head()
    mock_upgrade.assert_called_once()
    args, kwargs = mock_upgrade.call_args
    assert args[1] == "head"


def test_baseline_migration_defines_all_model_tables() -> None:
    migration_path = (
        REPO_ROOT / "alembic/versions/20260525_0001_baseline_schema.py"
    )
    source = migration_path.read_text()
    created = set(re.findall(r'op\.create_table\(\s*\n\s*"([^"]+)"', source))
    assert created == set(EXPECTED_TABLES)


def test_backup_script_is_valid_bash() -> None:
    script = REPO_ROOT / "deploy/scripts/backup-db.sh"
    assert script.is_file()
    subprocess.run(["bash", "-n", str(script)], check=True)


@pytest.mark.asyncio
async def test_api_lifespan_calls_ensure_schema_not_create_tables() -> None:
    from content_factory_bot.api.app import lifespan

    app = MagicMock()
    with (
        patch("content_factory_bot.api.app.init_db"),
        patch(
            "content_factory_bot.api.app.ensure_schema",
            new_callable=AsyncMock,
        ) as mock_ensure,
    ):
        async with lifespan(app):
            pass
    mock_ensure.assert_awaited_once()


def _integration_database_url() -> str | None:
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://cfbot:cfbot@127.0.0.1:5433/content_factory_test",
    )


async def _postgres_reachable(url: str) -> bool:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        await engine.dispose()


async def _reset_public_schema(url: str) -> None:
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


def _run_migrate_subprocess(database_url: str) -> None:
    """Prod path: sync subprocess, not inside pytest's event loop."""
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-c", "from content_factory_bot.db.migrate import run; run()"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


async def _fetch_schema_state(url: str) -> tuple[set[str], str]:
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        table_rows = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
            )
        )
        tables = {row[0] for row in table_rows}
        version_row = await conn.execute(text("SELECT version_num FROM alembic_version"))
        version = version_row.scalar_one()
    await engine.dispose()
    return tables, version


@pytest.mark.integration
def test_migrate_upgrade_head_creates_tables_and_version(
    clear_settings_cache: None,
) -> None:
    url = _integration_database_url()
    assert url is not None
    if not asyncio.run(_postgres_reachable(url)):
        pytest.skip("Postgres not reachable for integration test")

    asyncio.run(_reset_public_schema(url))
    _run_migrate_subprocess(url)
    _run_migrate_subprocess(url)

    tables, version = asyncio.run(_fetch_schema_state(url))
    assert tables == set(EXPECTED_TABLES)
    assert version == BASELINE_REVISION
