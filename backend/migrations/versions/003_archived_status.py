"""add_goal_status_archived

Revision ID: 003_archived_status
Revises: 002_null_goal_idx
Create Date: 2026-04-22

"""
from alembic import op

revision: str = '003_archived_status'
down_revision: str = '002_null_goal_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE goalstatus ADD VALUE IF NOT EXISTS 'archived'")


def downgrade() -> None:
    pass