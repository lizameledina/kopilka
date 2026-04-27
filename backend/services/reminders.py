import logging
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, ActivityLog

logger = logging.getLogger(__name__)

REMINDER_TEXTS = [
    "Твой следующий шаг ждёт тебя.",
    "Сегодня можно сделать маленький шаг к цели.",
    "Не забудь заглянуть в копилку.",
    "Один шаг сегодня — и цель ближе.",
    "Вернёмся к накоплениям?",
    "Открой приложение и продолжи копить.",
]

_STEP_EVENT_TYPES = {"step_completed", "step_skipped", "skipped_step_completed"}


async def get_reminder_settings(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"reminders_enabled": False, "reminder_time": "09:00"}
    return {
        "reminders_enabled": user.reminders_enabled,
        "reminder_time": user.reminder_time,
    }


async def update_reminder_settings(
    db: AsyncSession, user_id: int, reminders_enabled: bool, reminder_time: str
) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.reminders_enabled = reminders_enabled
    user.reminder_time = reminder_time
    await db.flush()
    return {
        "reminders_enabled": user.reminders_enabled,
        "reminder_time": user.reminder_time,
    }


async def _user_acted_today(db: AsyncSession, user_id: int, tz: ZoneInfo) -> bool:
    now_local = datetime.now(tz)
    today = now_local.date()
    day_start = datetime(today.year, today.month, today.day, tzinfo=tz)
    result = await db.execute(
        select(ActivityLog.id)
        .where(
            ActivityLog.user_id == user_id,
            ActivityLog.event_type.in_(_STEP_EVENT_TYPES),
            ActivityLog.created_at >= day_start,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _send_telegram_message(telegram_id: int, text: str, bot_token: str, webapp_url: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "Открыть приложение", "web_app": {"url": webapp_url}}
            ]]
        },
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            logger.warning("Telegram API error %s: %s", resp.status_code, resp.text[:200])


async def check_and_send_reminders():
    from database import async_session
    from config import settings

    if not settings.BOT_TOKEN:
        return

    now_utc = datetime.now(timezone.utc)

    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.reminders_enabled == True)  # noqa: E712
        )
        users = result.scalars().all()

        for user in users:
            try:
                tz = ZoneInfo(user.timezone or "UTC")
            except Exception:
                tz = ZoneInfo("UTC")

            now_local = now_utc.astimezone(tz)
            if now_local.strftime("%H:%M") != user.reminder_time:
                continue

            today_local = now_local.date()
            if user.last_reminder_sent_at:
                last_local_date = user.last_reminder_sent_at.astimezone(tz).date()
                if last_local_date == today_local:
                    continue

            if await _user_acted_today(db, user.id, tz):
                continue

            text = random.choice(REMINDER_TEXTS)

            try:
                await _send_telegram_message(user.telegram_id, text, settings.BOT_TOKEN, settings.WEBAPP_URL)
                user.last_reminder_sent_at = now_utc
                logger.info("Reminder sent to user %s", user.id)
            except Exception as e:
                logger.error("Failed to send reminder to user %s: %s", user.id, e)

        await db.commit()
