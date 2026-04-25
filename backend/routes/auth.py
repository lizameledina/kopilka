import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from schemas import TelegramAuthRequest, AuthResponse, UserInfo
from services.auth import validate_init_data, parse_user_data, create_jwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(request: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    parsed = validate_init_data(request.init_data)
    if not parsed:
        raise HTTPException(status_code=401, detail="Некорректные данные Telegram")

    user_data_str = parsed.get("user")
    if not user_data_str:
        raise HTTPException(status_code=401, detail="Нет данных пользователя")

    user_data = parse_user_data(user_data_str)
    telegram_id = user_data.get("id")
    first_name = user_data.get("first_name", "")
    username = user_data.get("username")
    tz = request.timezone or "UTC"

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            timezone=tz,
        )
        db.add(user)
        await db.flush()
    else:
        if first_name:
            user.first_name = first_name
        if username:
            user.username = username
        user.timezone = tz
        await db.flush()

    await db.commit()
    token = create_jwt(user.id)

    return AuthResponse(
        token=token,
        user=UserInfo(
            id=user.id,
            telegram_id=user.telegram_id,
            first_name=user.first_name,
            username=user.username,
            timezone=user.timezone,
        ),
    )
