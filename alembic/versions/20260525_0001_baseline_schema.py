"""baseline schema

Revision ID: 20260525_0001
Revises:
Create Date: 2026-05-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260525_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "creators",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("primary_language", sa.String(length=8), nullable=False),
        sa.Column("review_enabled", sa.Boolean(), nullable=False),
        sa.Column("research_default_enabled", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("telegram_user_id"),
    )
    op.create_table(
        "personality_profiles",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("ready", sa.Boolean(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("telegram_user_id"),
    )
    op.create_table(
        "profile_answers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("question_key", sa.String(length=64), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("option_index", sa.Integer(), nullable=True),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_profile_answers_telegram_user_id"),
        "profile_answers",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_table(
        "allowlist_entries",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("added_by", sa.String(length=64), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("telegram_user_id"),
    )
    op.create_table(
        "content_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("web_research", sa.Boolean(), nullable=False),
        sa.Column("cover_generation", sa.Boolean(), nullable=False),
        sa.Column("destinations_json", sa.Text(), nullable=True),
        sa.Column("research_brief", sa.Text(), nullable=True),
        sa.Column("final_draft_text", sa.Text(), nullable=True),
        sa.Column("cover_storage_ref", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_content_sessions_telegram_user_id"),
        "content_sessions",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_table(
        "session_inputs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("input_type", sa.String(length=16), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("storage_ref", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_session_inputs_session_id"),
        "session_inputs",
        ["session_id"],
        unique=False,
    )
    op.create_table(
        "draft_rounds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("round_no", sa.Integer(), nullable=False),
        sa.Column("options_json", sa.Text(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=True),
        sa.Column("is_refinement", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_draft_rounds_session_id"),
        "draft_rounds",
        ["session_id"],
        unique=False,
    )
    op.create_table(
        "published_artifacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_url", sa.String(length=512), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_published_artifacts_session_id"),
        "published_artifacts",
        ["session_id"],
        unique=False,
    )
    op.create_table(
        "provider_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("external_account_id", sa.String(length=128), nullable=True),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
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
    )
    op.create_index(
        op.f("ix_provider_connections_telegram_user_id"),
        "provider_connections",
        ["telegram_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_provider_connections_telegram_user_id"),
        table_name="provider_connections",
    )
    op.drop_table("provider_connections")
    op.drop_index(op.f("ix_published_artifacts_session_id"), table_name="published_artifacts")
    op.drop_table("published_artifacts")
    op.drop_index(op.f("ix_draft_rounds_session_id"), table_name="draft_rounds")
    op.drop_table("draft_rounds")
    op.drop_index(op.f("ix_session_inputs_session_id"), table_name="session_inputs")
    op.drop_table("session_inputs")
    op.drop_index(op.f("ix_content_sessions_telegram_user_id"), table_name="content_sessions")
    op.drop_table("content_sessions")
    op.drop_table("allowlist_entries")
    op.drop_index(op.f("ix_profile_answers_telegram_user_id"), table_name="profile_answers")
    op.drop_table("profile_answers")
    op.drop_table("personality_profiles")
    op.drop_table("creators")
