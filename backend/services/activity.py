from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ActivityLog
from services.events import (
    on,
    EVENT_STEP_COMPLETED,
    EVENT_STEP_SKIPPED,
    EVENT_SKIPPED_STEP_COMPLETED,
    EVENT_GOAL_CREATED,
    EVENT_GOAL_COMPLETED,
    EVENT_GOAL_FROZEN,
    EVENT_GOAL_UNFROZEN,
    EVENT_ACHIEVEMENT_UNLOCKED,
)

LOGGABLE_EVENTS = {
    EVENT_STEP_COMPLETED: "step_completed",
    EVENT_STEP_SKIPPED: "step_skipped",
    EVENT_SKIPPED_STEP_COMPLETED: "skipped_step_completed",
    EVENT_GOAL_CREATED: "goal_created",
    EVENT_GOAL_COMPLETED: "goal_completed",
    EVENT_GOAL_FROZEN: "goal_frozen",
    EVENT_GOAL_UNFROZEN: "goal_unfrozen",
    EVENT_ACHIEVEMENT_UNLOCKED: "achievement_unlocked",
}


async def log_event(db: AsyncSession, user_id: int, event_type: str, payload: dict | None = None):
    entry = ActivityLog(
        user_id=user_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(entry)
    await db.flush()


async def get_activity(db: AsyncSession, user_id: int, limit: int = 20) -> list[dict]:
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "created_at": e.created_at.isoformat(),
            "payload": e.payload,
        }
        for e in entries
    ]


async def _handle_event(event_type: str, user_id: int, **kwargs):
    from database import async_session
    payload = {k: v for k, v in kwargs.items() if k != "user_id"}
    async with async_session() as db:
        try:
            await log_event(db, user_id, event_type, payload or None)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


def _make_handler(event_type: str):
    async def handler(user_id: int, **kwargs):
        await _handle_event(event_type, user_id, **kwargs)
    return handler


for EVENT_NAME, EVENT_TYPE in LOGGABLE_EVENTS.items():
    on(EVENT_NAME)(_make_handler(EVENT_TYPE))
