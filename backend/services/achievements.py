from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserAchievement, Goal, GoalStatus, UserStreak
from services.events import on, emit, EVENT_STEP_COMPLETED, EVENT_SKIPPED_STEP_COMPLETED, EVENT_GOAL_COMPLETED, EVENT_GOAL_CREATED, EVENT_ACHIEVEMENT_UNLOCKED
from services.step_counts import get_step_counts

ACHIEVEMENTS_USER = {
    "first_step": {"title": "Первый шаг", "description": "Завершить первый конверт", "icon": "🎯"},
    "streak_3": {"title": "Серия 3 дня", "description": "3 дня подряд", "icon": "🔥"},
    "streak_7": {"title": "Серия 7 дней", "description": "7 дней подряд", "icon": "⚡"},
    "streak_30": {"title": "Месяц силы", "description": "30 дней подряд", "icon": "💪"},
    "streak_100": {"title": "Железная воля", "description": "100 дней подряд", "icon": "🛡️"},
    "multi_goal": {"title": "Многогранник", "description": "3 активных цели одновременно", "icon": "💎"},
    "skip_recovery": {"title": "Второй шанс", "description": "Завершить пропущенный конверт", "icon": "🔄"},
}

ACHIEVEMENTS_GOAL = {
    "steps_5": {"title": "Пятёрка", "description": "Завершить 5 конвертов", "icon": "✋"},
    "steps_10": {"title": "Десятка", "description": "Завершить 10 конвертов", "icon": "🔟"},
    "goal_25": {"title": "Четверть пути", "description": "Накопить 25% от цели", "icon": "🌿"},
    "goal_50": {"title": "Половина пути", "description": "Накопить 50% от цели", "icon": "🏔️"},
    "goal_75": {"title": "Три четверти", "description": "Накопить 75% от цели", "icon": "🏅"},
    "goal_completed": {"title": "Цель достигнута!", "description": "Выполнить цель", "icon": "🏆"},
    "no_skip": {"title": "Без пропусков", "description": "Завершить цель без единого пропуска", "icon": "✨"},
}


async def _try_unlock(db: AsyncSession, user_id: int, code: str, goal_id: int | None = None) -> bool:
    """Insert achievement if not already unlocked. Returns True on first unlock."""
    stmt = pg_insert(UserAchievement).values(
        user_id=user_id,
        achievement_code=code,
        goal_id=goal_id,
    ).on_conflict_do_nothing()
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0


async def get_achievements_unlocked_since(
    db: AsyncSession, user_id: int, since: datetime
) -> list[dict]:
    """Return achievements unlocked at or after `since`, with full metadata."""
    result = await db.execute(
        select(UserAchievement, Goal.title)
        .join(Goal, UserAchievement.goal_id == Goal.id, isouter=True)
        .where(
            UserAchievement.user_id == user_id,
            UserAchievement.unlocked_at >= since,
        )
        .order_by(UserAchievement.unlocked_at)
    )
    achievements = []
    for ua, goal_title in result.all():
        info = ACHIEVEMENTS_USER.get(ua.achievement_code) or ACHIEVEMENTS_GOAL.get(ua.achievement_code)
        if not info:
            continue
        achievements.append({
            "code": ua.achievement_code,
            "title": info["title"],
            "description": info["description"],
            "icon": info["icon"],
            "unlocked": True,
            "unlocked_at": ua.unlocked_at.isoformat(),
            "goal_id": ua.goal_id,
            "goal_title": goal_title,
        })
    return achievements


async def get_all_achievements(db: AsyncSession, user_id: int) -> list[dict]:
    result = await db.execute(
        select(UserAchievement, Goal.title)
        .join(Goal, UserAchievement.goal_id == Goal.id, isouter=True)
        .where(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.unlocked_at)
    )
    rows = result.all()
    unlocked_map: dict[tuple[str, int | None], tuple] = {}
    for ua, goal_title in rows:
        unlocked_map[(ua.achievement_code, ua.goal_id)] = (ua, goal_title)

    achievements = []

    for code, info in ACHIEVEMENTS_USER.items():
        ua, _ = unlocked_map.get((code, None), (None, None))
        achievements.append({
            "code": code,
            "title": info["title"],
            "description": info["description"],
            "icon": info["icon"],
            "unlocked": ua is not None,
            "unlocked_at": ua.unlocked_at.isoformat() if ua else None,
            "goal_id": None,
            "goal_title": None,
        })

    result_goals = await db.execute(
        select(Goal.id, Goal.title, Goal.status).where(
            Goal.user_id == user_id,
            Goal.status != GoalStatus.archived,
        )
    )
    user_goals = result_goals.all()

    for goal_id, goal_title, goal_status in user_goals:
        for code, info in ACHIEVEMENTS_GOAL.items():
            ua, g_title = unlocked_map.get((code, goal_id), (None, None))
            achievements.append({
                "code": code,
                "title": info["title"],
                "description": info["description"],
                "icon": info["icon"],
                "unlocked": ua is not None,
                "unlocked_at": ua.unlocked_at.isoformat() if ua else None,
                "goal_id": goal_id,
                "goal_title": goal_title,
            })

    return achievements


async def get_achievements_for_goal(db: AsyncSession, user_id: int, goal_id: int) -> list[dict]:
    result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user_id, UserAchievement.goal_id == goal_id)
        .order_by(UserAchievement.unlocked_at)
    )
    unlocked = {ua.achievement_code: ua for ua in result.scalars().all()}

    goal_result = await db.execute(select(Goal.title).where(Goal.id == goal_id))
    goal_title = goal_result.scalar_one_or_none() or ""

    achievements = []
    for code, info in ACHIEVEMENTS_GOAL.items():
        ua = unlocked.get(code)
        achievements.append({
            "code": code,
            "title": info["title"],
            "description": info["description"],
            "icon": info["icon"],
            "unlocked": ua is not None,
            "unlocked_at": ua.unlocked_at.isoformat() if ua else None,
            "goal_id": goal_id,
            "goal_title": goal_title,
        })
    return achievements


