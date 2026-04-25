import pytest
import pytest_asyncio
from datetime import date, datetime, timezone

from models import UserStreak


@pytest.mark.asyncio
async def test_streak_first_day(db, user):
    from services.streak import update_streak, get_or_create_streak

    streak = await get_or_create_streak(db, user.id)
    await db.flush()

    streak = await update_streak(db, user.id, "UTC")
    assert streak.current_streak == 1
    assert streak.best_streak == 1

    streak2 = await update_streak(db, user.id, "UTC")
    assert streak2.current_streak == 1


@pytest.mark.asyncio
async def test_streak_consecutive_days(db, user):
    from services.streak import update_streak, get_or_create_streak

    streak = await update_streak(db, user.id, "UTC")
    assert streak.current_streak == 1

    streak.last_activity_date = date.today() - __import__("datetime").timedelta(days=1)
    await db.flush()

    streak = await update_streak(db, user.id, "UTC")
    assert streak.current_streak == 2
    assert streak.best_streak == 2


@pytest.mark.asyncio
async def test_streak_broken(db, user):
    from services.streak import update_streak

    streak = await update_streak(db, user.id, "UTC")
    assert streak.current_streak == 1

    streak.last_activity_date = date.today() - __import__("datetime").timedelta(days=3)
    await db.flush()

    streak = await update_streak(db, user.id, "UTC")
    assert streak.current_streak == 1


@pytest.mark.asyncio
async def test_best_streak_preserved(db, user):
    from services.streak import update_streak

    streak = await update_streak(db, user.id, "UTC")
    streak.last_activity_date = date.today() - __import__("datetime").timedelta(days=1)
    streak.current_streak = 10
    streak.best_streak = 10
    await db.flush()

    streak = await update_streak(db, user.id, "UTC")
    assert streak.current_streak == 11
    assert streak.best_streak == 11