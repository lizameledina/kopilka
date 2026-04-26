from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Goal, GoalStatus, Challenge, ChallengeType
from schemas import GoalResponse
from services.events import (
    PendingEvent,
    EVENT_GOAL_CREATED,
    EVENT_GOAL_FROZEN,
    EVENT_GOAL_UNFROZEN,
)
from services.challenge_strategies import get_challenge_strategy
from services.goal_rules import can_freeze, can_unfreeze

MAX_ACTIVE_GOALS = 3

ARCHIVABLE_STATUSES = {
    GoalStatus.active,
    GoalStatus.frozen,
    GoalStatus.abandoned,
    GoalStatus.completed,
}


def goal_to_response(goal: Goal) -> GoalResponse:
    status = goal.status
    # Treat legacy abandoned as frozen in all API responses
    if status == GoalStatus.abandoned:
        status = GoalStatus.frozen
    return GoalResponse(
        id=goal.id,
        title=goal.title,
        target_amount=goal.target_amount,
        saved_amount=goal.saved_amount,
        status=status.value,
        total_steps=goal.total_steps,
        completed_at=goal.completed_at.isoformat() if goal.completed_at else None,
    )


async def create_goal(
    db: AsyncSession,
    user_id: int,
    title: str,
    target_amount: int,
    distribution: str,
    step_count: int = 100,
) -> tuple[Goal, list[PendingEvent]]:
    active_goals_result = await db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.status == GoalStatus.active)
        .with_for_update()
    )
    active_goals = list(active_goals_result.scalars().all())
    if len(active_goals) >= MAX_ACTIVE_GOALS:
        raise ValueError(f"Максимум {MAX_ACTIVE_GOALS} активных целей")

    goal = Goal(
        user_id=user_id,
        title=title,
        target_amount=target_amount,
        saved_amount=0,
        status=GoalStatus.active,
        total_steps=step_count,
    )
    db.add(goal)
    await db.flush()

    challenge = Challenge(
        goal_id=goal.id,
        type=ChallengeType.envelope,
        config={"distribution": distribution},
        total_steps=step_count,
    )
    db.add(challenge)
    await db.flush()

    strategy = get_challenge_strategy(ChallengeType.envelope.value)
    steps = strategy.generate_steps(
        challenge_id=challenge.id,
        goal_id=goal.id,
        target_amount=target_amount,
        count=step_count,
        distribution=distribution,
    )
    db.add_all(steps)
    await db.flush()

    events = [PendingEvent(EVENT_GOAL_CREATED, goal_id=goal.id, user_id=user_id)]
    return goal, events


async def get_user_goals(
    db: AsyncSession, user_id: int, status: GoalStatus | None = None
) -> list[Goal]:
    query = select(Goal).where(Goal.user_id == user_id)
    if status:
        query = query.where(Goal.status == status)
    else:
        query = query.where(Goal.status != GoalStatus.archived)
    query = query.order_by(Goal.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_goal(db: AsyncSession, goal_id: int, user_id: int) -> Goal | None:
    result = await db.execute(
        select(Goal).where(
            Goal.id == goal_id,
            Goal.user_id == user_id,
            Goal.status != GoalStatus.archived,
        )
    )
    return result.scalar_one_or_none()


async def get_current_goal(db: AsyncSession, user_id: int) -> Goal | None:
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.status == GoalStatus.active)
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def archive_goal(db: AsyncSession, goal_id: int, user_id: int) -> Goal | None:
    goal = await get_goal(db, goal_id, user_id)
    if not goal or goal.status not in ARCHIVABLE_STATUSES:
        return None
    goal.status = GoalStatus.archived
    await db.flush()
    return goal


async def freeze_goal(db: AsyncSession, goal_id: int, user_id: int) -> tuple[Goal | None, list[PendingEvent]]:
    events: list[PendingEvent] = []
    result = await db.execute(
        select(Goal)
        .where(Goal.id == goal_id, Goal.user_id == user_id)
        .with_for_update()
    )
    goal = result.scalar_one_or_none()
    if not goal or not can_freeze(goal.status):
        return None, events

    goal.status = GoalStatus.frozen
    await db.flush()
    events.append(PendingEvent(EVENT_GOAL_FROZEN, goal_id=goal.id, user_id=user_id))
    return goal, events


async def unfreeze_goal(db: AsyncSession, goal_id: int, user_id: int) -> tuple[Goal | None, list[PendingEvent]]:
    events: list[PendingEvent] = []
    result = await db.execute(
        select(Goal)
        .where(Goal.id == goal_id, Goal.user_id == user_id)
        .with_for_update()
    )
    goal = result.scalar_one_or_none()
    if not goal or not can_unfreeze(goal.status):
        return None, events

    active_goals_result = await db.execute(
        select(Goal.id)
        .where(Goal.user_id == user_id, Goal.status == GoalStatus.active)
        .with_for_update()
    )
    active_goal_ids = list(active_goals_result.scalars().all())
    if len(active_goal_ids) >= MAX_ACTIVE_GOALS:
        raise ValueError(
            "У тебя уже есть 3 активные цели. Заверши или заморозь одну из них, чтобы разморозить эту."
        )

    goal.status = GoalStatus.active
    await db.flush()
    events.append(PendingEvent(EVENT_GOAL_UNFROZEN, goal_id=goal.id, user_id=user_id))
    return goal, events


async def get_goal_by_id(db: AsyncSession, goal_id: int) -> Goal | None:
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    return result.scalar_one_or_none()
