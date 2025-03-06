# handlers/garage.py
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests
from Clients_bot.handlers.start import logger
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.utils.helpers import get_field_value
from Clients_bot.config import SERVER_URL

router = Router()
# 🔹 Обработчик кнопки "Гараж"

@router.message(F.text == "🚗 Гараж")
async def show_garage(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()
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

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔙 Назад")]
            ],
            resize_keyboard=True
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о гараже.")