import sys
from pathlib import Path
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from Clients_bot.utils.auth import load_sessions
from aiogram.fsm.storage.memory import MemoryStorage
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.utils.order_utils import initialize_orders, check_orders_status
from handlers import start, orders, garage, bonuses, buttons, admin, auth, payments, registration, ask_parts
initialized_numbers = set()

# Добавляем корневую папку проекта в sys.path
sys.path.append(str(Path(__file__).parent))



# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регистрируем обработчики
dp.include_router(start.router)
dp.include_router(orders.router)
dp.include_router(garage.router)
dp.include_router(payments.router)
dp.include_router(bonuses.router)
dp.include_router(buttons.router)
dp.include_router(admin.router)
dp.include_router(registration.router)
dp.include_router(ask_parts.router)
dp.include_router(auth.router)


async def initialize_all_orders():
    """Инициализирует заказы для всех активных сессий."""
    sessions = load_sessions()  # Загружаем активные сессии
    initialized_numbers = set()  # Множество для отслеживания инициализированных номеров

    for user_id, user_data in sessions.items():
        phone_number = user_data.get("phone")
        if phone_number and phone_number not in initialized_numbers:
            print(f"📞 Инициализация заказов для {phone_number}")
            await initialize_orders(phone_number)
            initialized_numbers.add(phone_number)  # Добавляем номер в множество

async def check_orders_background():
    """Фоновый процесс: проверяет статусы заказов каждые 20 секунд (для теста)."""
    global initialized_numbers  # Используем глобальное множество

    while True:
        print("🔄 Проверяем статусы заказов...")  # Лог для отслеживания работы

        sessions = load_sessions()  # Загружаем активные сессии
        if not sessions:
            print("⚠️ Нет активных сессий!")  # Лог, если сессий нет
            await asyncio.sleep(600)
            continue

        # Проверяем, есть ли новые пользователи
        for user_id, user_data in sessions.items():
            phone_number = user_data.get("phone")
            client_id = user_data.get("client_id")  # Используем client_id из сессии
            if phone_number and client_id and phone_number not in initialized_numbers:
                print(f"📞 Инициализация заказов для нового пользователя: {phone_number} (client_id: {client_id})")
                await initialize_orders(client_id, phone_number)
                initialized_numbers.add(phone_number)  # Добавляем номер в множество

        # Проверяем статусы заказов для всех активных сессий
        for user_id, user_data in sessions.items():
            phone_number = user_data.get("phone")
            client_id = user_data.get("client_id")  # Используем client_id из сессии
            if phone_number and client_id:
                print(f"📞 Проверяем заказы для {phone_number} (client_id: {client_id})")
                await check_orders_status(client_id, phone_number, user_id, bot)

        await asyncio.sleep(600)  # Проверяем каждые 20 секунд

async def main():

    #asyncio.create_task(initialize_all_orders())
    asyncio.create_task(check_orders_background())
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())