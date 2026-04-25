from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import UserInfo
from routes.deps import get_current_user

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo(
        id=current_user.id,
        telegram_id=current_user.telegram_id,
        first_name=current_user.first_name,
        username=current_user.username,
        timezone=current_user.timezone,
    )