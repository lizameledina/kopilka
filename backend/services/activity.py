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
    EVENT_GOAL_TITLE_CHANGED,
    EVENT_GOAL_AMOUNT_CHANGED,
    EVENT_GOAL_STEPS_CHANGED,
    EVENT_ENVELOPES_REDISTRIBUTED,
    EVENT_GOAL_RESET,
    EVENT_GOAL_ARCHIVED,
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
    EVENT_GOAL_TITLE_CHANGED: "goal_title_changed",
    EVENT_GOAL_AMOUNT_CHANGED: "goal_amount_changed",
    EVENT_GOAL_STEPS_CHANGED: "goal_steps_changed",
    EVENT_ENVELOPES_REDISTRIBUTED: "envelopes_redistributed",
    EVENT_GOAL_RESET: "goal_reset",
    EVENT_GOAL_ARCHIVED: "goal_archived",
}

TIMELINE_TITLES: dict[str, str] = {
    "goal_created": "Цель создана",
    "goal_title_changed": "Название изменено",
    "goal_amount_changed": "Сумма изменена",
    "goal_steps_changed": "Количество конвертов изменено",
    "envelopes_redistributed": "Конверты перераспределены",
    "goal_reset": "Цель начата заново",
    "goal_frozen": "Цель заморожена",
    "goal_unfrozen": "Цель разморожена",
    "goal_completed": "Цель достигнута",
    "step_completed": "Конверт закрыт",
    "skipped_step_completed": "Пропущенный конверт закрыт",
    "step_skipped": "Конверт пропущен",
    "goal_archived": "Цель удалена",
    "achievement_unlocked": "Достижение разблокировано",
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


async def get_goal_activity(db: AsyncSession, goal_id: int, user_id: int, limit: int = 50) -> list[dict]:
    result = await db.execute(
        select(ActivityLog)
        .where(
            ActivityLog.user_id == user_id,
            ActivityLog.payload["goal_id"].as_integer() == goal_id,
        )
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()
    items = []
    for e in entries:
        title = TIMELINE_TITLES.get(e.event_type, e.event_type)
        description = _build_description(e.event_type, e.payload or {})
        items.append({
            "event_type": e.event_type,
            "title": title,
            "description": description,
            "created_at": e.created_at.isoformat(),
        })
    return items


def _build_description(event_type: str, payload: dict) -> str:
    if event_type == "goal_title_changed":
        old = payload.get("old_title", "")
        new = payload.get("new_title", "")
        return f'"{old}" → "{new}"' if old and new else ""
    if event_type == "goal_amount_changed":
        old = payload.get("old_amount")
        new = payload.get("new_amount")
        if old is not None and new is not None:
            return f"{old:,} → {new:,} ₽"
    if event_type == "goal_steps_changed":
        old = payload.get("old_count")
        new = payload.get("new_count")
        if old is not None and new is not None:
            return f"{old} → {new} конвертов"
    if event_type == "step_completed":
        amount = payload.get("amount")
        step_num = payload.get("step_number")
        if amount is not None:
            return f"Конверт #{step_num}: {amount:,} ₽" if step_num else f"{amount:,} ₽"
    if event_type == "step_skipped":
        step_num = payload.get("step_number")
        return f"Конверт #{step_num}" if step_num else ""
    if event_type == "goal_reset":
        old_amount = payload.get("old_saved_amount")
        if old_amount:
            return f"Прогресс сброшен (было {old_amount:,} ₽)"
    return ""


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
