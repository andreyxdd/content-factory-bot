"""Add optional system prompt addition on creators."""

from alembic import op
import sqlalchemy as sa

revision = "20260601_0005"
down_revision = "20260601_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "creators",
        sa.Column("system_prompt_addition", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("creators", "system_prompt_addition")
