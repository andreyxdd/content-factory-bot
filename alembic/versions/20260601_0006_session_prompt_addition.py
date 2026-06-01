"""Add session_prompt_addition to content_sessions."""

from alembic import op
import sqlalchemy as sa

revision = "20260601_0006"
down_revision = "20260601_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_sessions",
        sa.Column("session_prompt_addition", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_sessions", "session_prompt_addition")
