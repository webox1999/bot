from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.handlers.keyboards import main_kb, cancel_keyboard, unAuth_keyboard
from Clients_bot.handlers.start import get_cars, get_info
from Clients_bot.utils.messaging import send_to_admins

router = Router()

# Состояние для ввода названия детали
class AskPartState(StatesGroup):
    waiting_for_part_name = State()

# Обработчик кнопки "Запрос детали"
@router.message(F.text == "📦 Запрос детали")
async def ask_for_part_name(message: types.Message, state: FSMContext):
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    """Запрашивает у пользователя название детали."""
    await state.set_state(AskPartState.waiting_for_part_name)
    await message.answer("Если ваш 🚗 авто еще не добавлен в гараж, добавьте чтобы поиск детали был точнее.\n 🔍 Введите название детали и  которую хотите найти:", reply_markup=cancel_keyboard)

@router.message(F.text == "❌ Отмена")
async def cancel_part_request(message: types.Message, state: FSMContext):
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    await state.clear()
    await message.answer("🔙 Вы возвращены в главное меню.", reply_markup=main_kb)

client_data = []

# Обработчик ввода названия детали
@router.message(StateFilter(AskPartState.waiting_for_part_name))
async def process_part_request(message: types.Message, state: FSMContext, bot):
    """Обрабатывает введённое название детали и отправляет запрос админу."""
    part_name = message.text.strip()
    user_id = str(message.from_user.id)
    phone_number = user_phone_numbers.get(user_id, "Не указан")
    full_name_tg = message.from_user.full_name

    # Получаем авто из гаража (если есть)
    cars = await get_cars(phone_number)
    car_info = cars if cars else "🚗 Авто не указано"
    client_data = get_info(phone_number)
    # Формируем запрос админу
    admin_message = (
        "📦 <b>Запрос детали</b>\n"
        f"👤 <b>Клиент:</b> {client_data[0]}\n"
        f"👤 <b>Клиент ID:</b> {client_data[1]}\n"
        f"🚗 <b>Авто:</b> {car_info}\n"
        f"🔍 <b>Запрос:</b> {part_name}\n"
        f"📞 <b>Контакт:</b> {phone_number}"
    )

    await send_to_admins(bot, admin_message)  # ✅ Теперь передаём `bot` как параметр

    # Оповещаем пользователя
    await message.answer("✅ Ваш запрос отправлен администратору. Ожидайте ответа.", reply_markup=main_kb)
    await state.clear()



