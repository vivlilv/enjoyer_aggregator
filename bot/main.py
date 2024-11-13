import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
BOT_TOKEN = os.getenv('BOT_TOKEN')
from handlers import register_handlers

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_handlers(dp)

    await dp.start_polling(bot)
    print('System ready')

if __name__ == '__main__':
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    asyncio.run(main())