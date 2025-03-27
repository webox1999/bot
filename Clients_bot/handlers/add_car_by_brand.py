from aiogram import Router, types
from aiogram.filters import Command
from Clients_bot.config import INDEX_URL
from Clients_bot.handlers.start import get_info
from Clients_bot.utils.storage import user_cars_vins, user_phone_numbers, user_cars_ids
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional  # Импортируем Optional

router = Router()



async def add_car_by_brand(message: types.Message, vin, client_id, sended_from, car_id: Optional[str] = None):

    web_app_url = f"{INDEX_URL}?vin={vin}&client_id={client_id}&from={sended_from}&car_id={car_id}"
    print(web_app_url)
    builder = InlineKeyboardBuilder()
    if sended_from == 'change':
        builder.button(
            text="Редактировать автомобиль",
            web_app=WebAppInfo(url=web_app_url)
        )

        await message.answer(
            f"Чтобы отредактировать авто с VIN: {vin}"
            "Нажмите сюда ⬇",
            reply_markup=builder.as_markup()
        )
    else:
        builder.button(
            text="Выбрать бренд и модель",
            web_app=WebAppInfo(url=web_app_url)
        )

        await message.answer(
            "Нажмите сюда, чтобы выбрать бренд и модель:",
            reply_markup=builder.as_markup()
        )
@router.message(Command("update_car"))
async def procces_add_car(message: types.Message):
    user_id = message.from_user.id
    phone_number = user_phone_numbers[user_id]
    name, client_id = get_info(phone_number)
    vin = user_cars_vins[user_id]
    car_id = user_cars_ids[user_id]
    print(vin, client_id, car_id)
    await add_car_by_brand(message, vin, client_id, 'change', car_id)