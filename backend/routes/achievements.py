from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import AchievementItem
from services.achievements import get_all_achievements
from routes.deps import get_current_user

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("", response_model=list[AchievementItem])
async def get_achievements_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    achievements = await get_all_achievements(db, current_user.id)
    return [AchievementItem(**a) for a in achievements]