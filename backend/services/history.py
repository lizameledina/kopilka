from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Goal, ChallengeStep, StepStatus


async def get_goal_history(
    db: AsyncSession,
    goal_id: int,
    user_id: int,
    sort_by: str = "date",
    status_filter: str | None = None,
) -> list[dict] | None:
    goal_result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = goal_result.scalar_one_or_none()
    if not goal:
        return None

    query = select(ChallengeStep).where(ChallengeStep.goal_id == goal_id,
                                          ChallengeStep.status != StepStatus.pending)

    if status_filter == "completed":
        query = query.where(ChallengeStep.status == StepStatus.completed)
    elif status_filter == "skipped":
        query = query.where(ChallengeStep.status == StepStatus.skipped)
    elif status_filter == "recovered":
        query = query.where(
            ChallengeStep.status == StepStatus.completed,
            ChallengeStep.was_skipped.is_(True),
        )

    if sort_by == "number":
        query = query.order_by(ChallengeStep.step_number)
    else:
        query = query.order_by(ChallengeStep.completed_at.desc().nulls_last(), ChallengeStep.step_number)

    result = await db.execute(query)
    steps = result.scalars().all()

    items = []
    for s in steps:
        label = s.status.value
        if s.status == StepStatus.completed and s.was_skipped:
            label = "recovered"

        items.append({
            "id": s.id,
            "step_number": s.step_number,
            "planned_amount": s.planned_amount,
            "status": s.status.value,
            "label": label,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        })

    return items