import sys
from pathlib import Path
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, orders, garage, bonuses, buttons, admin, auth, payments, registration


# Добавляем корневую папку проекта в sys.path
sys.path.append(str(Path(__file__).parent))



# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем обработчики
dp.include_router(start.router)
dp.include_router(orders.router)
dp.include_router(garage.router)
dp.include_router(payments.router)
dp.include_router(bonuses.router)
dp.include_router(buttons.router)
dp.include_router(admin.router)
dp.include_router(registration.router)
dp.include_router(auth.router)


async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())