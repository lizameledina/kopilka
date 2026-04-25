import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://kopilka:kopilka@db:5432/kopilka"
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = "https://localhost:3000"
    JWT_SECRET: str = "super-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 720

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()