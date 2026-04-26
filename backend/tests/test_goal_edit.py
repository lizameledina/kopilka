import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Goal, GoalStatus, Challenge, ChallengeType,
    ChallengeStep, StepStatus, UserAchievement,
)
from schemas import CreateGoalRequest
from services.goal_edit import edit_goal, preview_goal_edit, reset_goal, MAX_STEP_COUNT
from services.distribution_strategies import get_strategy


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

async def _make_goal(db, user, *, title="Test", target=10000, count=5, dist="equal", saved=0, status=GoalStatus.active):
    goal = Goal(
        user_id=user.id,
        title=title,
        target_amount=target,
        saved_amount=saved,
        status=status,
        total_steps=count,
    )
    db.add(goal)
    await db.flush()

    challenge = Challenge(
        goal_id=goal.id,
        type=ChallengeType.envelope,
        config={"distribution": dist},
        total_steps=count,
    )
    db.add(challenge)
    await db.flush()

    amounts = get_strategy(dist).distribute(target, count)
    steps = [
        ChallengeStep(
            challenge_id=challenge.id,
            goal_id=goal.id,
            step_number=i + 1,
            planned_amount=amount,
            status=StepStatus.pending,
        )
        for i, amount in enumerate(amounts)
    ]
    db.add_all(steps)
    await db.flush()

    return goal, challenge, steps


async def _complete_step(db, step, goal, amount):
    """Simulate completing a step (minimal, no events)."""
    step.status = StepStatus.completed
    goal.saved_amount += amount
    await db.flush()


async def _step_count(db, goal_id, status=None):
    q = select(func.count()).where(ChallengeStep.goal_id == goal_id)
    if status:
        q = q.where(ChallengeStep.status == status)
    return (await db.execute(q)).scalar()


# ---------------------------------------------------------------------------
# Tests: edit title only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_title_only_does_not_change_steps(db, user):
    goal, challenge, steps = await _make_goal(db, user)
    original_step_amounts = [s.planned_amount for s in steps]
    original_count = await _step_count(db, goal.id)

    edited, events = await edit_goal(db, goal.id, user.id, title="New Title")

    assert edited.title == "New Title"
    assert await _step_count(db, goal.id) == original_count
    # Verify amounts unchanged by re-querying
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.goal_id == goal.id)
        .order_by(ChallengeStep.step_number)
    )
    current_steps = result.scalars().all()
    assert [s.planned_amount for s in current_steps] == original_step_amounts
    assert any(e.name == "goal_title_changed" for e in events)


# ---------------------------------------------------------------------------
# Tests: edit target_amount
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_target_amount_redistributes_remaining(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    await _complete_step(db, steps[0], goal, steps[0].planned_amount)

    new_target = 20000
    edited, events = await edit_goal(db, goal.id, user.id, target_amount=new_target)

    assert edited.target_amount == new_target
    # saved_amount should be unchanged
    assert edited.saved_amount == steps[0].planned_amount

    # Pending steps should cover the remaining amount
    result = await db.execute(
        select(func.sum(ChallengeStep.planned_amount)).where(
            ChallengeStep.goal_id == goal.id,
            ChallengeStep.status == StepStatus.pending,
        )
    )
    pending_sum = result.scalar() or 0
    expected_remaining = new_target - edited.saved_amount
    assert pending_sum == expected_remaining


@pytest.mark.asyncio
async def test_edit_target_amount_below_saved_raises(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    await _complete_step(db, steps[0], goal, steps[0].planned_amount)

    with pytest.raises(ValueError, match="меньше уже накопленного"):
        await edit_goal(db, goal.id, user.id, target_amount=goal.saved_amount - 1)


# ---------------------------------------------------------------------------
# Tests: edit step_count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_step_count_redistributes_remaining(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    await _complete_step(db, steps[0], goal, steps[0].planned_amount)

    new_count = 10
    edited, events = await edit_goal(db, goal.id, user.id, step_count=new_count)

    assert edited.total_steps == new_count
    # completed stays 1, new pending should be new_count - 1 = 9
    assert await _step_count(db, goal.id, StepStatus.completed) == 1
    assert await _step_count(db, goal.id, StepStatus.pending) == new_count - 1


@pytest.mark.asyncio
async def test_edit_step_count_below_completed_raises(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    await _complete_step(db, steps[0], goal, steps[0].planned_amount)
    await _complete_step(db, steps[1], goal, steps[1].planned_amount)

    with pytest.raises(ValueError, match="меньше уже завершённых"):
        await edit_goal(db, goal.id, user.id, step_count=1)


# ---------------------------------------------------------------------------
# Tests: edit distribution only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_distribution_redistributes_with_new_strategy(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5, dist="equal")

    edited, events = await edit_goal(db, goal.id, user.id, distribution="ascending")

    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.goal_id == goal.id, ChallengeStep.status == StepStatus.pending)
        .order_by(ChallengeStep.step_number)
    )
    new_steps = result.scalars().all()
    assert len(new_steps) == 5
    amounts = [s.planned_amount for s in new_steps]
    # ascending should be non-decreasing
    assert amounts == sorted(amounts)
    assert any(e.name == "envelopes_redistributed" for e in events)


# ---------------------------------------------------------------------------
# Tests: frozen goal can still be edited
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_frozen_goal(db, user):
    goal, challenge, steps = await _make_goal(db, user, status=GoalStatus.frozen)
    edited, events = await edit_goal(db, goal.id, user.id, title="Frozen Edit")
    assert edited.title == "Frozen Edit"


# ---------------------------------------------------------------------------
# Tests: reset_goal
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reset_goal_clears_progress(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    await _complete_step(db, steps[0], goal, steps[0].planned_amount)
    await _complete_step(db, steps[1], goal, steps[1].planned_amount)

    old_saved = goal.saved_amount
    assert old_saved > 0

    reset, events = await reset_goal(db, goal.id, user.id)

    assert reset.saved_amount == 0
    assert reset.completed_at is None
    assert reset.status == GoalStatus.active
    assert await _step_count(db, goal.id, StepStatus.completed) == 0
    assert await _step_count(db, goal.id, StepStatus.pending) == 5
    assert any(e.name == "goal_reset" for e in events)


@pytest.mark.asyncio
async def test_reset_goal_deletes_goal_scoped_achievements(db, user):
    goal, challenge, steps = await _make_goal(db, user)

    # Add a goal-scoped achievement
    goal_ach = UserAchievement(user_id=user.id, achievement_code="steps_5", goal_id=goal.id)
    db.add(goal_ach)
    # Add a global achievement (no goal_id)
    global_ach = UserAchievement(user_id=user.id, achievement_code="first_step", goal_id=None)
    db.add(global_ach)
    await db.flush()

    await reset_goal(db, goal.id, user.id)

    # Goal-scoped achievement should be deleted
    result = await db.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == user.id,
            UserAchievement.goal_id == goal.id,
        )
    )
    assert result.scalars().all() == []

    # Global achievement should still exist
    result = await db.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == user.id,
            UserAchievement.goal_id.is_(None),
        )
    )
    globals_ = result.scalars().all()
    assert len(globals_) == 1
    assert globals_[0].achievement_code == "first_step"


