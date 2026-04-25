import pytest
from sqlalchemy import select

from models import Goal, GoalStatus
from services.goals import unfreeze_goal


@pytest.mark.asyncio
async def test_unfreeze_frozen_goal_success(db, user):
    goal = Goal(
        user_id=user.id,
        title="Frozen",
        target_amount=10000,
        saved_amount=0,
        status=GoalStatus.frozen,
    )
    db.add(goal)
    await db.flush()

    updated, events = await unfreeze_goal(db, goal.id, user.id)
    assert updated is not None
    assert updated.status == GoalStatus.active
    assert any(e.name == "goal_unfrozen" for e in events)


@pytest.mark.asyncio
async def test_unfreeze_goal_wrong_user_returns_none(db, user, second_user):
    goal = Goal(
        user_id=second_user.id,
        title="Frozen other",
        target_amount=10000,
        saved_amount=0,
        status=GoalStatus.frozen,
    )
    db.add(goal)
    await db.flush()

    updated, events = await unfreeze_goal(db, goal.id, user.id)
    assert updated is None
    assert events == []


@pytest.mark.asyncio
async def test_unfreeze_blocked_by_active_limit(db, user):
    for i in range(3):
        g = Goal(
            user_id=user.id,
            title=f"Active {i}",
            target_amount=10000,
            saved_amount=0,
            status=GoalStatus.active,
        )
        db.add(g)

    frozen = Goal(
        user_id=user.id,
        title="Frozen",
        target_amount=10000,
        saved_amount=0,
        status=GoalStatus.frozen,
    )
    db.add(frozen)
    await db.flush()

    with pytest.raises(ValueError):
        await unfreeze_goal(db, frozen.id, user.id)

    result = await db.execute(select(Goal).where(Goal.id == frozen.id))
    reread = result.scalar_one()
    assert reread.status == GoalStatus.frozen

