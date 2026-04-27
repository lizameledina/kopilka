from typing import Literal
from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str
    timezone: str | None = None


class UserInfo(BaseModel):
    id: int
    telegram_id: int
    first_name: str | None
    username: str | None
    timezone: str = "UTC"


class AuthResponse(BaseModel):
    token: str
    user: UserInfo


class CreateGoalRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    target_amount: int = Field(ge=100)
    distribution: Literal["equal", "random", "ascending", "descending"] = "equal"
    step_count: int = Field(ge=1, le=365, default=100)


class GoalResponse(BaseModel):
    id: int
    title: str
    target_amount: int
    saved_amount: int
    status: str
    total_steps: int = 100
    completed_at: str | None = None


class StepResponse(BaseModel):
    id: int
    step_number: int
    planned_amount: int
    status: str
    total_steps: int = 100
    goal_title: str | None = None
    goal_saved: int | None = None
    goal_target: int | None = None


class TodayStepItem(BaseModel):
    goal_id: int
    goal_title: str
    step: StepResponse | None = None
    total_steps: int = 100


class AchievementItem(BaseModel):
    code: str
    title: str
    description: str
    icon: str
    unlocked: bool
    unlocked_at: str | None = None
    goal_id: int | None = None
    goal_title: str | None = None


class StepActionResponse(BaseModel):
    id: int
    status: str
    newly_unlocked: list[AchievementItem] = []
    goal_completed: bool = False
    goal_id: int | None = None


class ProgressResponse(BaseModel):
    goal_id: int
    title: str
    target_amount: int
    saved_amount: int
    percent: float
    completed_steps: int
    skipped_steps: int
    total_steps: int
    status: str
    steps: list[dict] = []


class StreakResponse(BaseModel):
    current_streak: int
    best_streak: int


class ActivityItem(BaseModel):
    id: int
    event_type: str
    created_at: str
    payload: dict | None = None


class CompletionSummary(BaseModel):
    goal_id: int
    title: str
    target_amount: int
    saved_amount: int
    percent: float
    completed_steps: int
    skipped_steps: int
    total_steps: int
    status: str
    completed_at: str | None = None
    created_at: str
    duration_days: int
    current_streak: int
    best_streak: int
    achievements: list[AchievementItem] = []


class ShareSummary(BaseModel):
    goal_id: int
    title: str
    target_amount: int
    saved_amount: int
    percent: float
    completed_steps: int
    total_steps: int
    status: str
    completed_at: str | None = None
    duration_days: int | None = None
    current_streak: int
    best_streak: int


class GoalAchievementsResponse(BaseModel):
    goal_achievements: list[AchievementItem] = []
    global_achievements: list[AchievementItem] = []


class EditGoalRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    target_amount: int | None = Field(None, ge=100)
    step_count: int | None = Field(None, ge=1, le=365)
    distribution: Literal["equal", "random", "ascending", "descending"] | None = None
    reset: bool = False


class EditPreviewResponse(BaseModel):
    was: dict
    will_be: dict
    warnings: list[str] = []
    error: str | None = None


