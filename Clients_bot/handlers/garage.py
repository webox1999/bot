# handlers/garage.py
from aiogram import Router, types, F
import requests
import aiohttp
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from Clients_bot.handlers.start import logger
from Clients_bot.utils.storage import user_phone_numbers
from Clients_bot.utils.helpers import get_field_value
from Clients_bot.config import SERVER_URL, API_URL
from Clients_bot.filters import IsAuthenticated
from Clients_bot.handlers.start import get_info, get_cars_for_delete
from Clients_bot.handlers.keyboards import unAuth_keyboard, garage_keyboard, cancel_keyboard_garage, yes_no_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


router = Router()

async def add_car_to_garage(message: types.Message, vin_code: str):
    """Отправляет VIN-код на API и добавляет авто в гараж."""
    user_id = str(message.from_user.id)

    # Получаем номер телефона пользователя
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        return await message.answer("⚠️ Ошибка: Не удалось получить номер телефона.")

    # Получаем client_id
    name, client_id = get_info(phone_number)
    if not client_id:
        return await message.answer("⚠️ Ошибка: Не удалось получить ваш ID. Попробуйте позже.")

    # Формируем URL запроса
    url = f"{API_URL}/add_car?id={client_id}&vin={vin_code}"

    # Отправляем запрос на API
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                # Проверяем результат
                if data.get("status") == "ok":
                    await message.answer(f"✅ Автомобиль с VIN **{vin_code}** успешно добавлен в гараж! 🚗", reply_markup=garage_keyboard)
                    await show_garage(message)
                else:
                    await message.answer(f"❌ Ошибка: {data.get('msg', 'Неизвестная ошибка')}")

            else:
                await message.answer("⚠️ Ошибка сервера. Попробуйте позже.")





# 🔹 Обработчик кнопки "Гараж"

@router.message(F.text == "🚗 Гараж", IsAuthenticated())
async def show_garage(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    print(f'Получили номеРа для гаража {phone_number} и {user_phone_numbers}')
    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()
        data = response.json()

        if "cars" in data and data["cars"]:
            text = "🚗 *Ваш гараж:*\n\n"
            for car in data["cars"]:
                text += (
                    f"🔹 *Марка:* {get_field_value(car, 'auto_maker_name', 'Неизвестный бренд')}\n"
                    f"   🚘 *Модель:* {get_field_value(car, 'auto_model')}\n"
                    f"   📅 *Год выпуска:* {get_field_value(car, 'made_year')}\n"
                    f"   ⚙️ *Двигатель:* {get_field_value(car, 'engine_num')}\n"
                    f"   🔢 *VIN:* {get_field_value(car, 'vin', 'Нет VIN')}\n\n"
                )
        else:
            text = "⛔ У вас нет зарегистрированных автомобилей."


        await message.answer(text, parse_mode="Markdown", reply_markup=garage_keyboard)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о гараже.")

# Создаем состояние для ожидания VIN-кода
class AddCarState(StatesGroup):
    waiting_for_vin = State()
    waiting_for_car = State()

# Обработчик кнопки "➕ Добавить авто"
@router.message(F.text == "➕ Добавить авто", IsAuthenticated())
async def ask_for_vin(message: types.Message, state: FSMContext):
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    """Запрашивает у пользователя VIN-код для добавления автомобиля."""
    await state.set_state(AddCarState.waiting_for_vin)
    await message.answer("🚗 Введите **VIN-код** вашего автомобиля:", reply_markup=cancel_keyboard_garage)

# Обработчик ввода VIN-кода (Шаг 3)
@router.message(AddCarState.waiting_for_vin)
async def process_vin_code(message: types.Message, state: FSMContext):
    """Получает VIN-код, проверяет его и отправляет запрос на API."""
    vin_code = message.text.strip().upper()

    # Проверяем длину VIN-кода (17 символов)
    if len(vin_code) != 17:
        return await message.answer("⚠️ VIN-код должен содержать 17 символов. Попробуйте еще раз.")

    # Сохраняем VIN и переходим к отправке на API
    await state.update_data(vin=vin_code)
    await message.answer(f"✅ VIN-код **{vin_code}** принят. Отправляем данные...", reply_markup=garage_keyboard)

    # Завершаем состояние
    await state.clear()

    # Переходим к следующему шагу: отправка VIN в API (Шаг 4)
    await add_car_to_garage(message, vin_code)




# Определим состояния
class DeleteCarState(StatesGroup):
    waiting_for_car_choice = State()
    waiting_for_car_delete_confirmation = State()

# Обработчик кнопки "➖ Удалить авто"
@router.message(F.text == "➖ Удалить авто", IsAuthenticated())
async def choose_car(message: types.Message, state: FSMContext):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return

    # Получаем список автомобилей
    cars = get_cars_for_delete(phone_number)
    if not cars:
        await message.answer("🚫 В вашем гараже нет автомобилей для удаления.", reply_markup=cancel_keyboard_garage)
        return

    formatted_cars = []  # Список для кнопок
    car_mapping = {}  # Словарь для быстрого поиска ID авто

    # Формируем текст для каждой машины
    for car_id, car_data in cars.items():
        brand = car_data.get("brand", "Неизвестный бренд") or "Неизвестный бренд"
        model = car_data.get("model", "Информация отсутствует") or "Информация отсутствует"
        vin = car_data.get("vin", "VIN не указан") or "VIN не указан"

        car_text = f"🚗 {brand} {model} | {vin}"
        formatted_cars.append(car_text)
        car_mapping[car_text] = car_id  # Связываем текст с ID авто

    # Если у пользователя только 1 авто, пропускаем выбор
    if len(formatted_cars) == 1:
        selected_car_text = formatted_cars[0]
        selected_car_id = car_mapping[selected_car_text]
        await state.update_data(car_id=selected_car_id)
        await message.answer(f"🚗 Выбран автомобиль: {selected_car_text}", reply_markup=garage_keyboard)
        await state.set_state(DeleteCarState.waiting_for_car_delete_confirmation)
        return await confirm_car_delete(message, state)

    # Создаём клавиатуру с авто
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=car)] for car in formatted_cars],
        resize_keyboard=True
    )

    await state.update_data(car_list=car_mapping)
    await state.set_state(DeleteCarState.waiting_for_car_choice)
    await message.answer("🚗 Выберите авто для удаления:", reply_markup=keyboard)

