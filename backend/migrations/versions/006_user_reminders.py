"""add_reminder_settings_to_users

Revision ID: 006_user_reminders
Revises: 005_goal_total_steps
Create Date: 2026-04-27

"""

import sqlalchemy as sa
from alembic import op

revision: str = "006_user_reminders"
down_revision: str = "005_goal_total_steps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("reminders_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("reminder_time", sa.String(5), nullable=False, server_default="09:00"),
    )
    op.add_column(
        "users",
        sa.Column("last_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_reminder_sent_at")
    op.drop_column("users", "reminder_time")
    op.drop_column("users", "reminders_enabled")
