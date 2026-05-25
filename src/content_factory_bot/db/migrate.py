"""Run Alembic migrations from the repository root."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parents[3]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    return cfg


def run_upgrade_head() -> None:
    command.upgrade(_alembic_config(), "head")


def run() -> None:
    run_upgrade_head()
