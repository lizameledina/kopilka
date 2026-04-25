from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserStreak, User
from services.events import on, EVENT_STEP_COMPLETED, EVENT_SKIPPED_STEP_COMPLETED


async def _get_user_timezone(db: AsyncSession, user_id: int) -> str:
    result = await db.execute(select(User.timezone).where(User.id == user_id))
    tz = result.scalar_one_or_none()
    return tz or "UTC"


def _today_in_tz(tz_name: str) -> date:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


async def get_or_create_streak(db: AsyncSession, user_id: int) -> UserStreak:
    result = await db.execute(
        select(UserStreak)
        .where(UserStreak.user_id == user_id)
        .with_for_update()
    )
    streak = result.scalar_one_or_none()
    if streak:
        return streak

    stmt = pg_insert(UserStreak).values(
        user_id=user_id,
        current_streak=0,
        best_streak=0,
        last_activity_date=None,
    ).on_conflict_do_nothing(index_elements=["user_id"])
    await db.execute(stmt)
    await db.flush()

    result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == user_id)
    )
    return result.scalar_one()


async def update_streak(db: AsyncSession, user_id: int, tz_name: str = "UTC") -> UserStreak:
    streak = await get_or_create_streak(db, user_id)
    today = _today_in_tz(tz_name)

    if streak.last_activity_date == today:
        return streak

    if streak.last_activity_date is None:
        streak.current_streak = 1
    elif streak.last_activity_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    streak.last_activity_date = today

    if streak.current_streak > streak.best_streak:
        streak.best_streak = streak.current_streak

    await db.flush()
    return streak


async def get_streak(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == user_id)
    )
    streak = result.scalar_one_or_none()
    if not streak:
        return {"current_streak": 0, "best_streak": 0}
    return {
        "current_streak": streak.current_streak,
        "best_streak": streak.best_streak,
    }


@on(EVENT_STEP_COMPLETED)
async def on_step_completed(user_id: int, **kwargs):
    from database import async_session
    async with async_session() as db:
        try:
            tz_name = await _get_user_timezone(db, user_id)
            await update_streak(db, user_id, tz_name)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


@on(EVENT_SKIPPED_STEP_COMPLETED)
async def on_skipped_step_completed(user_id: int, **kwargs):
    from database import async_session
    async with async_session() as db:
        try:
            tz_name = await _get_user_timezone(db, user_id)
            await update_streak(db, user_id, tz_name)
            await db.commit()
        except Exception:
            await db.rollback()
            raise