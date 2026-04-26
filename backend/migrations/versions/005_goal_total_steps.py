"""add_total_steps_to_goals

Revision ID: 005_goal_total_steps
Revises: 004_frozen_status
Create Date: 2026-04-26

"""

import sqlalchemy as sa
from alembic import op

revision: str = "005_goal_total_steps"
down_revision: str = "004_frozen_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "goals",
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="100"),
    )
    # Backfill from challenges table (works on both PostgreSQL and SQLite)
    op.execute(
        "UPDATE goals SET total_steps = ("
        "  SELECT total_steps FROM challenges WHERE challenges.goal_id = goals.id"
        ") WHERE EXISTS ("
        "  SELECT 1 FROM challenges WHERE challenges.goal_id = goals.id"
        ")"
    )


def downgrade() -> None:
    op.drop_column("goals", "total_steps")
