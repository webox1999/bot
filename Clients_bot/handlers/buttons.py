# handlers/buttons.py
from aiogram import Router, types, F
from Clients_bot.handlers.start import user_phone_numbers, logger, process_phone
from Clients_bot.handlers.orders import group_orders, show_orders_list
from Clients_bot.config import SERVER_URL
import requests

router = Router()


# 🔹 Обработчик кнопки "🔙 Назад"
@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: types.Message):
    # Получаем номер телефона клиента
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return

    await process_phone(message, phone_number)

# Обработчик кнопки "🟡 Активные заказы"
@router.message(F.text.startswith("🟡 Активные заказы"))
async def show_active_orders(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()
        data = response.json()

        if "orders" not in data or not data["orders"]:
            await message.answer("⛔ У вас нет заказов.")
            return

        orders_grouped = group_orders(data["orders"])  # Группируем заказы
        await show_orders_list(message, orders_grouped, only_active=True)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о заказах.")

# Обработчик кнопки "🟢 Завершенные заказы"
@router.message(F.text.startswith("🟢 Завершенные заказы"))
async def show_completed_orders(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()
        data = response.json()

        if "orders" not in data or not data["orders"]:
            await message.answer("⛔ У вас нет заказов.")
            return

        orders_grouped = group_orders(data["orders"])  # Группируем заказы
        await show_orders_list(message, orders_grouped, only_completed=True)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о заказах.")

        #Обработчик для кнопки бонусов
@router.message(F.text == "✨ Подробнее о бонусах")
async def show_bonus_info(message: types.Message):
    text = (
        "✨ *Как работает наша бонусная система?* ✨\n\n"
        "💰 Копите бонусы при каждой покупке свыше 1000₽!\n"
        "🎁 Используйте бонусы для оплаты любых товаров в нашем магазине.\n\n"
        "🔹 Бонусы начисляются автоматически.\n"
        "🔹 Оплатить покупку можно, если накоплено 200 бонусов и более.\n"
        "🔹 1 бонус = 1 рубль скидки.\n\n"
        "🛒 Покупайте, накапливайте и экономьте вместе с нами! 🚀"
    )
    await message.answer(text, parse_mode="Markdown")