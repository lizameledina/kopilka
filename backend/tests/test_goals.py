import pytest
import pytest_asyncio
from sqlalchemy import select, func

from models import (
    Goal, GoalStatus, Challenge, ChallengeType,
    ChallengeStep, StepStatus, User, UserAchievement,
)
from services.distribution_strategies import get_strategy
from services.challenge_strategies import EnvelopeChallengeStrategy


@pytest.mark.asyncio
async def test_create_goal(db, user):
    goal = Goal(
        user_id=user.id,
        title="My Goal",
        target_amount=50000,
        saved_amount=0,
        status=GoalStatus.active,
    )
    db.add(goal)
    await db.flush()

    result = await db.execute(select(Goal).where(Goal.id == goal.id))
    found = result.scalar_one()
    assert found.title == "My Goal"
    assert found.target_amount == 50000
    assert found.status == GoalStatus.active


@pytest.mark.asyncio
async def test_create_goal_with_steps(db, user):
    goal = Goal(
        user_id=user.id,
        title="Step Goal",
        target_amount=10000,
        saved_amount=0,
        status=GoalStatus.active,
    )
    db.add(goal)
    await db.flush()

    challenge = Challenge(
        goal_id=goal.id,
        type=ChallengeType.envelope,
        config={"distribution": "equal"},
        total_steps=10,
    )
    db.add(challenge)
    await db.flush()

    strategy = EnvelopeChallengeStrategy()
    steps = strategy.generate_steps(
        challenge_id=challenge.id,
        goal_id=goal.id,
        target_amount=10000,
        count=10,
        distribution="equal",
    )
    db.add_all(steps)
    await db.flush()

    count_result = await db.execute(
        select(func.count()).select_from(ChallengeStep).where(ChallengeStep.goal_id == goal.id)
    )
    assert count_result.scalar() == 10

    sum_result = await db.execute(
        select(func.sum(ChallengeStep.planned_amount)).where(ChallengeStep.goal_id == goal.id)
    )
    assert sum_result.scalar() == 10000


@pytest.mark.asyncio
async def test_complete_step(db, goal_with_steps):
    goal, challenge, steps = goal_with_steps

    step = steps[0]
    assert step.status == StepStatus.pending

    step.status = StepStatus.completed
    step.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    goal.saved_amount += step.planned_amount
    await db.flush()

    await db.refresh(goal)
    assert goal.saved_amount > 0


@pytest.mark.asyncio
async def test_skip_step(db, goal_with_steps):
    goal, challenge, steps = goal_with_steps

    step = steps[0]
    step.status = StepStatus.skipped
    await db.flush()

    result = await db.execute(
        select(ChallengeStep).where(ChallengeStep.id == step.id)
    )
    updated = result.scalar_one()
    assert updated.status == StepStatus.skipped


@pytest.mark.asyncio
async def test_recover_skipped_step(db, goal_with_steps):
    goal, challenge, steps = goal_with_steps

    step = steps[0]
    step.status = StepStatus.skipped
    await db.flush()

    step.status = StepStatus.completed
    step.was_skipped = True
    step.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    goal.saved_amount += step.planned_amount
    await db.flush()

    result = await db.execute(
        select(ChallengeStep).where(ChallengeStep.id == step.id)
    )
    updated = result.scalar_one()
    assert updated.status == StepStatus.completed
    assert updated.was_skipped is True


@pytest.mark.asyncio
async def test_max_active_goals(db, user):
    for i in range(3):
        goal = Goal(
            user_id=user.id,
            title=f"Goal {i}",
            target_amount=10000,
            saved_amount=0,
            status=GoalStatus.active,
        )
        db.add(goal)
    await db.flush()

    result = await db.execute(
        select(func.count()).select_from(Goal).where(
            Goal.user_id == user.id,
            Goal.status == GoalStatus.active,
        )
    )
    assert result.scalar() == 3


@pytest.mark.asyncio
async def test_abandon_goal(db, user):
    goal = Goal(
        user_id=user.id,
        title="To Abandon",
        target_amount=10000,
        saved_amount=0,
        status=GoalStatus.active,
    )
    db.add(goal)
    await db.flush()

    goal.status = GoalStatus.abandoned
    await db.flush()

    result = await db.execute(select(Goal).where(Goal.id == goal.id))
    found = result.scalar_one()
    assert found.status == GoalStatus.abandoned