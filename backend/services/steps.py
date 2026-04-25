from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Deposit, DepositType, Goal, GoalStatus, Challenge, ChallengeStep, StepStatus
from services.events import PendingEvent, EVENT_STEP_COMPLETED, EVENT_STEP_SKIPPED, EVENT_SKIPPED_STEP_COMPLETED, EVENT_GOAL_COMPLETED, EVENT_DEPOSIT_MADE


async def get_today_step(db: AsyncSession, goal_id: int) -> ChallengeStep | None:
    result = await db.execute(
        select(ChallengeStep)
        .where(
            ChallengeStep.goal_id == goal_id,
            ChallengeStep.status == StepStatus.pending,
        )
        .order_by(ChallengeStep.step_number)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_today_steps_for_user(
    db: AsyncSession, user_id: int
) -> list[dict]:
    from services.goals import get_user_goals

    active_goals = await get_user_goals(db, user_id, status=GoalStatus.active)
    if not active_goals:
        return []

    goal_ids = [g.id for g in active_goals]

    challenge_result = await db.execute(
        select(Challenge).where(Challenge.goal_id.in_(goal_ids))
    )
    challenges = {c.goal_id: c for c in challenge_result.scalars().all()}

    pending_steps_result = await db.execute(
        select(ChallengeStep)
        .where(
            ChallengeStep.goal_id.in_(goal_ids),
            ChallengeStep.status == StepStatus.pending,
        )
        .order_by(ChallengeStep.goal_id, ChallengeStep.step_number)
    )
    all_pending = pending_steps_result.scalars().all()

    next_step_per_goal: dict[int, ChallengeStep] = {}
    seen_goals: set[int] = set()
    for step in all_pending:
        if step.goal_id not in seen_goals:
            next_step_per_goal[step.goal_id] = step
            seen_goals.add(step.goal_id)

    result = []
    for goal in active_goals:
        challenge = challenges.get(goal.id)
        total_steps = challenge.total_steps if challenge else 100
        result.append({
            "goal_id": goal.id,
            "goal_title": goal.title,
            "step": next_step_per_goal.get(goal.id),
            "total_steps": total_steps,
        })
    return result


async def get_step_by_id(db: AsyncSession, step_id: int) -> ChallengeStep | None:
    result = await db.execute(
        select(ChallengeStep).where(ChallengeStep.id == step_id)
    )
    return result.scalar_one_or_none()


async def get_step_by_id_with_lock(db: AsyncSession, step_id: int, goal_id: int) -> ChallengeStep | None:
    result = await db.execute(
        select(ChallengeStep)
        .where(ChallengeStep.id == step_id, ChallengeStep.goal_id == goal_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def skip_step(db: AsyncSession, step_id: int, goal_id: int, user_id: int) -> tuple[ChallengeStep | None, list[PendingEvent]]:
    events: list[PendingEvent] = []
    step = await get_step_by_id_with_lock(db, step_id, goal_id)
    if not step:
        return None, events

    if step.status != StepStatus.pending:
        return step, events

    step.status = StepStatus.skipped
    await db.flush()

    events.append(PendingEvent(EVENT_STEP_SKIPPED, step_id=step.id, goal_id=goal_id, user_id=user_id))
    return step, events


async def complete_step(db: AsyncSession, step_id: int, goal_id: int, user_id: int) -> tuple[ChallengeStep | None, list[PendingEvent]]:
    events: list[PendingEvent] = []
    step = await get_step_by_id_with_lock(db, step_id, goal_id)
    if not step:
        return None, events

    if step.status == StepStatus.completed:
        return step, events

    if step.status not in (StepStatus.pending, StepStatus.skipped):
        return None, events

    was_skipped = step.status == StepStatus.skipped

    deposit_amount = step.planned_amount

    step.was_skipped = was_skipped
    step.status = StepStatus.completed
    step.completed_at = datetime.now(timezone.utc)

    goal_result = await db.execute(
        select(Goal).where(Goal.id == goal_id).with_for_update()
    )
    goal = goal_result.scalar_one()
    goal.saved_amount += deposit_amount

    db.add(Deposit(
        goal_id=goal_id,
        step_id=step_id,
        amount=deposit_amount,
        type=DepositType.full,
    ))

    completion_events = _check_goal_completed(goal, user_id)
    events.extend(completion_events)

    await db.flush()

    if was_skipped:
        events.append(PendingEvent(EVENT_SKIPPED_STEP_COMPLETED, step_id=step.id, goal_id=goal.id, user_id=user_id))
    else:
        events.append(PendingEvent(EVENT_STEP_COMPLETED, step_id=step.id, goal_id=goal.id, user_id=user_id))
    events.append(PendingEvent(EVENT_DEPOSIT_MADE, goal_id=goal.id, amount=deposit_amount, user_id=user_id))
    return step, events


def _check_goal_completed(goal: Goal, user_id: int) -> list[PendingEvent]:
    events: list[PendingEvent] = []
    if goal.saved_amount >= goal.target_amount and goal.status != GoalStatus.completed:
        goal.status = GoalStatus.completed
        goal.completed_at = datetime.now(timezone.utc)
        events.append(PendingEvent(EVENT_GOAL_COMPLETED, goal_id=goal.id, user_id=user_id))
    return events