async def _check_user_achievements(db: AsyncSession, user_id: int) -> list[tuple[int, str, int | None]]:
    """Check and unlock user-level achievements. Returns list of (user_id, code, goal_id) for new unlocks."""
    unlocked: list[tuple[int, str, int | None]] = []

    streak_result = await db.execute(select(UserStreak).where(UserStreak.user_id == user_id))
    streak = streak_result.scalar_one_or_none()

    if await _try_unlock(db, user_id, "first_step"):
        unlocked.append((user_id, "first_step", None))

    if streak and streak.current_streak >= 3:
        if await _try_unlock(db, user_id, "streak_3"):
            unlocked.append((user_id, "streak_3", None))
        if streak.current_streak >= 7:
            if await _try_unlock(db, user_id, "streak_7"):
                unlocked.append((user_id, "streak_7", None))
            if streak.current_streak >= 30:
                if await _try_unlock(db, user_id, "streak_30"):
                    unlocked.append((user_id, "streak_30", None))
                if streak.current_streak >= 100:
                    if await _try_unlock(db, user_id, "streak_100"):
                        unlocked.append((user_id, "streak_100", None))

    active_count = await db.execute(
        select(func.count())
        .select_from(Goal)
        .where(Goal.user_id == user_id, Goal.status == GoalStatus.active)
    )
    if active_count.scalar() >= 3:
        if await _try_unlock(db, user_id, "multi_goal"):
            unlocked.append((user_id, "multi_goal", None))

    return unlocked


async def _check_goal_achievements(db: AsyncSession, user_id: int, goal_id: int) -> list[tuple[int, str, int | None]]:
    """Check and unlock goal-level achievements. Returns list of (user_id, code, goal_id) for new unlocks."""
    unlocked: list[tuple[int, str, int | None]] = []
    counts = await get_step_counts(db, goal_id)

    if counts["completed"] >= 5:
        if await _try_unlock(db, user_id, "steps_5", goal_id):
            unlocked.append((user_id, "steps_5", goal_id))
    if counts["completed"] >= 10:
        if await _try_unlock(db, user_id, "steps_10", goal_id):
            unlocked.append((user_id, "steps_10", goal_id))

    goal_result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = goal_result.scalar_one_or_none()
    if goal and goal.target_amount > 0:
        percent = goal.saved_amount / goal.target_amount
        if percent >= 0.25:
            if await _try_unlock(db, user_id, "goal_25", goal_id):
                unlocked.append((user_id, "goal_25", goal_id))
        if percent >= 0.5:
            if await _try_unlock(db, user_id, "goal_50", goal_id):
                unlocked.append((user_id, "goal_50", goal_id))
        if percent >= 0.75:
            if await _try_unlock(db, user_id, "goal_75", goal_id):
                unlocked.append((user_id, "goal_75", goal_id))

    if goal and goal.status == GoalStatus.completed:
        if await _try_unlock(db, user_id, "goal_completed", goal_id):
            unlocked.append((user_id, "goal_completed", goal_id))
        if counts["skipped"] == 0:
            if await _try_unlock(db, user_id, "no_skip", goal_id):
                unlocked.append((user_id, "no_skip", goal_id))

    return unlocked


async def _emit_unlocked(newly_unlocked: list[tuple[int, str, int | None]]) -> None:
    """Emit EVENT_ACHIEVEMENT_UNLOCKED for each newly unlocked achievement after DB commit."""
    for uid, code, gid in newly_unlocked:
        await emit(EVENT_ACHIEVEMENT_UNLOCKED, user_id=uid, achievement_code=code, goal_id=gid)


@on(EVENT_STEP_COMPLETED)
async def on_step_completed(user_id: int, goal_id: int, **kwargs):
    from database import async_session
    async with async_session() as db:
        try:
            newly_unlocked = []
            newly_unlocked.extend(await _check_user_achievements(db, user_id))
            newly_unlocked.extend(await _check_goal_achievements(db, user_id, goal_id))
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    await _emit_unlocked(newly_unlocked)


@on(EVENT_SKIPPED_STEP_COMPLETED)
async def on_skipped_step_completed(user_id: int, goal_id: int, **kwargs):
    from database import async_session
    async with async_session() as db:
        try:
            newly_unlocked = []
            if await _try_unlock(db, user_id, "skip_recovery"):
                newly_unlocked.append((user_id, "skip_recovery", None))
            newly_unlocked.extend(await _check_user_achievements(db, user_id))
            newly_unlocked.extend(await _check_goal_achievements(db, user_id, goal_id))
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    await _emit_unlocked(newly_unlocked)


@on(EVENT_GOAL_CREATED)
async def on_goal_created(user_id: int, goal_id: int, **kwargs):
    from database import async_session
    async with async_session() as db:
        try:
            newly_unlocked = await _check_user_achievements(db, user_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    await _emit_unlocked(newly_unlocked)


@on(EVENT_GOAL_COMPLETED)
async def on_goal_completed(user_id: int, goal_id: int, **kwargs):
    from database import async_session
    async with async_session() as db:
        try:
            newly_unlocked = await _check_goal_achievements(db, user_id, goal_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    await _emit_unlocked(newly_unlocked)
