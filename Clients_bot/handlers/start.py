# handlers/start.py
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.config import SERVER_URL  # Абсолютный импорт
from Clients_bot.utils.helpers import clean_phone_number  # Абсолютный импорт
import logging
import requests

# 🔹 Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# Клавиатура с основными кнопками
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚗 Гараж"), KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="📞 Отправить номер телефона", request_contact=True)],
        [KeyboardButton(text="✨ Подробнее о бонусах")]
    ],
    resize_keyboard=True
)

@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Введи номер телефона клиента 📲 или отправь свой контакт:", reply_markup=main_kb)

# 🔹 Обработчик номера телефона (контакт)
@router.message(F.text.regexp(r"^\+?\d{10,15}$"))
async def get_manual_phone(message: types.Message):
    # Очищаем номер телефона
    cleaned_phone_number = clean_phone_number(message.text.strip())

    # Сохраняем номер пользователя
    user_phone_numbers[message.from_user.id] = cleaned_phone_number
    await process_phone(message, cleaned_phone_number)

# 🔹 Обработчик номера телефона (вручную)

@router.message(F.text.regexp(r"^\+?\d{10,15}$"))
async def get_manual_phone(message: types.Message):
    phone_number = message.text.strip()
    user_phone_numbers[message.from_user.id] = phone_number  # Сохраняем номер пользователя
    await process_phone(message, phone_number)

# 🔹 Функция обработки номера телефона
async def process_phone(message: types.Message, phone_number: str):
    logger.info(f"Получен номер: {phone_number}")
    await message.answer(f"🔍 Ищу информацию для номера: {phone_number}...")

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        logger.info(f"🔹 Ответ сервера: {data}")

        text = f"✅ *Данные клиента:*\n"
        text += f"👤 *Имя:* {data.get('name', 'Нет данных')}\n"
        text += f"💰 *Баланс:* {data.get('balance', 'Нет данных')} ₽\n"
        text += f"💸 *Бонусы:* {data.get('cashback', 'Нет данных')} ₽\n"
        text += f"📅 *Дата регистрации:* {data.get('reg_date', 'Нет данных')}\n"
        text += f"📊 *Оборот:* {data.get('oborot', 'Нет данных')} ₽\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=main_kb)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при подключении к серверу.")