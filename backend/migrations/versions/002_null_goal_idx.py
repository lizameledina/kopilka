"""add_null_goal_partial_index

Revision ID: 002_null_goal_idx
Revises: 001_create_all
Create Date: 2026-04-22

"""
from alembic import op

revision: str = '002_null_goal_idx'
down_revision: str = '001_create_all'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_achievement_null_goal "
        "ON user_achievements (user_id, achievement_code) "
        "WHERE goal_id IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_user_achievement_null_goal")