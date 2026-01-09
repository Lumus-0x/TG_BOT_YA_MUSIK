import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from bot.handlers import router

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    # Получение токенов из переменных окружения
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    YANDEX_MUSIC_TOKEN = os.getenv("YANDEX_MUSIC_TOKEN")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    if not YANDEX_MUSIC_TOKEN:
        logger.warning("YANDEX_MUSIC_TOKEN not found. Some features may be limited.")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(router)
    
    # Запуск бота
    logger.info("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())