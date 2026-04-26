import logging
import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
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

MESSAGES = {
    "start": (
        "Привет! Я помогу тебе копить деньги через цели и конверты.\n\n"
        "Создай цель, открывай конверты и отмечай прогресс в приложении."
    ),
    "app": "Открываю твою копилку.",
    "help": (
        "Это копилка в Telegram.\n\n"
        "В приложении можно:\n"
        "— создать цель\n"
        "— открыть конверт\n"
        "— отметить накопление\n"
        "— следить за прогрессом\n"
        "— замораживать цели\n"
        "— смотреть достижения\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение."
    ),
    "how": (
        "Это копилка с конвертами.\n\n"
        "Ты создаёшь цель и выбираешь количество шагов. Приложение распределяет сумму по конвертам.\n\n"
        "Каждый раз ты открываешь конверт и видишь сумму, которую нужно отложить.\n\n"
        "Важно: деньги ты откладываешь сам — на свою карту, счёт или наличными. Приложение не хранит деньги, оно только помогает следить за прогрессом.\n\n"
        "Ты отмечаешь, что отложил сумму, и переходишь к следующему шагу.\n\n"
        "Так маленькими действиями ты доходишь до цели."
    ),
    "reminder_envelope": "Твой конверт ждёт тебя.",
    "reminder_no_goal": (
        "У тебя пока нет активной цели.\n\n"
        "Открой приложение, чтобы создать новую цель или разморозить одну из замороженных."
    ),
    "reminder_all_frozen": (
        "Все цели сейчас заморожены.\n\n"
        "Открой приложение, чтобы разморозить цель или создать новую."
    ),
    "reminder_goal_done": (
        "Цель достигнута. Отличная работа!\n\n"
        "Открой приложение, чтобы посмотреть итог или создать новую цель."
    ),
}


def open_app_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(MESSAGES["start"], reply_markup=open_app_keyboard())


@router.message(Command("app"))
async def cmd_app(message: Message):
    await message.answer(MESSAGES["app"], reply_markup=open_app_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(MESSAGES["help"], reply_markup=open_app_keyboard())


@router.message(Command("how"))
async def cmd_how(message: Message):
    await message.answer(MESSAGES["how"], reply_markup=open_app_keyboard())


dp.include_router(router)


async def send_reminder_message(telegram_id: int, text: str):
    try:
        await bot.send_message(chat_id=telegram_id, text=text, reply_markup=open_app_keyboard())
    except Exception as e:
        logger.error(f"Failed to send message to {telegram_id}: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
