import enum
from datetime import date, datetime
from sqlalchemy import String, Integer, BigInteger, Enum as SAEnum, DateTime, ForeignKey, func, JSON, Date, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class GoalStatus(str, enum.Enum):
    active = "active"
    frozen = "frozen"
    completed = "completed"
    abandoned = "abandoned"
    archived = "archived"


class ChallengeType(str, enum.Enum):
    envelope = "envelope"


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        Index("ix_goals_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    target_amount: Mapped[int] = mapped_column(BigInteger)
    saved_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[GoalStatus] = mapped_column(SAEnum(GoalStatus), default=GoalStatus.active, index=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    challenge: Mapped["Challenge"] = relationship(back_populates="goal", uselist=False)


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), unique=True)
    type: Mapped[ChallengeType] = mapped_column(SAEnum(ChallengeType), default=ChallengeType.envelope)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal: Mapped["Goal"] = relationship(back_populates="challenge")
    steps: Mapped[list["ChallengeStep"]] = relationship(back_populates="challenge", order_by="ChallengeStep.step_number")


class StepStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"


class ChallengeStep(Base):
    __tablename__ = "challenge_steps"
    __table_args__ = (
        Index("ix_challenge_steps_goal_id_status", "goal_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    step_number: Mapped[int] = mapped_column(Integer)
    planned_amount: Mapped[int] = mapped_column(BigInteger)
    was_skipped: Mapped[bool] = mapped_column(default=False)
    status: Mapped[StepStatus] = mapped_column(SAEnum(StepStatus), default=StepStatus.pending)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    challenge: Mapped["Challenge"] = relationship(back_populates="steps")
    goal: Mapped["Goal"] = relationship()


class DepositType(str, enum.Enum):
    full = "full"


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("challenge_steps.id"))
    amount: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[DepositType] = mapped_column(SAEnum(DepositType))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    # TODO: drop columns reminders_enabled, reminder_time, last_reminder_sent_at via migration (006_user_reminders)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserStreak(Base):
    __tablename__ = "user_streaks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_code", "goal_id", name="uq_user_achievement_per_goal"),
        Index("uq_user_achievement_null_goal", "user_id", "achievement_code", unique=True, postgresql_where=text("goal_id IS NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    achievement_code: Mapped[str] = mapped_column(String(50))
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id"), nullable=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
