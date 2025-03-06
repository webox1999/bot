from aiogram import Router, types, F
from Clients_bot.handlers.keyboards import payment_menu
from datetime import datetime, timedelta
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

# Обработчик кнопки "История платежей" (переход в подменю)
@router.message(F.text == "💳 История платежей")
async def show_payment_menu(message: types.Message):
    """Открывает подменю истории платежей"""
    await message.answer("Выберите категорию:", reply_markup=payment_menu)

# Функция для получения даты 180 месяц назад
def get_default_start_date():
    return (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")


# Обработчик кнопки "Платежи"
@router.message(F.text == "💵 Платежи")
async def request_payment_period(message: types.Message):
    """Запрашивает выбор периода для истории платежей"""
    start_date = get_default_start_date()
    end_date = datetime.now().strftime("%Y-%m-%d")
    await message.answer(
        f"📅 История платежей\n"
        f"Период: {start_date} – {end_date}\n\n"
        f"📅 Ваша история платежей за последние 180 дней.",
        reply_markup=payment_menu
    )

# Обработчик кнопки "Бонусы"
@router.message(F.text == "💰 Бонусы")
async def request_bonus_period(message: types.Message):
    """Запрашивает выбор периода для истории бонусов"""
    start_date = get_default_start_date()
    end_date = datetime.now().strftime("%Y-%m-%d")
    await message.answer(
        f"🎁 История бонусов\n"
        f"📅 Ваша история платежей за последние 180 дней.\n"
        f"Период: {start_date} – {end_date}\n\n",
        reply_markup=payment_menu
    )
