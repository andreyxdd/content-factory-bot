"""profile artifacts for onboarding

Revision ID: 20260530_0002
Revises: 20260525_0001
Create Date: 2026-05-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260530_0002"
down_revision: Union[str, Sequence[str], None] = "20260525_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "personality_profiles",
        sa.Column("style_card_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "personality_profiles",
        sa.Column("values_block_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "personality_profiles",
        sa.Column("tribal_block_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "personality_profiles",
        sa.Column("system_prompt_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("personality_profiles", "system_prompt_text")
    op.drop_column("personality_profiles", "tribal_block_text")
    op.drop_column("personality_profiles", "values_block_text")
    op.drop_column("personality_profiles", "style_card_text")
