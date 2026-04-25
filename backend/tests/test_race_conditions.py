import os

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from database import Base
from models import (
    Challenge,
    ChallengeStep,
    ChallengeType,
    Goal,
    GoalStatus,
    StepStatus,
    User,
    UserAchievement,
    UserStreak,
)
from services.achievements import _try_unlock
from services.goals import MAX_ACTIVE_GOALS, create_goal
from services.streak import get_or_create_streak, update_streak

USE_PG = os.environ.get("TEST_DB", "sqlite") == "postgres"
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://kopilka:kopilka@localhost:5434/kopilka_test",
)


@pytest_asyncio.fixture(scope="session")
async def pg_engine():
    if not USE_PG:
        pytest.skip("Set TEST_DB=postgres to run Postgres race-condition tests")

    eng = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    try:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        await eng.dispose()
        pytest.skip(f"Postgres is not available for tests: {type(e).__name__}")

    yield eng

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def pg_db(pg_engine):
    session_factory = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def pg_user(pg_db: AsyncSession) -> User:
    u = User(telegram_id=99999, first_name="TestPg", timezone="UTC")
    pg_db.add(u)
    await pg_db.flush()
    return u


class TestCreateGoalPostgres:
    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_create_goal(self, pg_db: AsyncSession, pg_user: User):
        goal, _events = await create_goal(pg_db, pg_user.id, "PG Goal", 5000, "equal", 10)
        assert goal.id is not None
        assert goal.title == "PG Goal"
        assert goal.target_amount == 5000

        result = await pg_db.execute(
            select(ChallengeStep).where(ChallengeStep.goal_id == goal.id)
        )
        steps = list(result.scalars().all())
        assert len(steps) == 10

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_max_active_goals(self, pg_db: AsyncSession, pg_user: User):
        for i in range(MAX_ACTIVE_GOALS):
            await create_goal(pg_db, pg_user.id, f"Goal {i}", 10000, "equal", 5)
        await pg_db.flush()

        with pytest.raises(ValueError, match="Максимум|ÐœÐ°"):
            await create_goal(pg_db, pg_user.id, "Overflow", 10000, "equal", 5)


class TestTryUnlockPostgres:
    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_unlock_first_time(self, pg_db: AsyncSession, pg_user: User):
        result = await _try_unlock(pg_db, pg_user.id, "first_step")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_unlock_duplicate_returns_false(self, pg_db: AsyncSession, pg_user: User, pg_engine):
        r1 = await _try_unlock(pg_db, pg_user.id, "skip_recovery")
        assert r1 is True
        await pg_db.commit()

        session_factory = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as fresh_session:
            r2 = await _try_unlock(fresh_session, pg_user.id, "skip_recovery")
            await fresh_session.commit()
            assert r2 is False

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_unlock_different_codes(self, pg_db: AsyncSession, pg_user: User):
        goal = Goal(user_id=pg_user.id, title="Test", target_amount=1000, saved_amount=0, status=GoalStatus.active)
        pg_db.add(goal)
        await pg_db.flush()

        r1 = await _try_unlock(pg_db, pg_user.id, "steps_5", goal_id=goal.id)
        r2 = await _try_unlock(pg_db, pg_user.id, "steps_10", goal_id=goal.id)
        assert r1 is True
        assert r2 is True

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_unlock_same_code_different_goal(self, pg_db: AsyncSession, pg_user: User):
        goal1 = Goal(user_id=pg_user.id, title="G1", target_amount=1000, saved_amount=0, status=GoalStatus.active)
        goal2 = Goal(user_id=pg_user.id, title="G2", target_amount=1000, saved_amount=0, status=GoalStatus.active)
        pg_db.add_all([goal1, goal2])
        await pg_db.flush()

        r1 = await _try_unlock(pg_db, pg_user.id, "steps_5", goal_id=goal1.id)
        r2 = await _try_unlock(pg_db, pg_user.id, "steps_5", goal_id=goal2.id)
        assert r1 is True
        assert r2 is True


class TestStreakPostgres:
    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_streak_first_day(self, pg_db: AsyncSession, pg_user: User):
        streak = await update_streak(pg_db, pg_user.id, "UTC")
        await pg_db.flush()
        assert streak.current_streak == 1
        assert streak.best_streak == 1

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_streak_same_day_no_double(self, pg_db: AsyncSession, pg_user: User):
        await update_streak(pg_db, pg_user.id, "UTC")
        await pg_db.flush()
        streak = await update_streak(pg_db, pg_user.id, "UTC")
        assert streak.current_streak == 1

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_get_or_create_streak(self, pg_db: AsyncSession, pg_user: User):
        streak = await get_or_create_streak(pg_db, pg_user.id)
        await pg_db.flush()
        assert streak.current_streak == 0
        assert streak.user_id == pg_user.id
