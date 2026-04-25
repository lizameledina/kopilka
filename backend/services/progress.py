from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Goal, ChallengeStep
from services.step_counts import get_step_counts


async def get_progress(db: AsyncSession, goal_id: int) -> dict:
    goal_result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = goal_result.scalar_one()

    counts = await get_step_counts(db, goal_id)

    percent = round(goal.saved_amount / goal.target_amount * 100, 1) if goal.target_amount > 0 else 0

    return {
        "goal_id": goal.id,
        "title": goal.title,
        "target_amount": goal.target_amount,
        "saved_amount": goal.saved_amount,
        "percent": percent,
        "completed_steps": counts["completed"],
        "skipped_steps": counts["skipped"],
        "total_steps": counts["total"],
        "status": goal.status.value,
    }


async def get_steps_list(db: AsyncSession, goal_id: int) -> list[dict]:
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.goal_id == goal_id)
        .order_by(ChallengeStep.step_number)
    )
    steps = result.scalars().all()
    return [
        {
            "id": s.id,
            "step_number": s.step_number,
            "planned_amount": s.planned_amount,
            "status": s.status.value,
        }
        for s in steps
    ]