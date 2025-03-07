# handlers/orders.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from aiogram import Router, types, F
from Clients_bot.handlers.start import user_phone_numbers, logger
from Clients_bot.utils.delivery import calculate_delivery_date
from Clients_bot.utils.helpers import split_text
from Clients_bot.config import SERVER_URL
from Clients_bot.filters import IsAuthenticated
from Clients_bot.utils.auth import update_last_active

import requests


router = Router()
# Функция для подсчета активных и завершенных заказов

def count_orders(orders):
    active_count = 0
    completed_count = 0

    for order in orders:
        status = int(order.get("status", 0))
        if status in [12, 20, 21, 25, 30, 37, 40, 41, 2, 3, 1, 10, 11]:
            active_count += 1
        elif status in [70, 101, 102, 200, 201]:
            completed_count += 1

    return active_count, completed_count

# Функция для формирования текста статуса заказа
def get_status_text(status: int):
    status_texts = {
        70: "✅ Заказ выдан",
        101: "⚠ Отказ поставщика. Свяжитесь с менеджером",
        102: "⚠ Отменен менеджером.",
        12: "⏳ Обрабатывается",
        20: "🚚 Заказан у поставщика. Ожидается доставка",
        21: "🚚 Заказан у поставщика. Ожидается доставка",
        25: "🚚 Товар на складе у поставщика. Ожидается отправка",
        30: "🚚 В пути на склад",
        37: "📦 Товар поступил на склад",
        40: "📦 Готов к выдаче",
        41: "✅ Клиент оповещен, товар готов к выдаче",
        1: "📝 Заказ создан",
        2: "⏳ Обрабатывается",
        3: "💰 Оплачен",
        10: '🚚 Заказан у поставщика',
        11: '🚚 Заказан у поставщика',
        200: '🔄 Оформлен возврат',
        201: '🔄 Оформлен возврат'
    }
    return status_texts.get(status, "❓ Неизвестный статус")

# Функция для отображения меню заказов
async def show_order_menu(message: types.Message, active_count: int, completed_count: int):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🟡 Активные заказы ({active_count})")] if active_count > 0 else [],
            [KeyboardButton(text=f"🟢 Завершенные заказы ({completed_count})")] if completed_count > 0 else [],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

    text = (
        "📦 *Ваши заказы:*\n\n"
        f"🔹 *Активные заказы:* {active_count} шт.\n"
        f"✅ *Завершенные заказы:* {completed_count} шт."
    )

    if active_count == 0:
        text += "\n😕 *У вас нет текущих заказов.*"
    if completed_count == 0:
        text += "\n😔 *У вас нет завершенных заказов.*"

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# Группируем заказы

def group_orders(orders):
    """
    Группирует заказы по zakaz_id.
    :param orders: Список заказов.
    :return: Группированные заказы.
    """
    orders_grouped = {}

    for order in orders:
        zakaz_id = order.get("zakaz_id", "Неизвестный заказ")
        zakaz_date_str = order.get("create_date", "0000-00-00 00:00:00")
        delivery_days = order.get("time", "0")
        deliverer_id = order.get("deliverer_id", "0")
        order_cashback = order.get("cashback", 0)
        count = int(order.get("count", 1))

        try:
            zakaz_date = datetime.strptime(zakaz_date_str, "%Y-%m-%d %H:%M:%S")
            delivery_days = int(delivery_days)
            order_cashback = float(order_cashback)
        except ValueError:
            zakaz_date = "Неизвестная дата"
            delivery_days = 0

        if zakaz_id not in orders_grouped:
            orders_grouped[zakaz_id] = {
                "date": zakaz_date if isinstance(zakaz_date, str) else zakaz_date.strftime("%Y-%m-%d"),
                "items": [],
                "order_price": 0,
                "statuses": set(),
                "order_cashback": 0

            }

        price = order.get("price", "0")
        try:
            price = float(price)
        except ValueError:
            price = 0

        status = int(order.get("status", 0))
        status_text = get_status_text(status)

        # Учитываем количество товаров
        total_price = price * count  # Стоимость товара с учетом количества
        orders_grouped[zakaz_id]["order_price"] += total_price
        orders_grouped[zakaz_id]["statuses"].add(status)
        orders_grouped[zakaz_id]["order_cashback"] += order_cashback
        expected_delivery = ""
        if status in [12, 20, 21, 25, 30, 37, 40, 41, 2, 3, 1, 10, 11]:
            expected_delivery = calculate_delivery_date(zakaz_date_str, delivery_days, deliverer_id)

        item_text = (
            f"   \n🔸 *{order.get('name', 'Нет данных')}* ({order.get('article', '-')}) — {int(price):,} ₽\n"
            f"      🔹 *Количество:* {count}\n"
            f"      🔹 *Статус:* {status_text}\n"
        ).replace(",", " ")

        if expected_delivery:
            item_text += f"      🔹 *Ожидаемая дата доставки: 📅* {expected_delivery}\n"

        orders_grouped[zakaz_id]["items"].append(item_text)

    return orders_grouped

#Выводим необходимые заказы

