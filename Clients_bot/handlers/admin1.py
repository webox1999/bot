from aiogram import Router, F
from aiogram.types import Message
import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from Clients_bot.utils.helpers import get_default_dates
from Clients_bot.utils.admin_utils import is_admin
from Clients_bot.handlers.keyboards import admin_keyboard, choose_metod_kb
from Clients_bot.config import API_URL
from Clients_bot.utils.helpers import clean_phone_number
from Clients_bot.utils.messaging import send_to_all,load_codes,save_codes,delete_code_from_profile
from datetime import datetime, timedelta

# Создаем роутер
router = Router()


async def get_profit_user(phone_number):
    """Рассчитывает валовую прибыль, процент наценки и выводит отчёт."""
    start_date, end_date = get_default_dates()
    url = f"{API_URL}/get_profit?phone={phone_number}&start={start_date}&end={end_date}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                sales_volume = float(data.get("sale_sum"))
                cost_price = float(data.get("dealer_sum"))
                name = data.get("name")
                client_id = data.get("client_id")
    if cost_price == 0:  # Проверяем деление на ноль
        return "Ошибка: Себестоимость не может быть 0"

    # Расчёт валовой прибыли
    gross_profit = sales_volume - cost_price

    # Расчёт среднего процента наценки
    markup_percentage = (gross_profit / cost_price) * 100

    # Форматируем числа до 2 знаков после запятой
    sales_volume = f"{sales_volume:,.2f}".replace(",", " ")
    cost_price = f"{cost_price:,.2f}".replace(",", " ")
    gross_profit = f"{gross_profit:,.2f}".replace(",", " ")
    markup_percentage = f"{markup_percentage:.2f} %"

    # Вывод результата
    result = (
        f"📊 <b>Расчёт прибыли по клиенту</b>\n"
        f"👤 <b>Клиент:</b> {name} | 🆔 <b>ID:</b> {client_id}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 1️⃣ <b>Объем продаж:</b> {sales_volume} ₽\n"
        f"📉 2️⃣ <b>Себестоимость проданной продукции:</b> {cost_price} ₽\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 3️⃣ <b>Средний процент наценки:</b> {markup_percentage}\n"
        f"💵 4️⃣ <b>Итого валовая прибыль:</b> {gross_profit} ₽\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    return result



class CheckProfitState(StatesGroup):
    waiting_for_profit_phone = State()  # Состояние ожидания ввода номера



@router.message(Command("check_profit"))
@router.message(F.text == "💲 Доход от клиента")
async def profit_from_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    # Если команда вызвана как /check_phone [номер]
    if message.text.startswith("/check_profit"):
        try:
            phone_number = message.text.split()[1]
            cleaned_phone_number = clean_phone_number(phone_number)
            await get_profit_user(cleaned_phone_number)
        except IndexError:
            await message.answer("❌ Использование: /check_profit [номер]")
        return

    # Если команда вызвана как "🔎 Проверить клиента"
    await message.answer("Введите номер клиента:")
    await state.set_state(CheckProfitState.waiting_for_profit_phone)  # Переводим в состояние ожидания

# Обработчик ввода номера телефона
@router.message(CheckProfitState.waiting_for_profit_phone)
async def process_phone_input(message: Message, state: FSMContext):
    phone_number = message.text
    cleaned_phone_number = clean_phone_number(phone_number)

    # Обрабатываем номер
    profit_message = await get_profit_user(cleaned_phone_number)
    print(profit_message)
    # Сбрасываем состояние
    await state.clear()
    await message.answer(profit_message, parse_mode="HTML", reply_markup=admin_keyboard)


class SendMessageState(StatesGroup):
    waiting_for_message = State()  # Состояние ожидания ввода номера
    waiting_for_percent = State()
    waiting_for_code = State()

@router.message(Command("send"))
@router.message(F.text == "💬 Отправить сообщение")
async def choose_metod_message(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    await message.answer('Выберите тип отправки сообщения', reply_markup=choose_metod_kb)

@router.message(Command("send_all_discount"))
@router.message(F.text == "🏷 Сообщение всем с купоном")
async def send_for_all_discount(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    text = (
            "⚠ Внимание! Введите данные в формате:\n"
            "📌 **Пример:** `5-7`\n"
            "🔹 5% скидка, действует 7 дней."
        )
    await message.answer(text)
    await state.set_state(SendMessageState.waiting_for_percent)  # Переводим в состояние ожидания

@router.message(SendMessageState.waiting_for_percent)
async def process_percent_input(message: Message, state: FSMContext):
    validity = message.text.split("-")[1]  # Извлекаем ID запроса
    percent = message.text.split("-")[0]

    # Обновляем данные состояния
    await state.update_data(percent=percent, validity=validity)

    await message.answer("Введите текст сообщения, которое хотите отправить всем активным клиентам:")
    await state.set_state(SendMessageState.waiting_for_message)  # Переводим в состояние ожидания

@router.message(SendMessageState.waiting_for_message)
async def process_text_input_discount(message: Message, state: FSMContext, bot):
    text = message.text
    admin_id = message.from_user.id
    # Получаем данные состояния
    data = await state.get_data()
    percent = data.get('percent')
    validity = data.get('validity')

    # Сбрасываем состояние
    await state.clear()

    # Отправляем сообщение всем клиентам
    await send_to_all(bot, admin_id, text, percent, validity)


@router.message(Command("send_all"))
@router.message(F.text == "💬 Сообщение всем")
async def send_for_all(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    await message.answer("Введите текст сообщения, которое хотите отправить всем активным клиентам:")
    await state.set_state(SendMessageState.waiting_for_message)  # Переводим в состояние ожидания

@router.message(SendMessageState.waiting_for_message)
async def process_text_input(message: Message, state: FSMContext, bot):
    text = message.text
    admin_id = message.from_user.id

    # Сбрасываем состояние
    await state.clear()

    # Отправляем сообщение всем клиентам
    await send_to_all(bot, admin_id, text)

@router.message(Command("use_code"))
@router.message(F.text == "Активировать купон")
async def send_for_all(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    await message.answer("Введите код предоставленый клиентом:")
    await state.set_state(SendMessageState.waiting_for_code)  # Переводим в состояние ожидания

@router.message(SendMessageState.waiting_for_code)
async def process_code_input(message: Message, state: FSMContext, bot):
    code_from_admin = message.text


    # Сбрасываем состояние
    await state.clear()

    # Отправляем сообщение всем клиентам
    await check_code(message, code_from_admin)


async def check_code(message: Message, code):
    data_code = load_codes()

    # Найдем код в JSON
    request = next((req for req in data_code if req["sale_code"] == code), None)

    # Если кода нет в базе
    if not request:
        return await message.answer("⚠ Код отсутствует в системе.")

    # Если код уже использован
    if request["status"] == "used":
        return await message.answer(
            f"⚠ Этот код уже был использован!\n"
            f"📅 Дата использования: {request['date']}."
        )

    # Проверяем срок действия кода
    code_date = datetime.strptime(request["date"], "%Y-%m-%d %H:%M:%S")
    validity_days = request.get("validity", 0)  # Получаем кол-во дней (по умолчанию 0)
    expiry_date = code_date + timedelta(days=validity_days)

    if datetime.now() > expiry_date:
        request["status"] = "expired"
        save_codes(data_code)  # Сохраняем изменения
        return await message.answer(
            f"⚠ Срок действия этого кода истёк.\n"
            f"⏳ Истек: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # Если код активен, используем его
    text = (
        f"🎟 **Скидочный купон**\n"
        f"📅 Дата создания кода: {request['date']}\n"
        f"👨‍💻 Кем был создан: {request['admin']}\n"
        f"👤 Имя клиента: {request['name']}\n"
        f"💰 Скидка: {request['percent']}%\n\n"
        f"✅ **Код успешно использован!**"
    )

    request["status"] = "used"
    request["used_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_id = request.get('client_id')
    await delete_code_from_profile(client_id, code)  # Удаляем купон у клиента
    save_codes(data_code)  # Сохраняем обновленный JSON
    await message.answer(text)
