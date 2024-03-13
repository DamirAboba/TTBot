import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from handlers.youtube_handler import router

load_dotenv()
bot = Bot(str(os.getenv("BOT_TOKEN")))
dp = Dispatcher()


async def on_startup():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(on_startup())
    except KeyboardInterrupt:
        print("Exit")
