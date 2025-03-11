from aiogram import Router, F
from aiogram.types import Message
import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from Clients_bot.utils.helpers import get_default_dates
from Clients_bot.utils.admin_utils import is_admin
from Clients_bot.handlers.keyboards import admin_keyboard
from Clients_bot.config import API_URL
from Clients_bot.utils.helpers import clean_phone_number

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


