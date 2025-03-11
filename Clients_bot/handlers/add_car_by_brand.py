from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

router = Router()
# Ваша функция для добавления авто
def add_car_by_brand(vin: str, brand: str, model: str, engine_code: str, year: str):
    """
    Функция для добавления автомобиля.
    :param vin: VIN-код автомобиля
    :param brand: Название бренда
    :param model: Название модели
    :param engine_code: Код двигателя
    :param year: Год выпуска
    """
    # Здесь ваша логика добавления авто
    print(f"Добавлен автомобиль: {brand} {model}, VIN: {vin}, Двигатель: {engine_code}, Год: {year}")


@router.message(Command("test"))
async def start(message: types.Message):
    vin = "testVIN123456"  # Пример VIN-кода
    client_id = 160295
    web_app_url = f"https://choosecar.duckdns.org/static/index.html?vin={vin}&client_id={client_id}"

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Выбрать бренд и модель",
        web_app=WebAppInfo(url=web_app_url)
    )

    await message.answer(
        "Нажмите кнопку, чтобы выбрать бренд и модель:",
        reply_markup=builder.as_markup()
    )
