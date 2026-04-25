"""create_all_tables

Revision ID: 001_create_all
Revises: 
Create Date: 2026-04-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_create_all'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    op.create_table('goals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('target_amount', sa.BigInteger(), nullable=False),
        sa.Column('saved_amount', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.Enum('active', 'completed', 'abandoned', name='goalstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_goals_user_id', 'goals', ['user_id'], unique=False)
    op.create_index('ix_goals_status', 'goals', ['status'], unique=False)
    op.create_index('ix_goals_user_id_status', 'goals', ['user_id', 'status'], unique=False)

    op.create_table('challenges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('envelope', name='challengetype'), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('total_steps', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_challenges_goal_id', 'challenges', ['goal_id'], unique=True)

    op.create_table('challenge_steps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('planned_amount', sa.BigInteger(), nullable=False),
        sa.Column('was_skipped', sa.Boolean(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'completed', 'skipped', name='stepstatus'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id'], ),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_challenge_steps_goal_id', 'challenge_steps', ['goal_id'], unique=False)
    op.create_index('ix_challenge_steps_goal_id_status', 'challenge_steps', ['goal_id', 'status'], unique=False)

    op.create_table('deposits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('type', sa.Enum('full', name='deposittype'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['step_id'], ['challenge_steps.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deposits_goal_id', 'deposits', ['goal_id'], unique=False)

    op.create_table('user_streaks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=True),
        sa.Column('best_streak', sa.Integer(), nullable=True),
        sa.Column('last_activity_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_streaks_user_id', 'user_streaks', ['user_id'], unique=True)

    op.create_table('user_achievements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_code', sa.String(length=50), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=True),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'achievement_code', 'goal_id', name='uq_user_achievement_per_goal'),
    )
    op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'], unique=False)

    op.create_table('activity_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_activity_log_user_id', 'activity_log', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('activity_log')
    op.drop_table('user_achievements')
    op.drop_table('user_streaks')
    op.drop_table('deposits')
    op.drop_table('challenge_steps')
    op.drop_table('challenges')
    op.drop_table('goals')
    op.drop_table('users')

    op.execute("DROP TYPE IF EXISTS goalstatus")
    op.execute("DROP TYPE IF EXISTS challengetype")
    op.execute("DROP TYPE IF EXISTS stepstatus")
    op.execute("DROP TYPE IF EXISTS deposittype")