# Обработчик выбора автомобиля
@router.message(DeleteCarState.waiting_for_car_choice)
async def process_car_choice(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    car_list = user_data.get("car_list", {})

    selected_car_text = message.text
    if selected_car_text not in car_list:
        await message.answer("🚫 Выбранный автомобиль не найден. Пожалуйста, выберите автомобиль из списка.")
        return

    selected_car_id = car_list[selected_car_text]
    await state.update_data(car_id=selected_car_id)
    await message.answer(f"🚗 Выбран автомобиль: {selected_car_text}", reply_markup=garage_keyboard)
    await state.set_state(DeleteCarState.waiting_for_car_delete_confirmation)
    await confirm_car_delete(message, state)

# Подтверждение удаления автомобиля
async def confirm_car_delete(message: types.Message, state: FSMContext):
    await message.answer("❓ Вы уверены, что хотите удалить этот автомобиль? (да/нет)", reply_markup=yes_no_kb)

# Обработчик подтверждения удаления
@router.message(DeleteCarState.waiting_for_car_delete_confirmation)
async def process_car_delete_confirmation(message: types.Message, state: FSMContext):
    confirmation = message.text.strip().lower()
    if confirmation not in ["да", "нет"]:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'.")
        return

    if confirmation == "нет":
        await message.answer("🚗 Удаление отменено.", reply_markup=garage_keyboard)
        await state.clear()
        return

    user_data = await state.get_data()
    car_id = user_data.get("car_id")

    if not car_id:
        await message.answer("🚫 Ошибка: Не удалось получить ID автомобиля.")
        await state.clear()
        return

    await delete_car_from_garage(message, car_id)
    await state.clear()

@router.message(AddCarState.waiting_for_car)
async def process_car_delete(message: types.Message, state: FSMContext):
    """Получает VIN-код, проверяет его и отправляет запрос на API."""
    car_id = message.text.strip().upper()

    # Сохраняем car_id и переходим к отправке на API
    await state.update_data(id=car_id)
    await message.answer(f"✅ ID-авто **{car_id}** принято. Удаляем данные...", reply_markup=garage_keyboard)

    # Завершаем состояние
    await state.clear()

    # Переходим к следующему шагу: отправка VIN в API (Шаг 4)
    await delete_car_from_garage(message, car_id)

# Функция удаления автомобиля из гаража
async def delete_car_from_garage(message: types.Message, car_id: str):
    """Отправляет car_id на API и удаляет авто из гаража."""
    user_id = str(message.from_user.id)

    # Получаем номер телефона пользователя
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        return await message.answer("⚠️ Ошибка: Не удалось получить номер телефона.")

    # Получаем client_id
    name, client_id = get_info(phone_number)
    if not client_id:
        return await message.answer("⚠️ Ошибка: Не удалось получить ваш ID. Попробуйте позже.")

    try:
        # Формируем URL запроса для удаления
        url = f"{API_URL}/car_delete?id={car_id}"

        # Отправляем запрос на API для удаления автомобиля
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    # Успешное удаление
                    await message.answer(
                        f"✅ Автомобиль с ID **{car_id}** успешно удален из гаража! 🚗",
                        reply_markup=garage_keyboard,
                        parse_mode="Markdown"
                    )
                    await show_garage(message)
                else:
                    # Ошибка при удалении
                    await message.answer("⚠️ Ошибка сервера. Попробуйте позже.")

    except Exception as e:
        # Логируем ошибку и сообщаем пользователю
        print(f"Произошла ошибка: {e}")
        await message.answer("⚠️ Произошла ошибка при удалении автомобиля. Пожалуйста, попробуйте позже.")






@router.message(F.text == "Отмена", IsAuthenticated())
async def cancel_part_request(message: types.Message, state: FSMContext):
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    await state.clear()
    await message.answer("🔙 Вы возвращены в Гараж", reply_markup=garage_keyboard)

