from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Goal, Challenge, ChallengeStep
from routes.deps import get_current_user
from schemas import StepResponse, StepActionResponse, TodayStepItem
from services.events import emit_pending
from services.goal_rules import can_mutate_steps, is_paused
from services.goals import get_goal
from services.steps import get_today_steps_for_user, get_step_by_id, complete_step, skip_step

router = APIRouter(prefix="/steps", tags=["steps"])


async def _verify_step_ownership(
    db: AsyncSession, step_id: int, user_id: int
) -> tuple[ChallengeStep | None, Goal | None]:
    step = await get_step_by_id(db, step_id)
    if not step:
        return None, None
    goal = await get_goal(db, step.goal_id, user_id)
    if not goal:
        return None, None
    return step, goal


@router.get("/today", response_model=list[TodayStepItem])
async def get_today_steps_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_today_steps_for_user(db, current_user.id)
    result = []
    for item in items:
        step_resp = None
        if item["step"]:
            s = item["step"]
            total_steps = item["total_steps"]
            step_resp = StepResponse(
                id=s.id,
                step_number=s.step_number,
                planned_amount=s.planned_amount,
                status=s.status.value,
                total_steps=total_steps,
                goal_title=item["goal_title"],
                goal_saved=None,
                goal_target=None,
            )
        result.append(
            TodayStepItem(
                goal_id=item["goal_id"],
                goal_title=item["goal_title"],
                step=step_resp,
                total_steps=item["total_steps"],
            )
        )
    return result


@router.get("/{step_id}", response_model=StepResponse)
async def get_step_endpoint(
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    step, goal = await _verify_step_ownership(db, step_id, current_user.id)
    if not step or not goal:
        raise HTTPException(status_code=404, detail="Шаг не найден")

    challenge_result = await db.execute(select(Challenge).where(Challenge.goal_id == goal.id))
    challenge = challenge_result.scalar_one_or_none()
    total_steps = challenge.total_steps if challenge else 100

    return StepResponse(
        id=step.id,
        step_number=step.step_number,
        planned_amount=step.planned_amount,
        status=step.status.value,
        total_steps=total_steps,
        goal_title=goal.title,
        goal_saved=goal.saved_amount,
        goal_target=goal.target_amount,
    )


def _goal_mutation_error_detail(goal: Goal) -> str:
    if is_paused(goal.status):
        return "Цель заморожена"
    return "Цель не активна"


@router.post("/{step_id}/complete", response_model=StepActionResponse)
async def complete_step_endpoint(
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    step, goal = await _verify_step_ownership(db, step_id, current_user.id)
    if not step or not goal:
        raise HTTPException(status_code=404, detail="Шаг не найден")
    if not can_mutate_steps(goal.status):
        raise HTTPException(status_code=400, detail=_goal_mutation_error_detail(goal))

    completed, events = await complete_step(db, step_id, goal.id, current_user.id)
    if not completed:
        raise HTTPException(status_code=404, detail="Шаг не найден")

    await db.commit()
    await emit_pending(events)

    return StepActionResponse(id=completed.id, status=completed.status.value)


@router.post("/{step_id}/skip", response_model=StepActionResponse)
async def skip_step_endpoint(
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    step, goal = await _verify_step_ownership(db, step_id, current_user.id)
    if not step or not goal:
        raise HTTPException(status_code=404, detail="Шаг не найден")
    if not can_mutate_steps(goal.status):
        raise HTTPException(status_code=400, detail=_goal_mutation_error_detail(goal))

    skipped, events = await skip_step(db, step_id, goal.id, current_user.id)
    if not skipped:
        raise HTTPException(status_code=404, detail="Шаг не найден")

    await db.commit()
    await emit_pending(events)

    return StepActionResponse(id=skipped.id, status=skipped.status.value)