async def show_orders_list(message: types.Message, orders_grouped: dict, only_active: bool = False, only_completed: bool = False):
    """
    Отображает список заказов (активных или завершенных).
    :param message: Объект сообщения.
    :param orders_grouped: Группированные заказы.
    :param only_active: Показывать только активные заказы.
    :param only_completed: Показывать только завершенные заказы.
    """
    text = "📦 *Ваши заказы:*\n\n"

    for zakaz_id, data in orders_grouped.items():
        # Фильтруем заказы по статусу
        if only_active and not any(status in data["statuses"] for status in [12, 20, 21, 25, 30, 37, 40, 41, 2, 3, 1, 10, 11]):
            continue
        if only_completed and not all(status == 70 for status in data["statuses"]):
            continue

        # Формируем текст для заказа
        text += f"🔹 *Заказ №{zakaz_id}* ({data['date']})\n"
        text += f"   💰 *Сумма заказа:* {int(data['order_price']):,} ₽\n"

        # Добавляем информацию о бонусах для завершенных заказов
        if only_completed:
            text += f"   🎁 *Начислено бонусов:* {int(data['order_cashback']):,} ₽\n"

        text += "   📦 *Товары:*\n"
        for item in data["items"]:
            text += item
        text += "\n"

    if not text.strip():
        text = "⛔ Нет заказов для отображения."

    await send_long_message(message, text, parse_mode="Markdown")


# Обрабатываем кнопку "Заказа" //Все остальные кнопки в buttons

# 🔹 Обработчик кнопки "📦 Заказы"
@router.message(F.text == "📦 Заказы", IsAuthenticated())
async def show_orders(message: types.Message):
    logger.info("📦 Кнопка 'Заказы' нажата!")

    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.")
        return

    try:
        # Запрос данных о заказах
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        if "orders" not in data or not data["orders"]:
            await message.answer(
                "⛔ У вас нет заказов.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔙 Назад")]],
                    resize_keyboard=True,
                   # one_time_keyboard=True
                )
            )
            return

        # Группировка заказов по zakaz_id
        orders_grouped = {}
        active_count = 0
        completed_count = 0
        total_completed_price = 0

        for order in data["orders"]:
            zakaz_id = order.get("zakaz_id", "Неизвестный заказ")
            zakaz_date_str = order.get("create_date", "0000-00-00 00:00:00")
            delivery_days = order.get("time", "0")
            deliverer_id = order.get("deliverer_id", "0")


            try:
                zakaz_date = datetime.strptime(zakaz_date_str, "%Y-%m-%d %H:%M:%S")
                delivery_days = int(delivery_days)
            except ValueError:
                zakaz_date = "Неизвестная дата"
                delivery_days = 0

            if zakaz_id not in orders_grouped:
                orders_grouped[zakaz_id] = {
                    "date": zakaz_date if isinstance(zakaz_date, str) else zakaz_date.strftime("%Y-%m-%d"),
                    "items": [],
                    "order_price": 0,
                    "statuses": set()
                }

            # Получаем цену и статус
            price = order.get("price", "0")
            try:
                price = float(price)
            except ValueError:
                price = 0

            status = int(order.get("status", 0))
            status_text = get_status_text(status)  # Используем функцию для получения текста статуса

            orders_grouped[zakaz_id]["order_price"] += price
            orders_grouped[zakaz_id]["statuses"].add(status)

            # Рассчитываем дату доставки для активных заказов
            expected_delivery = ""
            if status in [12, 20, 21, 25, 30, 37, 40, 41, 2, 3, 1, 10, 11]:
                expected_delivery = calculate_delivery_date(zakaz_date_str, delivery_days, deliverer_id)

            # Формируем текст для товара
            item_text = (
                f"   \n🔸 *{order.get('name', 'Нет данных')}* ({order.get('article', '-')}) — {int(price):,} ₽\n"
                f"      🔹 *Статус:* {status_text}\n"
            ).replace(",", " ")

            if expected_delivery:
                item_text += f"      🔹 *Ожидаемая дата доставки: 📅* {expected_delivery}\n"

            orders_grouped[zakaz_id]["items"].append(item_text)

        # Подсчитываем активные и завершенные заказы
        for zakaz_id, data in orders_grouped.items():
            if any(status in data["statuses"] for status in [12, 20, 21, 25, 30, 37, 40, 41, 2, 3, 1, 10, 11]):
                active_count += 1
            elif all(status == 70 for status in data["statuses"]):
                completed_count += 1
                total_completed_price += data["order_price"]

        # Отображаем меню с кнопками заказов
        await show_order_menu(message, active_count, completed_count)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о заказах.")

#Выводим длинное сообщение при необходимости

async def send_long_message(message: types.Message, text: str, parse_mode: str = "Markdown"):
    """
    Отправляет длинное сообщение, разбивая его на части.
    :param message: Объект сообщения.
    :param text: Текст для отправки.
    :param parse_mode: Режим форматирования (по умолчанию Markdown).
    """
    parts = split_text(text)
    for part in parts:
        await message.answer(part, parse_mode=parse_mode)