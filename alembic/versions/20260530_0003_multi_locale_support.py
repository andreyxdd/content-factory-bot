"""multi-locale support tables

Revision ID: 20260530_0003
Revises: 20260530_0002
Create Date: 2026-05-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260530_0003"
down_revision: Union[str, Sequence[str], None] = "20260530_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supported_locales",
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_index(
        "uq_supported_locales_single_default",
        "supported_locales",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )
    op.create_table(
        "profile_artifact_sets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("profile_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("source_locale", sa.String(length=16), nullable=True),
        sa.Column("style_card_text", sa.Text(), nullable=True),
        sa.Column("values_block_text", sa.Text(), nullable=True),
        sa.Column("tribal_block_text", sa.Text(), nullable=True),
        sa.Column("system_prompt_text", sa.Text(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_user_id",
            "locale",
            "profile_version",
            name="uq_profile_artifact_set_version",
        ),
        sa.ForeignKeyConstraint(["locale"], ["supported_locales.code"]),
        sa.ForeignKeyConstraint(["source_locale"], ["supported_locales.code"]),
    )
    op.create_index(
        "ix_profile_artifact_sets_telegram_user_id",
        "profile_artifact_sets",
        ["telegram_user_id"],
    )
    op.create_index("ix_profile_artifact_sets_locale", "profile_artifact_sets", ["locale"])
    op.create_index(
        "uq_profile_artifact_sets_active_locale",
        "profile_artifact_sets",
        ["telegram_user_id", "locale"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_table(
        "translation_consent_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("source_locale", sa.String(length=16), nullable=False),
        sa.Column("target_locale", sa.String(length=16), nullable=False),
        sa.Column("policy_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_user_id",
            "source_locale",
            "target_locale",
            "policy_version",
            "approved",
            name="uq_translation_consent_scope",
        ),
        sa.ForeignKeyConstraint(["source_locale"], ["supported_locales.code"]),
        sa.ForeignKeyConstraint(["target_locale"], ["supported_locales.code"]),
    )
    op.create_index(
        "ix_translation_consent_records_telegram_user_id",
        "translation_consent_records",
        ["telegram_user_id"],
    )

    op.bulk_insert(
        sa.table(
            "supported_locales",
            sa.column("code", sa.String()),
            sa.column("display_name", sa.String()),
            sa.column("is_active", sa.Boolean()),
            sa.column("is_default", sa.Boolean()),
        ),
        [
            {"code": "en", "display_name": "English", "is_active": True, "is_default": True},
            {"code": "ru", "display_name": "Russian", "is_active": True, "is_default": False},
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_translation_consent_records_telegram_user_id",
        table_name="translation_consent_records",
    )
    op.drop_table("translation_consent_records")
    op.drop_index(
        "uq_profile_artifact_sets_active_locale",
        table_name="profile_artifact_sets",
    )
    op.drop_index("ix_profile_artifact_sets_locale", table_name="profile_artifact_sets")
    op.drop_index("ix_profile_artifact_sets_telegram_user_id", table_name="profile_artifact_sets")
    op.drop_table("profile_artifact_sets")
    op.drop_index("uq_supported_locales_single_default", table_name="supported_locales")
    op.drop_table("supported_locales")
