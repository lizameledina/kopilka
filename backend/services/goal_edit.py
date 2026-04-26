from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Goal, GoalStatus, Challenge, ChallengeStep, Deposit, UserAchievement, StepStatus
from services.events import (
    PendingEvent,
    EVENT_GOAL_TITLE_CHANGED,
    EVENT_GOAL_AMOUNT_CHANGED,
    EVENT_GOAL_STEPS_CHANGED,
    EVENT_ENVELOPES_REDISTRIBUTED,
    EVENT_GOAL_RESET,
)
from services.distribution_strategies import get_strategy

MAX_STEP_COUNT = 365
EDITABLE_STATUSES = {GoalStatus.active, GoalStatus.frozen}


async def _get_challenge(db: AsyncSession, goal_id: int) -> Challenge:
    result = await db.execute(select(Challenge).where(Challenge.goal_id == goal_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise ValueError("Challenge not found")
    return challenge


async def _get_completed_info(db: AsyncSession, goal_id: int) -> tuple[int, int]:
    """Returns (completed_count, max_completed_step_number)."""
    result = await db.execute(
        select(func.count(), func.max(ChallengeStep.step_number))
        .where(
            ChallengeStep.goal_id == goal_id,
            ChallengeStep.status == StepStatus.completed,
        )
    )
    row = result.one()
    count = row[0] or 0
    max_num = row[1] or 0
    return count, max_num


async def _redistribute_remaining(
    db: AsyncSession,
    challenge: Challenge,
    goal_id: int,
    new_target: int,
    new_count: int,
    distribution: str,
    saved_amount: int,
) -> None:
    """Delete pending/skipped steps and regenerate new ones starting after the last completed step."""
    completed_count, max_completed_num = await _get_completed_info(db, goal_id)

    await db.execute(
        delete(ChallengeStep).where(
            ChallengeStep.goal_id == goal_id,
            ChallengeStep.status.in_([StepStatus.pending, StepStatus.skipped]),
        )
    )

    remaining_count = new_count - completed_count
    remaining_amount = new_target - saved_amount

    if remaining_count <= 0 or remaining_amount <= 0:
        challenge.total_steps = new_count
        return

    strategy = get_strategy(distribution)
    amounts = strategy.distribute(remaining_amount, remaining_count)

    new_steps = []
    for i, amount in enumerate(amounts):
        new_steps.append(
            ChallengeStep(
                challenge_id=challenge.id,
                goal_id=goal_id,
                step_number=max_completed_num + i + 1,
                planned_amount=amount,
                status=StepStatus.pending,
            )
        )
    db.add_all(new_steps)
    challenge.total_steps = new_count


async def edit_goal(
    db: AsyncSession,
    goal_id: int,
    user_id: int,
    *,
    title: str | None = None,
    target_amount: int | None = None,
    step_count: int | None = None,
    distribution: str | None = None,
) -> tuple[Goal, list[PendingEvent]]:
    result = await db.execute(
        select(Goal)
        .where(Goal.id == goal_id, Goal.user_id == user_id)
        .with_for_update()
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise ValueError("Goal not found")
    if goal.status not in EDITABLE_STATUSES:
        raise ValueError("Можно редактировать только активные или замороженные цели")

    challenge = await _get_challenge(db, goal_id)
    completed_count, _ = await _get_completed_info(db, goal_id)
    events: list[PendingEvent] = []
    needs_redistribute = False

    if title is not None and title != goal.title:
        old_title = goal.title
        goal.title = title
        events.append(PendingEvent(
            EVENT_GOAL_TITLE_CHANGED,
            goal_id=goal_id, user_id=user_id,
            old_title=old_title, new_title=title,
        ))

    effective_target = target_amount if target_amount is not None else goal.target_amount
    effective_count = step_count if step_count is not None else challenge.total_steps
    effective_dist = distribution or (challenge.config or {}).get("distribution", "equal")

    if target_amount is not None and target_amount != goal.target_amount:
        if target_amount < goal.saved_amount:
            raise ValueError("Новая сумма не может быть меньше уже накопленного")
        old_amount = goal.target_amount
        goal.target_amount = target_amount
        needs_redistribute = True
        events.append(PendingEvent(
            EVENT_GOAL_AMOUNT_CHANGED,
            goal_id=goal_id, user_id=user_id,
            old_amount=old_amount, new_amount=target_amount,
        ))

    if step_count is not None and step_count != challenge.total_steps:
        if step_count < completed_count:
            raise ValueError(f"Новое количество конвертов ({step_count}) не может быть меньше уже завершённых ({completed_count})")
        old_count = challenge.total_steps
        needs_redistribute = True
        events.append(PendingEvent(
            EVENT_GOAL_STEPS_CHANGED,
            goal_id=goal_id, user_id=user_id,
            old_count=old_count, new_count=step_count,
        ))

    if distribution is not None and distribution != (challenge.config or {}).get("distribution"):
        needs_redistribute = True

    if needs_redistribute:
        await _redistribute_remaining(
            db, challenge, goal_id,
            new_target=effective_target,
            new_count=effective_count,
            distribution=effective_dist,
            saved_amount=goal.saved_amount,
        )
        challenge.config = {**(challenge.config or {}), "distribution": effective_dist}
        goal.total_steps = challenge.total_steps
        events.append(PendingEvent(
            EVENT_ENVELOPES_REDISTRIBUTED,
            goal_id=goal_id, user_id=user_id,
        ))

    await db.flush()
    return goal, events


async def preview_goal_edit(
    db: AsyncSession,
    goal_id: int,
    user_id: int,
    *,
    title: str | None = None,
    target_amount: int | None = None,
    step_count: int | None = None,
    distribution: str | None = None,
) -> dict:
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        return {"was": {}, "will_be": {}, "warnings": [], "error": "Цель не найдена"}
    if goal.status not in EDITABLE_STATUSES:
        return {"was": {}, "will_be": {}, "warnings": [], "error": "Можно редактировать только активные или замороженные цели"}

    challenge = await _get_challenge(db, goal_id)
    completed_count, _ = await _get_completed_info(db, goal_id)
    current_dist = (challenge.config or {}).get("distribution", "equal")

    effective_target = target_amount if target_amount is not None else goal.target_amount
    effective_count = step_count if step_count is not None else challenge.total_steps
    effective_dist = distribution or current_dist

    error: str | None = None
    warnings: list[str] = []

    if target_amount is not None and target_amount < goal.saved_amount:
        error = f"Новая сумма ({target_amount:,} ₽) не может быть меньше уже накопленного ({goal.saved_amount:,} ₽)"
    if step_count is not None and step_count < completed_count:
        error = f"Новое количество конвертов ({step_count}) не может быть меньше уже завершённых ({completed_count})"

    remaining_steps = effective_count - completed_count
    was = {
        "title": goal.title,
        "target_amount": goal.target_amount,
        "saved_amount": goal.saved_amount,
        "step_count": challenge.total_steps,
        "completed_steps": completed_count,
        "remaining_steps": challenge.total_steps - completed_count,
        "distribution": current_dist,
    }
    will_be = {
        "title": title if title is not None else goal.title,
        "target_amount": effective_target,
        "remaining_amount": effective_target - goal.saved_amount,
        "step_count": effective_count,
        "completed_steps": completed_count,
        "remaining_steps": remaining_steps,
        "distribution": effective_dist,
    }

    return {"was": was, "will_be": will_be, "warnings": warnings, "error": error}


async def reset_goal(
    db: AsyncSession,
    goal_id: int,
    user_id: int,
    *,
    distribution: str | None = None,
    step_count: int | None = None,
    target_amount: int | None = None,
) -> tuple[Goal, list[PendingEvent]]:
    result = await db.execute(
        select(Goal)
        .where(Goal.id == goal_id, Goal.user_id == user_id)
        .with_for_update()
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise ValueError("Goal not found")
    if goal.status not in EDITABLE_STATUSES:
        raise ValueError("Можно сбросить только активные или замороженные цели")

    challenge = await _get_challenge(db, goal_id)
    old_saved = goal.saved_amount

    # Delete all steps, deposits, and goal-scoped achievements
    await db.execute(delete(ChallengeStep).where(ChallengeStep.goal_id == goal_id))
    await db.execute(delete(Deposit).where(Deposit.goal_id == goal_id))
    await db.execute(
        delete(UserAchievement).where(
            UserAchievement.goal_id == goal_id,
            UserAchievement.user_id == user_id,
        )
    )

    effective_target = target_amount if target_amount is not None else goal.target_amount
    effective_count = step_count if step_count is not None else challenge.total_steps
    effective_dist = distribution or (challenge.config or {}).get("distribution", "equal")

    goal.saved_amount = 0
    goal.completed_at = None
    goal.target_amount = effective_target
    goal.total_steps = effective_count
    if goal.status == GoalStatus.frozen:
        goal.status = GoalStatus.active

    challenge.total_steps = effective_count
    challenge.config = {**(challenge.config or {}), "distribution": effective_dist}

    strategy = get_strategy(effective_dist)
    amounts = strategy.distribute(effective_target, effective_count)
    new_steps = [
        ChallengeStep(
            challenge_id=challenge.id,
            goal_id=goal_id,
            step_number=i + 1,
            planned_amount=amount,
            status=StepStatus.pending,
        )
        for i, amount in enumerate(amounts)
    ]
    db.add_all(new_steps)
    await db.flush()

    events = [PendingEvent(
        EVENT_GOAL_RESET,
        goal_id=goal_id, user_id=user_id,
        old_saved_amount=old_saved,
    )]
    return goal, events
