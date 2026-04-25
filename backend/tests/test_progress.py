import pytest
import pytest_asyncio
from sqlalchemy import select

from models import Goal, GoalStatus, ChallengeStep, StepStatus


@pytest.mark.asyncio
async def test_progress_counts(db, goal_with_steps):
    from services.progress import get_progress
    goal, challenge, steps = goal_with_steps

    progress = await get_progress(db, goal.id)
    assert progress["goal_id"] == goal.id
    assert progress["completed_steps"] == 0
    assert progress["skipped_steps"] == 0
    assert progress["total_steps"] == 5
    assert progress["percent"] == 0.0


@pytest.mark.asyncio
async def test_progress_with_completed(db, goal_with_steps):
    from services.progress import get_progress
    goal, challenge, steps = goal_with_steps

    steps[0].status = StepStatus.completed
    steps[1].status = StepStatus.completed
    steps[2].status = StepStatus.skipped
    goal.saved_amount = steps[0].planned_amount + steps[1].planned_amount
    await db.flush()

    progress = await get_progress(db, goal.id)
    assert progress["completed_steps"] == 2
    assert progress["skipped_steps"] == 1


@pytest.mark.asyncio
async def test_steps_list(db, goal_with_steps):
    from services.progress import get_steps_list
    goal, challenge, steps = goal_with_steps

    result = await get_steps_list(db, goal.id)
    assert len(result) == 5
    assert result[0]["status"] == "pending"
    assert result[0]["step_number"] == 1