import aiohttp
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import Command
from Clients_bot.utils.helpers import clean_phone_number
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.handlers.start import process_phone
from Clients_bot.handlers.keyboards import unAuth_keyboard, register_keyboard
from Clients_bot.config import SERVER_URL
from Clients_bot.utils.auth import load_sessions, save_sessions, is_authorized
from Clients_bot.handlers.registration import start_registration
#from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # Импортируем клавиатуру



router = Router()

async def check_phone(message: Message, phone_number: str):
    """Проверяет номер телефона по API, очищает его и сохраняет сессию"""
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Не указан"
    full_name_tg = message.from_user.full_name  # Имя в Telegram

    # Очищаем номер телефона
    phone_number = clean_phone_number(phone_number)
    user_phone_numbers[user_id] = phone_number  # Сохранение номера в глобальную переменную

    # Проверяем номер в API
    api_url = SERVER_URL + phone_number
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            try:
                data = await response.json()
            except Exception as e:
                print(f"❌ Ошибка запроса к API: {e}")
                return await message.answer("🚨 Ошибка сервера. Попробуйте позже.")

    # Если API вернул ошибку, клиент не найден – предлагаем регистрацию
    if data.get("error") == "Клиент не найден":
        return await message.answer(
            "🚨 Вашего номера нет в системе. Желаете зарегистрироваться?",
            reply_markup=register_keyboard
        )

    # ✅ Клиент найден – продолжаем авторизацию
    client_id = data.get("client_id", "Неизвестно")
    name = data.get("name", "Неизвестно")

    # Загружаем текущие сессии
    sessions = load_sessions()

    # Сохраняем данные пользователя в JSON
    sessions[user_id] = {
        "phone": phone_number,   # Очищенный номер
        "username": username,    # Telegram username
        "full_name_tg": full_name_tg,  # Полное имя в Telegram
        "client_id": client_id,  # ID клиента из API
        "name": name  # Имя клиента из базы API
    }
    save_sessions(sessions)

    await message.answer(f"✅ Вы успешно авторизованы!")
    await process_phone(message, phone_number)


# Обработчик контакта (автоматическая авторизация)
@router.message(F.contact)
async def get_contact_phone(message: Message):
    """Получает номер телефона из контакта, очищает его и проверяет в API"""
    if not message.contact:
        return await message.answer("❌ Не удалось получить номер.")

    phone_number = clean_phone_number(message.contact.phone_number)  # Очистка номера
    user_phone_numbers[message.from_user.id] = phone_number  # Сохранение номера в глобальную переменную

    await check_phone(message, phone_number)  # Проверка номера через API

@router.message(Command("logout"))
async def logout_user(message: Message):
    """Команда /logout – выход из системы"""
    user_id = str(message.from_user.id)
    sessions = load_sessions()

    if user_id not in sessions:
        return await message.answer("❌ Вы не авторизованы.")

    # Удаляем пользователя из сессий
    del sessions[user_id]
    save_sessions(sessions)

    # Удаляем номер телефона, если он есть в user_phone_numbers
    if user_id in user_phone_numbers:
        removed_phone = user_phone_numbers.pop(user_id)  # Теперь удаляется именно номер авторизованного пользователя

    await message.answer(
        "🔴 Вы успешно вышли из системы.\n\nЧтобы войти снова, отправьте свой контакт.",
        reply_markup=unAuth_keyboard  # Показываем клавиатуру снова
    )

# Обработчик для не авторизированых клиентов

@router.message()
async def handle_unauthorized(message: types.Message):
    """Этот обработчик ловит ВСЕ сообщения от неавторизованных пользователей"""

    user_id = str(message.from_user.id)

    sessions = load_sessions()
    if user_id not in sessions:
        return await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для входа.")

