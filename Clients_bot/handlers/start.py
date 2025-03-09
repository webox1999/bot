# handlers/start.py
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.filters import Command
from aiohttp import web
from aiogram.types import WebAppInfo
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.utils.auth import update_last_active
from Clients_bot.config import SERVER_URL,API_URL  # Абсолютный импорт
from Clients_bot.utils.helpers import clean_phone_number  # Абсолютный импорт
from Clients_bot.handlers.keyboards import main_kb, unAuth_keyboard
from Clients_bot.utils.helpers import get_field_value
import logging
import requests

# 🔹 Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Отправь номер телефона 📲 для начала работы с ботом.:", reply_markup=unAuth_keyboard)
    await update_last_active(message.from_user.id)
# 🔹 Обработчик номера телефона (вручную) - сейчас отключен
# @router.message(F.text.regexp(r"^\+?\d{10,15}$"))
# async def get_manual_phone(message: types.Message):
#     # Очищаем номер телефона
#     cleaned_phone_number = clean_phone_number(message.text.strip())
#
#     # Сохраняем номер пользователя
#     user_phone_numbers[message.from_user.id] = cleaned_phone_number
#     await process_phone(message, cleaned_phone_number)

# Обработчик для контакта(через отправить контакт) - Отключил временно проверка для авторизации
# @router.message(F.contact)
# async def get_contact_phone(message: Message):
#     """Получает номер телефона из контакта"""
#     if not message.contact:
#         return await message.answer("❌ Не удалось получить номер.")
#
#     phone_number = clean_phone_number(message.contact.phone_number)
#     user_phone_numbers[message.from_user.id] = phone_number
#
#     await process_phone(message, phone_number)

# 🔹 Функция обработки номера телефона
async def process_phone(message: types.Message, phone_number: str):
    logger.info(f"Получен номер: {phone_number}")

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

        await message.answer(text, parse_mode="Markdown", reply_markup=main_kb(message.from_user.id))
        await update_last_active(message.from_user.id)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Клиент не найден или номер пользователя отсутствует!")

def get_bonuses(phone_number):
    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        bonuses = data.get('cashback', 'Нет данных')
        return bonuses
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")

async def get_cars(phone_number):
    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        if "cars" in data and data["cars"]:
            text = "🚗 *Ваш гараж:*\n\n"
            for car in data["cars"]:
                text += (
                    f"🔹 *Марка:* {get_field_value(car, 'auto_maker_name', 'Неизвестный бренд')}\n"
                    f"   🚘 *Модель:* {get_field_value(car, 'auto_model')}\n"
                    f"   📅 *Год выпуска:* {get_field_value(car, 'made_year')}\n"
                    f"   ⚙️ *Двигатель:* {get_field_value(car, 'engine_num')}\n"
                    f"   🔢 *VIN:* {get_field_value(car, 'vin', 'Нет VIN')}\n\n"
                )
        else:
            text = "⛔ У вас нет зарегистрированных автомобилей."
        return text

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")

def get_cars_for_delete(phone_number):
    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        cars = {}  # Используем словарь для хранения данных об автомобилях

        if "cars" in data and data["cars"]:
            for car in data["cars"]:
                brand = car.get("auto_maker_name", "Неизвестный бренд")
                model = car.get("auto_model", "Неизвестная модель")
                vin = car.get("vin", "Нет VIN")
                car_id = car.get("id", "Нет id")

                # Добавляем данные автомобиля в словарь
                cars[car_id] = {
                    "brand": brand,
                    "model": model,
                    "vin": vin,
                    "id": car_id
                }

        print(cars)

        return cars

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return {}

def get_info(phone_number):
    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        name = data.get('name', 'Нет данных')
        client_id = data.get('client_id', 'Нет данных')
        return name, client_id

    except requests.exceptions.RequestException as e:

        logger.error(f"Ошибка при запросе к API: {e}")

def get_car_info(car_id):
    try:
        response = requests.get(f'{API_URL}/car_info?id={car_id}')
        response.raise_for_status()  # Проверка на ошибки HTTP
        if response.status_code == 200:
            return response.json()

    except requests.exceptions.RequestException as e:

        logger.error(f"Ошибка при запросе к API: {e}")

