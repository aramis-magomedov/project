from db import init_models
from headlers import router


import asyncio
import logging
from tabulate import tabulate
from aiogram import Bot, Dispatcher



# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="7793831868:AAGMDKY-PnVtVDm4cIZQx5ckMdg3OJ7_9bU")
dp = Dispatcher()


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True) #Чтобы выключенный бот не копил команды
    await init_models()  # Инициализация БД
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
