from __future__ import annotations

from models import GoalStatus


PAUSED_STATUSES: set[GoalStatus] = {GoalStatus.frozen, GoalStatus.abandoned}


def is_paused(status: GoalStatus) -> bool:
    return status in PAUSED_STATUSES


def counts_toward_active_limit(status: GoalStatus) -> bool:
    return status == GoalStatus.active


def is_goal_in_today(status: GoalStatus) -> bool:
    return status == GoalStatus.active


def can_mutate_steps(status: GoalStatus) -> bool:
    return status == GoalStatus.active


def can_freeze(status: GoalStatus) -> bool:
    return status == GoalStatus.active


def can_unfreeze(status: GoalStatus) -> bool:
    return status in PAUSED_STATUSES
