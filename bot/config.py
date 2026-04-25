from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = "https://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


bot_settings = BotSettings()