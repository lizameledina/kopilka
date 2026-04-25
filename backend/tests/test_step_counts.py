import pytest
import pytest_asyncio
from sqlalchemy import select, func

from models import ChallengeStep, StepStatus


@pytest.mark.asyncio
async def test_step_counts_all_pending(db, goal_with_steps):
    from services.step_counts import get_step_counts
    goal, challenge, steps = goal_with_steps

    counts = await get_step_counts(db, goal.id)
    assert counts["pending"] == 5
    assert counts["completed"] == 0
    assert counts["skipped"] == 0
    assert counts["total"] == 5


@pytest.mark.asyncio
async def test_step_counts_mixed(db, goal_with_steps):
    from services.step_counts import get_step_counts
    goal, challenge, steps = goal_with_steps

    steps[0].status = StepStatus.completed
    steps[1].status = StepStatus.completed
    steps[2].status = StepStatus.skipped
    await db.flush()

    counts = await get_step_counts(db, goal.id)
    assert counts["completed"] == 2
    assert counts["skipped"] == 1
    assert counts["pending"] == 2
    assert counts["total"] == 5


@pytest.mark.asyncio
async def test_step_counts_all_completed(db, goal_with_steps):
    from services.step_counts import get_step_counts
    goal, challenge, steps = goal_with_steps

    for s in steps:
        s.status = StepStatus.completed
    await db.flush()

    counts = await get_step_counts(db, goal.id)
    assert counts["completed"] == 5
    assert counts["pending"] == 0
    assert counts["skipped"] == 0
    assert counts["total"] == 5