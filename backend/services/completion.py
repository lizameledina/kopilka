from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Goal, GoalStatus, UserStreak
from services.achievements import get_achievements_for_goal
from services.step_counts import get_step_counts


async def _get_goal_stats(db: AsyncSession, goal_id: int, user_id: int) -> dict | None:
    goal_result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = goal_result.scalar_one_or_none()
    if not goal:
        return None

    counts = await get_step_counts(db, goal_id)

    streak_result = await db.execute(select(UserStreak).where(UserStreak.user_id == user_id))
    streak = streak_result.scalar_one_or_none()

    duration_days = None
    if goal.completed_at and goal.created_at:
        duration_days = (goal.completed_at.date() - goal.created_at.date()).days

    return {
        "goal": goal,
        "counts": counts,
        "streak": streak,
        "duration_days": duration_days,
    }


async def get_completion_summary(db: AsyncSession, goal_id: int, user_id: int) -> dict | None:
    stats = await _get_goal_stats(db, goal_id, user_id)
    if not stats:
        return None

    goal = stats["goal"]
    if goal.status != GoalStatus.completed:
        return None

    counts = stats["counts"]
    streak = stats["streak"]

    achievements = await get_achievements_for_goal(db, user_id, goal_id)
    unlocked_achievements = [a for a in achievements if a["unlocked"]]

    return {
        "goal_id": goal.id,
        "title": goal.title,
        "target_amount": goal.target_amount,
        "saved_amount": goal.saved_amount,
        "percent": round(goal.saved_amount / goal.target_amount * 100, 1) if goal.target_amount > 0 else 0,
        "completed_steps": counts["completed"],
        "skipped_steps": counts["skipped"],
        "total_steps": counts["total"],
        "status": goal.status.value,
        "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
        "created_at": goal.created_at.isoformat(),
        "duration_days": stats["duration_days"] or 0,
        "current_streak": streak.current_streak if streak else 0,
        "best_streak": streak.best_streak if streak else 0,
        "achievements": unlocked_achievements,
    }


async def get_share_summary(db: AsyncSession, goal_id: int, user_id: int) -> dict | None:
    stats = await _get_goal_stats(db, goal_id, user_id)
    if not stats:
        return None

    goal = stats["goal"]
    counts = stats["counts"]
    streak = stats["streak"]

    return {
        "goal_id": goal.id,
        "title": goal.title,
        "target_amount": goal.target_amount,
        "saved_amount": goal.saved_amount,
        "percent": round(goal.saved_amount / goal.target_amount * 100, 1) if goal.target_amount > 0 else 0,
        "completed_steps": counts["completed"],
        "total_steps": counts["total"],
        "status": goal.status.value,
        "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
        "duration_days": stats["duration_days"],
        "current_streak": streak.current_streak if streak else 0,
        "best_streak": streak.best_streak if streak else 0,
    }