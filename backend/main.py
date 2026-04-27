import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings as app_settings
from database import init_db
from models import *  # noqa: ensure all models are imported for create_all
from routes import auth, users, goals, steps, streaks, achievements, activity
from routes import settings as settings_routes

import services.streak  # noqa: register event handlers
import services.achievements  # noqa: register event handlers
import services.activity  # noqa: register event handlers

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from services.reminders import check_and_send_reminders
    _scheduler.add_job(check_and_send_reminders, "interval", minutes=1, id="reminders")
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(title="Kopilka API", lifespan=lifespan)

allowed_origins = [
    app_settings.WEBAPP_URL,
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(goals.router)
app.include_router(steps.router)
app.include_router(streaks.router)
app.include_router(achievements.router)
app.include_router(activity.router)
app.include_router(settings_routes.router)


@app.get("/health")
async def health():
    return {"status": "ok"}