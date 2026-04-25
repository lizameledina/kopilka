import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database import Base
from models import (
    User, Goal, GoalStatus, Challenge, ChallengeType,
    ChallengeStep, StepStatus, UserStreak, UserAchievement,
)
from services.distribution_strategies import get_strategy as get_dist_strategy

USE_PG = os.environ.get("TEST_DB", "sqlite") == "postgres"
PG_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://kopilka:kopilka@localhost:5434/kopilka_test")
SQLITE_URL = "sqlite+aiosqlite://"

TEST_DATABASE_URL = PG_URL if USE_PG else SQLITE_URL


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    if not USE_PG:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user(db: AsyncSession) -> User:
    u = User(telegram_id=12345, first_name="Test", timezone="UTC")
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def second_user(db: AsyncSession) -> User:
    u = User(telegram_id=67890, first_name="Test2", timezone="UTC")
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def goal_with_steps(db: AsyncSession, user: User) -> tuple[Goal, Challenge, list[ChallengeStep]]:
    goal = Goal(
        user_id=user.id,
        title="Test Goal",
        target_amount=10000,
        saved_amount=0,
        status=GoalStatus.active,
    )
    db.add(goal)
    await db.flush()

    challenge = Challenge(
        goal_id=goal.id,
        type=ChallengeType.envelope,
        config={"distribution": "equal"},
        total_steps=5,
    )
    db.add(challenge)
    await db.flush()

    amounts = get_dist_strategy("equal").distribute(10000, 5)
    steps = []
    for i, amount in enumerate(amounts, 1):
        step = ChallengeStep(
            challenge_id=challenge.id,
            goal_id=goal.id,
            step_number=i,
            planned_amount=amount,
            status=StepStatus.pending,
        )
        steps.append(step)
    db.add_all(steps)
    await db.flush()

    return goal, challenge, steps