import aiohttp
import json
import asyncio
from Clients_bot.config import STATUS_FILE, SERVER_URL, IGNORE_FILE

ORDERS_API = SERVER_URL

async def initialize_orders(client_id: str, phone_number: str):
    """Инициализирует заказы для нового пользователя, не перезаписывая существующие данные."""

    url = f"{ORDERS_API}{phone_number}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return
            data = await response.json()
            orders = data.get("orders", [])

    # Загружаем существующие данные
    order_statuses = load_json(STATUS_FILE)
    ignore_orders = load_json(IGNORE_FILE)

    # Инициализируем структуру для текущего клиента, если её нет
    if client_id not in order_statuses:
        order_statuses[client_id] = {}
    if client_id not in ignore_orders:
        ignore_orders[client_id] = {}

    # Добавляем данные для текущего клиента
    for order in orders:
        zakaz_id = order["zakaz_id"]
        detail_id = order["detail_id"]
        reorder_detail_id = order.get("reorder_detail_id", "0")  # Если нет reorder_detail_id, используем "0"
        new_status = order["status"]

        # Если деталь была перезаказана, обновляем статус существующей детали
        if reorder_detail_id != "0":
            for existing_zakaz_id, details in order_statuses[client_id].items():
                if reorder_detail_id in details:
                    details[reorder_detail_id] = new_status
                    break
            continue

        # Разделяем активные и завершённые заказы
        if new_status in ["70", "101", "102"]:
            ignore_orders[client_id].setdefault(zakaz_id, {})[detail_id] = new_status
        else:
            # Добавляем только новые заказы, не перезаписываем существующие
            if zakaz_id not in order_statuses[client_id] or detail_id not in order_statuses[client_id].get(zakaz_id, {}):
                order_statuses[client_id].setdefault(zakaz_id, {})[detail_id] = new_status

    # Сохраняем обновленные данные
    save_json(STATUS_FILE, order_statuses)
    save_json(IGNORE_FILE, ignore_orders)


async def check_orders_status(client_id: str, phone_number: str, user_id: str, bot):
    """Проверяет статусы заказов и отправляет уведомления при изменении."""
    print(f"🔍 Запрос обновления заказов для {phone_number} (client_id: {client_id})")

    url = f"{ORDERS_API}{phone_number}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return
            data = await response.json()
            orders = data.get("orders", [])

    old_statuses = load_json(STATUS_FILE).get(client_id, {})
    ignore_orders = load_json(IGNORE_FILE).get(client_id, {})

    new_statuses = {}
    new_orders = []
    status_changes = {}
    completed_orders = {}

    for order in orders:
        zakaz_id = order["zakaz_id"]
        detail_id = order["detail_id"]
        reorder_detail_id = order.get("reorder_detail_id", "0")  # Если нет reorder_detail_id, используем "0"
        part_name = order["name"]
        new_status = order["status"]

        # Если деталь была перезаказана, обновляем статус существующей детали
        if reorder_detail_id != "0":
            for existing_zakaz_id, details in old_statuses.items():
                if reorder_detail_id in details:
                    old_status = details[reorder_detail_id]
                    if old_status != new_status:
                        if new_status in ["70", "101", "102"]:
                            completed_orders.setdefault(existing_zakaz_id, []).append((reorder_detail_id, part_name, new_status))
                        else:
                            status_changes.setdefault(existing_zakaz_id, []).append((reorder_detail_id, part_name, new_status))
                    break
            continue

        if zakaz_id in ignore_orders:
            continue

        if zakaz_id not in new_statuses:
            new_statuses[zakaz_id] = {}

        if zakaz_id not in old_statuses or detail_id not in old_statuses.get(zakaz_id, {}):
            new_orders.append((zakaz_id, detail_id, part_name, new_status))
        else:
            old_status = old_statuses[zakaz_id][detail_id]
            if old_status != new_status:
                if new_status in ["70", "101", "102"]:
                    completed_orders.setdefault(zakaz_id, []).append((detail_id, part_name, new_status))
                else:
                    status_changes.setdefault(zakaz_id, []).append((detail_id, part_name, new_status))

        new_statuses[zakaz_id][detail_id] = new_status

    # Сохраняем обновленные данные для текущего клиента
    order_statuses = load_json(STATUS_FILE)
    order_statuses[client_id] = new_statuses
    save_json(STATUS_FILE, order_statuses)

    await send_order_notifications(user_id, new_orders, status_changes, completed_orders, bot)

    # Обновляем ignore_orders для текущего клиента
    for zakaz_id, details in completed_orders.items():
        ignore_orders[zakaz_id] = {detail_id: status for detail_id, _, status in details}
        ignore_data = load_json(IGNORE_FILE)
        ignore_data[client_id] = ignore_orders
        save_json(IGNORE_FILE, ignore_data)


async def send_order_notifications(user_id: str, new_orders: list, status_changes: dict, completed_orders: dict, bot):
    """Отправляет уведомления пользователю о новых заказах, изменениях статусов и завершении заказов."""
    grouped_orders = {}

    # Уведомления о новых заказах
    for zakaz_id, detail_id, part_name, status in new_orders:
        grouped_orders.setdefault(zakaz_id, []).append(f"🔹 {part_name} – {get_status_text(status)}")

    for zakaz_id, details in grouped_orders.items():
        message = f"📦 Ваш заказ №{zakaz_id} был создан:\n" + "\n".join(details)
        await bot.send_message(user_id, message)

    # Уведомления об изменении статусов
    for zakaz_id, changes in status_changes.items():
        message = f"📦 Заказ №{zakaz_id} статус обновлён:\n"
        message += "\n".join([f"🔹 {part} – {get_status_text(status)}" for _, part, status in changes])
        await bot.send_message(user_id, message)

    # Уведомления о завершении заказов
    for zakaz_id, changes in completed_orders.items():
        message = f"✅ Заказ №{zakaz_id} завершён:\n"
        message += "\n".join([f"🔹 {part} – {get_status_text(status)}" for _, part, status in changes])
        await bot.send_message(user_id, message)


def load_json(filename):
    """Загружает данные из JSON, если файл существует"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filename, data):
    """Сохраняет данные в JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_status_text(status_code):
    """Преобразует код статуса в читаемый текст"""
    status_dict = {
        "70": "✅ Заказ выдан",
        "101": "⚠ Отказ поставщика. Свяжитесь с менеджером",
        "102": "⚠ Отменен менеджером.",
        "12": "⏳ Обрабатывается",
        "20": "🚚 Заказан у поставщика. Ожидается доставка",
        "21": "🚚 Заказан у поставщика. Ожидается доставка",
        "25": "🚚 Товар на складе у поставщика. Ожидается отправка",
        "30": "🚚 В пути на склад",
        "35": "🚚 В пути на склад",
        '37': "📦 Товар поступил на склад",
        "40": "📦 Готов к выдаче",
        '41': "✅ Клиент оповещен, товар готов к выдаче",
        '1': "📝 Заказ создан",
        '2': "⏳ Обрабатывается",
        '3': "💰 Оплачен",
        '10': '🚚 Заказан у поставщика',
        '11': '🚚 Заказан у поставщика',
        '200': '🔄 Оформлен возврат',
        '201': '🔄 Оформлен возврат'
    }
    return status_dict.get(str(status_code), "Неизвестный статус")