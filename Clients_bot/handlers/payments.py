from aiogram import Router, types, F
from Clients_bot.handlers.keyboards import payment_menu
from Clients_bot.config import API_URL , SERVER_URL
from Clients_bot.handlers.start import get_bonuses
from Clients_bot.handlers.keyboards import unAuth_keyboard
from Clients_bot.filters import IsAuthenticated
from Clients_bot.utils.storage import user_phone_numbers  # Храним номера пользователей
import aiohttp
from datetime import datetime, timedelta

router = Router()

# 📌 Обработчик кнопки "История платежей" (показывает краткую инфу и меню выбора)
@router.message(F.text == "💳 История платежей", IsAuthenticated())
async def show_payment_summary(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        return await message.answer("❌ Вы не авторизованы! Отправьте контакт для входа.", reply_markup=unAuth_keyboard)

    # Получаем zakaz_id пользователя
    user_zakaz_ids = await get_user_zakaz_ids(phone_number)
    if not user_zakaz_ids:
        return await message.answer("📭 У вас нет заказов за последние 180 дней.")

    # Получаем платежи
    payments_data = await get_payments()
    payments = payments_data.get("payments", [])

    # Фильтруем платежи по zakaz_id
    user_payments = [p for p in payments if str(p.get("zakaz_id", "0")) in user_zakaz_ids and p.get("zakaz_id", "0") != "0"]

    # Подсчитываем суммы и количество операций
    total_payments = sum(int(float(p["summ"])) for p in user_payments if p["payment_type"] == "1")
    total_bonuses = sum(int(float(p["summ"])) for p in user_payments if p["payment_type"] == "8")
    count_payments = sum(1 for p in user_payments if p["payment_type"] == "1")
    count_bonuses = sum(1 for p in user_payments if p["payment_type"] == "8")

    # Формируем сообщение
    summary_text = (
        f"📊 *История платежей ({count_payments} операций)*\n"
        f"💰 *Сумма:* {total_payments:,} ₽\n\n"
        f"🎁 *История бонусов ({count_bonuses} начислений)*\n"
        f"💸 *Всего было накоплено:* {total_bonuses} бонусов\n"
        f"💰 *Текущий остаток:* {get_bonuses(phone_number)} бонусов"
    )

    await message.answer(summary_text, parse_mode="Markdown", reply_markup=payment_menu)

# 📌 Обработчик кнопки "Платежи" (только реальные платежи, без бонусов)
@router.message(F.text == "💵 Платежи")
async def show_full_payments(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        return await message.answer("❌ Вы не авторизованы! Отправьте контакт для входа.")

    await message.answer("⏳ Загружаем платежи...")

    user_zakaz_ids = await get_user_zakaz_ids(phone_number)
    payments_data = await get_payments()
    payments = payments_data.get("payments", [])

    # Фильтруем только реальные платежи (без payment_type: 8)
    user_payments = [
        p for p in payments
        if str(p.get("zakaz_id", "0")) in user_zakaz_ids and p.get("zakaz_id", "0") != "0" and p["payment_type"] == "1"
    ]

    if not user_payments:
        return await message.answer("📭 У вас нет платежей за последние 180 дней.")

    # 📌 Сортируем по дате (от старых к новым)
    user_payments.sort(key=lambda p: p.get("create_date", ""), reverse=False)

    # Формируем список платежей
    payment_text = "📊 *Подробная история платежей*\n\n"
    for p in user_payments:
        date = p.get("create_date", "Нет даты")[0:10]
        amount = int(float(p.get("summ", "0")))
        description = p.get("payment_target", "Нет описания")
        is_advance = p.get("is_advance") == "1"

        text = f"📅 {date} | {'✅' if amount > 0 else '❌'} {amount:,} ₽ | {description}"
        if is_advance:
            text = f"📅 {date} | {'✅' if amount > 0 else '❌'} {amount:,} ₽ | Аванс для заказа {description[14:21]}"
        payment_text += text + "\n"

    await message.answer(payment_text, parse_mode="Markdown")


# 📌 Обработчик кнопки "Бонусы" (сортируем так, чтобы списания шли перед начислениями)
@router.message(F.text == "💰 Бонусы")
async def show_full_bonuses(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        return await message.answer("❌ Вы не авторизованы! Отправьте контакт для входа.")

    await message.answer("⏳ Загружаем бонусы...")

    user_zakaz_ids = await get_user_zakaz_ids(phone_number)
    payments_data = await get_payments()
    payments = payments_data.get("payments", [])

    # Фильтруем бонусные списания (payment_type: 8)
    bonus_spendings = [
        p for p in payments
        if str(p.get("zakaz_id", "0")) in user_zakaz_ids and p.get("zakaz_id", "0") != "0" and p["payment_type"] == "8"
    ]

    # Получаем заказы для начислений бонусов
    orders_data = await get_orders(phone_number)
    orders = orders_data.get("orders", [])

    # Фильтруем только те заказы, которые дали кешбэк
    bonus_earnings = [
        o for o in orders if int(o.get("cashback", "0")) > 0
    ]

    if not bonus_spendings and not bonus_earnings:
        return await message.answer("📭 У вас нет бонусов за последние 180 дней.")

    # 📌 Сортируем бонусные списания (от старых к новым)
    bonus_spendings.sort(key=lambda p: p.get("create_date", ""), reverse=False)

    # 📌 Сортируем начисления (от старых к новым)
    bonus_earnings.sort(key=lambda o: o.get("create_date", ""), reverse=False)

    # 📌 Группируем по `zakaz_id`, чтобы сначала шли списания, потом начисления
    bonuses_by_order = {}

    # Добавляем списания бонусов
    for p in bonus_spendings:
        zakaz_id = p.get("zakaz_id", "Нет заказа")
        date = p.get("create_date", "Нет даты")[0:10]
        amount = int(float(p.get("summ", "0")))
        description = p.get("payment_target", "Оплата заказа")

        text = f"📅 {date} | ❌ -{amount} | Оплата заказа №{zakaz_id}"

        if zakaz_id not in bonuses_by_order:
            bonuses_by_order[zakaz_id] = []
        bonuses_by_order[zakaz_id].append(text)

    # Добавляем начисления бонусов
    for o in bonus_earnings:
        zakaz_id = o.get("zakaz_id", "Нет заказа")
        date = o.get("create_date", "Нет даты")[0:10]
        amount = int(o.get("cashback", "0"))

        text = f"📅 {date} | ✅ +{amount} | Начислено за заказ №{zakaz_id}"

        if zakaz_id not in bonuses_by_order:
            bonuses_by_order[zakaz_id] = []
        bonuses_by_order[zakaz_id].append(text)

    # 📌 Собираем финальный текст (по `zakaz_id`, сначала списания, потом начисления)
    bonus_text = "🎁 *Подробная история бонусов*\n\n"
    for zakaz_id in sorted(bonuses_by_order.keys(), key=lambda x: min([t.split(" | ")[0] for t in bonuses_by_order[x]])):
        for entry in bonuses_by_order[zakaz_id]:
            bonus_text += entry + "\n"

    await message.answer(bonus_text, parse_mode="Markdown")


# Функция для получения даты 180 месяц назад
def get_default_dates():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    return start_date, end_date

# Функция получения `zakaz_id` пользователя
async def get_user_zakaz_ids(phone_number):
    url = SERVER_URL + phone_number
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ Ошибка API: {response.status}")
                return set()

            data = await response.json()
            #print(f"📩 Полученные данные: {data}")  # Выводим JSON в консоль

            # Проверяем, есть ли ключ "orders" и является ли он списком
            orders = data.get("orders", [])
            if not isinstance(orders, list):
                print("❌ Ошибка: 'orders' не является списком")
                return set()

            # Извлекаем zakaz_id, преобразуем в set
            zakaz_ids = {order["zakaz_id"] for order in orders if "zakaz_id" in order}
           # print(f"✅ Полученные zakaz_id: {zakaz_ids}")  # Выводим результат

            return zakaz_ids  # Возвращаем уникальные zakaz_id

    return set()

# Функция получения платежей
async def get_payments():
    start_date, end_date = get_default_dates()
    url = f"{API_URL}/get_payments?start={start_date}&end={end_date}"
    #print(f"📡 Отправляем запрос: {url}")  # Выводим URL в консоль

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            #print(f"📩 Статус ответа: {response.status}")  # Выводим HTTP-статус

            if response.status == 200:
                data = await response.json()
               # print(f"📩 Полученные платежи: {data}")  # Выводим JSON в консоль
                return data  # Возвращаем ответ API

    print("❌ Ошибка: Платежи не получены")  # Если код != 200
    return {"history": []}

async def get_orders(phone_number):
    url = SERVER_URL + phone_number
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return {"orders": []}
            return await response.json()