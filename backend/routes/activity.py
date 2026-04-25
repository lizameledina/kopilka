from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import ActivityItem
from services.activity import get_activity
from routes.deps import get_current_user

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityItem])
async def get_activity_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_activity(db, current_user.id, limit)
    return [ActivityItem(**a) for a in items]