import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

logger = logging.getLogger(__name__)

from config import bot_settings

BOT_TOKEN = bot_settings.BOT_TOKEN
WEBAPP_URL = bot_settings.WEBAPP_URL

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🪙 Открыть Копилку",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Копилка — это инструмент для формирования привычки накопления.\n"
        "Создай цель на 100 шагов и откладывай понемногу каждый день.\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=keyboard,
    )


dp.include_router(router)


async def send_reminder_message(telegram_id: int, text: str):
    try:
        await bot.send_message(chat_id=telegram_id, text=text)
    except Exception as e:
        logger.error(f"Failed to send message to {telegram_id}: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())