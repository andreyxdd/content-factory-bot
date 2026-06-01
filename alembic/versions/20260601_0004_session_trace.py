"""Add session_trace_json to content_sessions."""

from alembic import op
import sqlalchemy as sa

revision = "20260601_0004"
down_revision = "20260530_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_sessions",
        sa.Column("session_trace_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_sessions", "session_trace_json")
