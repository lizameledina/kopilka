from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import StreakResponse
from services.streak import get_streak
from routes.deps import get_current_user

router = APIRouter(prefix="/streak", tags=["streak"])


@router.get("", response_model=StreakResponse)
async def get_streak_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    streak = await get_streak(db, current_user.id)
    return StreakResponse(**streak)