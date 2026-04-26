import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Goal, GoalStatus, User
from schemas import (
    CreateGoalRequest,
    GoalResponse,
    ProgressResponse,
    AchievementItem,
    CompletionSummary,
    ShareSummary,
    HistoryItem,
    GoalAchievementsResponse,
    EditGoalRequest,
    EditPreviewResponse,
    GoalActivityItem,
)
from services.goals import (
    create_goal,
    get_current_goal,
    get_user_goals,
    get_goal,
    archive_goal,
    freeze_goal,
    unfreeze_goal,
    goal_to_response,
)
from services.goal_edit import edit_goal, preview_goal_edit, reset_goal
from services.achievements import get_achievements_for_goal, get_all_achievements
from services.progress import get_progress, get_steps_list
from services.completion import get_completion_summary, get_share_summary
from services.history import get_goal_history
from services.activity import get_goal_activity
from services.events import emit_pending, PendingEvent, EVENT_GOAL_ARCHIVED
from routes.deps import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])
logger = logging.getLogger(__name__)


@router.post("", response_model=GoalResponse)
async def create_goal_endpoint(
    request: CreateGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        goal, events = await create_goal(
            db,
            user_id=current_user.id,
            title=request.title,
            target_amount=request.target_amount,
            distribution=request.distribution,
            step_count=request.step_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    await emit_pending(events)
    return goal_to_response(goal)


@router.get("", response_model=list[GoalResponse])
async def list_goals_endpoint(
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal_status = None
    if status:
        try:
            goal_status = GoalStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Некорректный статус: {status}")

    goals = await get_user_goals(db, current_user.id, status=goal_status)
    return [goal_to_response(g) for g in goals]


@router.get("/current", response_model=GoalResponse | None)
async def get_current_goal_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_current_goal(db, current_user.id)
    if not goal:
        return None
    return goal_to_response(goal)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal_to_response(goal)


@router.patch("/{goal_id}", response_model=GoalResponse)
async def edit_goal_endpoint(
    goal_id: int,
    request: EditGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        goal, events = await edit_goal(
            db,
            goal_id=goal_id,
            user_id=current_user.id,
            title=request.title,
            target_amount=request.target_amount,
            step_count=request.step_count,
            distribution=request.distribution,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    await emit_pending(events)
    return goal_to_response(goal)


@router.post("/{goal_id}/edit-preview", response_model=EditPreviewResponse)
async def edit_preview_endpoint(
    goal_id: int,
    request: EditGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await preview_goal_edit(
        db,
        goal_id=goal_id,
        user_id=current_user.id,
        title=request.title,
        target_amount=request.target_amount,
        step_count=request.step_count,
        distribution=request.distribution,
    )
    return EditPreviewResponse(**result)


@router.post("/{goal_id}/reset", response_model=GoalResponse)
async def reset_goal_endpoint(
    goal_id: int,
    request: EditGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        goal, events = await reset_goal(
            db,
            goal_id=goal_id,
            user_id=current_user.id,
            distribution=request.distribution,
            step_count=request.step_count,
            target_amount=request.target_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    await emit_pending(events)
    return goal_to_response(goal)


@router.get("/{goal_id}/activity", response_model=list[GoalActivityItem])
async def get_goal_activity_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    items = await get_goal_activity(db, goal_id, current_user.id)
    return [GoalActivityItem(**item) for item in items]


@router.post("/{goal_id}/abandon", response_model=GoalResponse)
async def abandon_goal_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Legacy endpoint: delegates to freeze
    existing = await get_goal(db, goal_id, current_user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    goal, events = await freeze_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=400, detail="Цель нельзя заморозить")

    await db.commit()
    await emit_pending(events)
    return goal_to_response(goal)


@router.post("/{goal_id}/freeze", response_model=GoalResponse)
async def freeze_goal_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await get_goal(db, goal_id, current_user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    goal, events = await freeze_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=400, detail="Цель нельзя заморозить")

    await db.commit()
    await emit_pending(events)
    return goal_to_response(goal)


@router.post("/{goal_id}/unfreeze", response_model=GoalResponse)
async def unfreeze_goal_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await get_goal(db, goal_id, current_user.id)
    if not existing:
        logger.info("unfreeze: not found (goal_id=%s, user_id=%s)", goal_id, current_user.id)
        raise HTTPException(status_code=404, detail="Цель не найдена")

    try:
        goal, events = await unfreeze_goal(db, goal_id, current_user.id)
    except ValueError as e:
        logger.info(
            "unfreeze: blocked (goal_id=%s, user_id=%s, status=%s, err=%s)",
            goal_id,
            current_user.id,
            getattr(existing.status, "value", existing.status),
            str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))

    if not goal:
        logger.info(
            "unfreeze: invalid state (goal_id=%s, user_id=%s, status=%s)",
            goal_id,
            current_user.id,
            getattr(existing.status, "value", existing.status),
        )
        raise HTTPException(status_code=400, detail="Цель не заморожена")

    await db.commit()
    await emit_pending(events)
    return goal_to_response(goal)


@router.delete("/{goal_id}", response_model=GoalResponse)
async def delete_goal_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await archive_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    await db.commit()
    await emit_pending([PendingEvent(EVENT_GOAL_ARCHIVED, goal_id=goal_id, user_id=current_user.id)])
    return goal_to_response(goal)


@router.get("/{goal_id}/progress", response_model=ProgressResponse)
async def get_progress_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    progress = await get_progress(db, goal.id)
    steps = await get_steps_list(db, goal.id)

    return ProgressResponse(
        goal_id=progress["goal_id"],
        title=progress["title"],
        target_amount=progress["target_amount"],
        saved_amount=progress["saved_amount"],
        percent=progress["percent"],
        completed_steps=progress["completed_steps"],
        skipped_steps=progress["skipped_steps"],
        total_steps=progress["total_steps"],
        status=progress["status"],
        steps=steps,
    )


@router.get("/{goal_id}/achievements", response_model=GoalAchievementsResponse)
async def get_goal_achievements_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    goal_achievements = await get_achievements_for_goal(db, current_user.id, goal_id)
    global_achievements = await get_all_achievements(db, current_user.id)
    global_only = [a for a in global_achievements if a["goal_id"] is None]

    return GoalAchievementsResponse(
        goal_achievements=[AchievementItem(**a) for a in goal_achievements],
        global_achievements=[AchievementItem(**a) for a in global_only],
    )


@router.get("/{goal_id}/completion", response_model=CompletionSummary)
async def get_completion_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    summary = await get_completion_summary(db, goal_id, current_user.id)
    if not summary:
        raise HTTPException(status_code=400, detail="Цель ещё не завершена")

    return CompletionSummary(**summary)


@router.get("/{goal_id}/share-summary", response_model=ShareSummary)
async def get_share_summary_endpoint(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    summary = await get_share_summary(db, goal_id, current_user.id)
    return ShareSummary(**summary)


@router.get("/{goal_id}/history", response_model=list[HistoryItem])
async def get_history_endpoint(
    goal_id: int,
    sort_by: str = Query("date", pattern="^(date|number)$"),
    status: str | None = Query(None, pattern="^(completed|skipped|recovered)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = await get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    items = await get_goal_history(
        db,
        goal_id,
        user_id=current_user.id,
        sort_by=sort_by,
        status_filter=status,
    )
    if items is None:
        raise HTTPException(status_code=404, detail="Цель не найдена")

    return [HistoryItem(**item) for item in items]
