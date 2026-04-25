from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import ChallengeStep, StepStatus


async def get_step_counts(db: AsyncSession, goal_id: int) -> dict[str, int]:
    result = await db.execute(
        select(ChallengeStep.status, func.count())
        .where(ChallengeStep.goal_id == goal_id)
        .group_by(ChallengeStep.status)
    )
    counts = {"completed": 0, "skipped": 0, "pending": 0}
    for status, count in result.all():
        counts[status.value] = count
    counts["total"] = sum(counts.values())
    return counts