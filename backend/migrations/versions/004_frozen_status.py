"""add_goal_status_frozen

Revision ID: 004_frozen_status
Revises: 003_archived_status
Create Date: 2026-04-24

"""

from alembic import op

revision: str = "004_frozen_status"
down_revision: str = "003_archived_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE goalstatus ADD VALUE IF NOT EXISTS 'frozen'")


def downgrade() -> None:
    pass

