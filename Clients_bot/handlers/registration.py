from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import json
import os
import aiohttp
from Clients_bot.handlers.keyboards import unAuth_keyboard, phone_keyboard, Auth_keyboard
from Clients_bot.utils.helpers import clean_phone_number
from Clients_bot.handlers.start import get_cars  # Получение авто
from Clients_bot.config import API_URL
from Clients_bot.utils.auth import DATA_PATH

router = Router()


# Машина состояний для регистрации
class RegistrationState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_vin = State()


@router.message(F.text == "❌ Нет")
async def cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Вы возвращены в главное меню.", reply_markup=unAuth_keyboard)


@router.message(F.text == "✅ Да")
async def start_registration(message: types.Message, state: FSMContext):
    await state.set_state(RegistrationState.waiting_for_name)
    await message.answer("✍️ Введите ваше **Имя и Фамилию**:")


@router.message(RegistrationState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(RegistrationState.waiting_for_phone)


    await message.answer(
        "📞 Введите **ваш номер телефона** или отправьте контакт кнопкой ниже:",
        reply_markup=phone_keyboard
    )


@router.message(RegistrationState.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone_number = clean_phone_number(message.contact.phone_number)
    await state.update_data(phone=phone_number)
    await request_vin(message, state)


@router.message(RegistrationState.waiting_for_phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext):
    phone_number = clean_phone_number(message.text.strip())
    await state.update_data(phone=phone_number)
    await request_vin(message, state)


async def request_vin(message: types.Message, state: FSMContext):
    await state.set_state(RegistrationState.waiting_for_vin)
    await message.answer(
        "🚗 Введите **VIN-код** вашего автомобиля,он добавиться в ваш Гараж клиента (необязательно, можете пропустить):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⏭ Пропустить VIN")]],
            resize_keyboard=True
        )
    )


@router.message(F.text == "⏭ Пропустить VIN", RegistrationState.waiting_for_vin)
async def skip_vin(message: types.Message, state: FSMContext):
    await state.update_data(vin=None)
    await register_client(message, state)


@router.message(RegistrationState.waiting_for_vin, F.text)
async def process_vin(message: types.Message, state: FSMContext):
    await state.update_data(vin=message.text.strip())
    await register_client(message, state)


async def register_client(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data["name"]
    phone_number = user_data["phone"]
    vin = user_data["vin"] or ""

    register_url = f"{API_URL}/register_client?name={name}&phone={phone_number}&type=3&bonuses=1232&vin={vin}"

    print(f"📡 Отправляем запрос на регистрацию:\n{register_url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(register_url) as response:
            try:
                data = await response.json()
                print(f"📩 Ответ от сервера регистрации:\n{data}")  # Лог ответа API
            except Exception as e:
                print(f"❌ Ошибка при запросе к API регистрации: {e}")
                return await message.answer("🚨 Ошибка сервера. Попробуйте позже.")

    if "companys" in data:
        return await message.answer("❌ Ошибка: Такой клиент уже зарегистрирован.", reply_markup=unAuth_keyboard)

    if data.get("dogovor_res", {}).get("status") == "ok":
        client_id = data.get("company_id", "Неизвестно")
        tg_id = message.from_user.id
        tg_name = message.from_user.full_name or "Не указан"
        await message.answer(f"✅ Вы успешно зарегистрированы!\n👤 {name}\n📱 {phone_number}")

        cars = await get_cars(phone_number)
        if cars:
            await message.answer(f"{cars}", reply_markup=Auth_keyboard)
        await save_new_user(tg_id, tg_name, name, phone_number, client_id)
        await state.clear()

    else:
        print("❌ Ошибка регистрации, сервер не вернул 'status': 'ok'")
        await message.answer("❌ Ошибка регистрации. Попробуйте позже.")


async def save_new_user(tg_id, tg_name, name, phone, client_id):
    """Добавляет нового пользователя в new_users.json"""
    if not os.path.exists("data"):
        os.makedirs("data")

    if not os.path.exists(DATA_PATH):
        data = {"users": []}
    else:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {"users": []}  # Если файл пустой или поврежден

    new_user = {
        "tg_id": str(tg_id),
        "tg_name": tg_name,
        "name": name,
        "phone": phone,
        "client_id": str(client_id)
    }

    # Проверяем, нет ли уже такого пользователя
    if not any(user["phone"] == phone for user in data["users"]):
        data["users"].append(new_user)

        with open(DATA_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"✅ Новый пользователь добавлен в new_users.json: {new_user}")
    else:
        print(f"ℹ Пользователь {phone} уже есть в базе.")
