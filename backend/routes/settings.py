from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.deps import get_current_user
from schemas import ReminderSettings, UpdateReminderSettings
from services.reminders import get_reminder_settings, update_reminder_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/reminders", response_model=ReminderSettings)
async def get_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_reminder_settings(db, current_user.id)
    return ReminderSettings(**data)


@router.patch("/reminders", response_model=ReminderSettings)
async def update_reminders(
    body: UpdateReminderSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await update_reminder_settings(
        db, current_user.id, body.reminders_enabled, body.reminder_time
    )
    await db.commit()
    return ReminderSettings(**data)