@pytest.mark.asyncio
async def test_reset_frozen_goal_reactivates(db, user):
    goal, challenge, steps = await _make_goal(db, user, status=GoalStatus.frozen)
    reset, _ = await reset_goal(db, goal.id, user.id)
    assert reset.status == GoalStatus.active


# ---------------------------------------------------------------------------
# Tests: preview
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_preview_does_not_modify_db(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    original_target = goal.target_amount
    original_count = await _step_count(db, goal.id)

    preview = await preview_goal_edit(db, goal.id, user.id, target_amount=50000, step_count=10)

    # DB not modified
    await db.refresh(goal)
    assert goal.target_amount == original_target
    assert await _step_count(db, goal.id) == original_count

    assert preview["was"]["target_amount"] == 10000
    assert preview["will_be"]["target_amount"] == 50000
    assert preview["will_be"]["step_count"] == 10
    assert preview["error"] is None


@pytest.mark.asyncio
async def test_preview_returns_error_for_invalid_amount(db, user):
    goal, challenge, steps = await _make_goal(db, user, target=10000, count=5)
    await _complete_step(db, steps[0], goal, steps[0].planned_amount)

    preview = await preview_goal_edit(db, goal.id, user.id, target_amount=1)

    assert preview["error"] is not None
    assert "меньше уже накопленного" in preview["error"]


@pytest.mark.asyncio
async def test_preview_title_change(db, user):
    goal, challenge, steps = await _make_goal(db, user, title="Old")
    preview = await preview_goal_edit(db, goal.id, user.id, title="New")
    assert preview["was"]["title"] == "Old"
    assert preview["will_be"]["title"] == "New"
    assert preview["error"] is None


# ---------------------------------------------------------------------------
# Tests: schema validation (step_count limits)
# ---------------------------------------------------------------------------

def test_schema_step_count_max_is_365():
    req = CreateGoalRequest(title="T", target_amount=1000, step_count=365)
    assert req.step_count == 365


def test_schema_step_count_over_365_rejected():
    with pytest.raises(ValidationError):
        CreateGoalRequest(title="T", target_amount=1000, step_count=366)


def test_max_step_count_constant():
    assert MAX_STEP_COUNT == 365


# ---------------------------------------------------------------------------
# Tests: goal achievements endpoint no longer returns other_goal_achievements
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_goal_achievements_schema_no_other_goals():
    from schemas import GoalAchievementsResponse
    resp = GoalAchievementsResponse(
        goal_achievements=[],
        global_achievements=[],
    )
    assert not hasattr(resp, "other_goal_achievements") or getattr(resp, "other_goal_achievements", None) is None


# ---------------------------------------------------------------------------
# Tests: edit does not affect completed goals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_edit_completed_goal_raises(db, user):
    goal, challenge, steps = await _make_goal(db, user, status=GoalStatus.completed)
    with pytest.raises(ValueError, match="активные или замороженные"):
        await edit_goal(db, goal.id, user.id, title="New")


@pytest.mark.asyncio
async def test_reset_completed_goal_raises(db, user):
    goal, challenge, steps = await _make_goal(db, user, status=GoalStatus.completed)
    with pytest.raises(ValueError, match="активные или замороженные"):
        await reset_goal(db, goal.id, user.id)
