from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import uuid
from typing import Optional
from Clients_bot.utils.admin_utils import  get_change_requests
from Clients_bot.utils.storage import load_part_requests, save_part_requests
from Clients_bot.filters import IsAuthenticated
from Clients_bot.utils.storage import user_phone_numbers,user_cars_names
from Clients_bot.handlers.keyboards import main_kb, cancel_keyboard_parts, unAuth_keyboard, my_request_kb, my_change_request_kb, my_parts_request_kb
from Clients_bot.handlers.start import get_cars_for_delete, get_info
from Clients_bot.utils.messaging import send_to_admins
from Clients_bot.utils.helpers import add_message_to_request

router = Router()

# Состояние для ввода названия детали
class AskPartState(StatesGroup):
    waiting_for_car_choice = State()
    waiting_for_part_name = State()


# Обработчик кнопки "Запрос детали"
@router.message(F.text == "🔎 Подобрать запчасть", IsAuthenticated())
async def ask_for_car_choice(message: types.Message, state: FSMContext):
    """Проверяем авторизацию у клиента перед запросом детали."""
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    """Запрашивает у клиента выбор автомобиля перед запросом детали."""
    phone_number = user_phone_numbers.get(message.from_user.id)

    # ✅ Получаем JSON-список авто клиента
    cars = get_cars_for_delete(phone_number)
    if not cars:
        await state.update_data(car_info="🚗 Авто не указано")
        return await ask_for_part_name(message, state)  # ✅ Если авто нет, сразу запрашиваем деталь

    formatted_cars = []  # Список для кнопок
    car_mapping = {}  # Словарь для быстрого поиска ID авто

    # ✅ Формируем текст для каждой машины
    for car_id, car_data in cars.items():
        brand = car_data.get("brand", "Неизвестный бренд")
        model = car_data.get("model", "Информация отсутствует")
        year = car_data.get("year", "Год не указан")
        vin = car_data.get("vin", "VIN не указан")

        car_text = f"🚗 {brand} {model} {year}| {vin}"
        formatted_cars.append(car_text)
        car_mapping[car_text] = car_id  # Связываем текст с ID авто

    # ✅ Если у пользователя только 1 авто, пропускаем выбор
    if len(formatted_cars) == 1:
        selected_car_text = formatted_cars[0]
        selected_car_id = car_mapping[selected_car_text]
        await state.update_data(car_info=selected_car_text, car_id=selected_car_id)
        return await ask_for_part_name(message, state)

    # ✅ Создаём клавиатуру с авто
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=car)] for car in formatted_cars],
        resize_keyboard=True
    )

    await state.update_data(car_list=car_mapping)
    await state.set_state(AskPartState.waiting_for_car_choice)
    await message.answer("🚗 Выберите авто для запроса:", reply_markup=keyboard)

@router.message(F.text == "Вернуться")
async def cancel_part_request(message: types.Message, state: FSMContext):
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    await state.clear()
    await message.answer("🔙 Вы возвращены в главное меню.", reply_markup=main_kb(message.from_user.id))

client_data = []

# Обработчик ввода названия детали
@router.message(AskPartState.waiting_for_car_choice)
async def save_car_choice(message: types.Message, state: FSMContext):
    """Сохраняет выбранное авто и переходит к вводу детали."""
    data = await state.get_data()
    car_list = data.get("car_list", [])

    if message.text not in car_list:
        return await message.answer("⚠ Пожалуйста, выберите авто из списка!")

    await state.update_data(car_info=message.text)
    await ask_for_part_name(message, state)

async def ask_for_part_name(message: types.Message, state: FSMContext):
    """Запрашивает у клиента название детали после выбора авто."""
    await state.set_state(AskPartState.waiting_for_part_name)
    await message.answer("🔍 Введите название детали, которую хотите найти:", reply_markup=cancel_keyboard_parts)

@router.message(AskPartState.waiting_for_part_name)
async def process_part_request(message: types.Message, state: FSMContext, bot, article: Optional[str] = None):
    """Сохраняет запрос клиента и отправляет уведомление админам."""

    # Проверяем, есть ли текст в сообщении
    if message.text:
        part_name = message.text.strip()
    else:
        part_name = "Неизвестная деталь"  # Подставляем заглушку, если текста нет
    user_id = str(message.from_user.id)
    full_name_tg = message.from_user.full_name
    phone = user_phone_numbers.get(message.from_user.id)
    name, client_id = get_info(phone)

    data = await state.get_data()
    car_info = data.get("car_info", "🚗 Авто не указано")

    requests = load_part_requests()
    request_id = str(uuid.uuid4())[:8]  # Генерируем ID запроса
    admin_message = (
        f"📦 <b>Новый запрос на деталь</b>\n"
        f"🆔 <b>Запрос:</b> {request_id}\n"
        f"👤 <b>Клиент:</b> {name} , ID: {client_id}\n"
        f"📞 <b>Телефон:</b> {phone}\n"
        f"🚗 <b>Авто:</b> {car_info}\n"
        f"🔍 <b>Деталь:</b> {part_name}\n\n"
        f"💬 <b>Ответить:</b> /answer_{request_id}\n"
        f"❌ <b>Отклонить и закрыть:</b> /cancel_{request_id}\n"
    )
    if car_info == "🚗 Авто не указано":
        car_info = user_cars_names[message.from_user.id]
    if article:
        part_name = f'Какая стоимость этой детали {article}'
        admin_message = (
            f"📦 <b>Новый запрос на деталь</b>\n"
            f"🆔 <b>Запрос:</b> {request_id}\n"
            f"👤 <b>Клиент:</b> {name} , ID: {client_id}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"🚗 <b>Авто:</b> {car_info}\n"
            f"🔍 <b>Деталь:</b> {part_name}\n"
            f"🔍 <b>Открыть запчасть:</b> /show_{article}\n\n"
            f"💬 <b>Ответить:</b> /answer_{request_id}\n"
            f"❌ <b>Отклонить и закрыть:</b> /cancel_{request_id}\n"
        )
    new_request = {
        "request_id": request_id,
        "user_id": user_id,
        "client_id": client_id,
        "phone_number": phone,
        "full_name": full_name_tg,
        "name": name,
        "part_name": part_name,
        "car_info": car_info,
        "status": "active",
        "admin_answer": None,
        "answer": None,
        "canceled_message": None

    }

    requests.append(new_request)
    save_part_requests(requests)

    await send_to_admins(bot, admin_message)
    await message.answer("✅ Ваш запрос отправлен администратору. Ожидайте ответа.", reply_markup=main_kb(message.from_user.id))
    await state.clear()

class ReplyPartRequest(StatesGroup):
    waiting_for_reply = State()


@router.message(F.text.startswith("/reply_"))
async def start_replyng_request(message: types.Message, state: FSMContext):
    """Запрашиваем у администратора ответ на запрос."""
    request_id = message.text.split("_")[1]  # Извлекаем ID запроса
    requests = load_part_requests()

    request = next((req for req in requests if req["request_id"] == request_id and req["status"] == "active"), None)
    if not request:
        return await message.answer("⚠ Запрос уже закрыт или не найден.")

    await state.update_data(request_id=request_id)
    await state.set_state(ReplyPartRequest.waiting_for_reply)
    await message.answer(f"✍️ Введите ответ администратору для запроса: «{request['part_name']}»")

@router.message(ReplyPartRequest.waiting_for_reply)
async def process_reply(message: types.Message, state: FSMContext, bot):
    """Отправляем ответ клиенту и обновляем статус запроса."""
    client_reply = message.text
    data = await state.get_data()
    request_id = data["request_id"]

    requests = load_part_requests()
    request = next((req for req in requests if req["request_id"] == request_id), None)

    if not request:
        return await message.answer("⚠ Ошибка! Запрос не найден.")

    # Отправляем Админу сообщение с ответом
    client_message = (
        f"📦 <b>Ответ для администратора:</b>\n"
        f"🔹 На запрос: {request['part_name']}\n"
        f"📩 <b>Сообщение от клиента:</b> {client_reply}\n\n"
        f"💬 <b>Ответить клиенту</b>  /answer_{request_id}\n"
        f"❌ <b>Закрыть запрос</b>  /cancel_{request_id}"
    )

    # ✅ Добавляем в историю (НЕ перезаписываем!)
    add_message_to_request(request_id, "client", client_reply)

    # Отправляем сообщение админу
    await send_to_admins(bot, client_message)

    await message.answer("✅ Ответ отправлен администратору.", reply_markup=main_kb(message.from_user.id))
    await state.clear()


@router.message(F.text == "📜 Мои запросы")
async def my_request(message: types.Message):
    await message.answer("*Меню запросов*.",
                         reply_markup=my_request_kb)

@router.message(F.text == "🛒 Запросы запчастей")
async def my_request(message: types.Message):
    await message.answer("*Меню запросов запчастей*.",
                         reply_markup=my_parts_request_kb)

@router.message(F.text == "📞 Запросы смены номера")
async def my_request(message: types.Message):
    await message.answer("*Меню запросов о смене номера*.",
                         reply_markup=my_change_request_kb)

@router.message(F.text == "📜 Активные запросы(Смена номера)")
async def show_my_change_requests(message: types.Message):

    phone_number = user_phone_numbers.get(message.from_user.id)
    history_requests = get_change_requests()
    history_requests = [
        req for req in history_requests
        if
        req["status"] in ["active"] and (req["current_phone"] == phone_number or req["new_phone"] == phone_number)
    ]

    if not history_requests:
        await message.answer("Активные запросы для смены номера отсутствуют.")
        return

    for req in history_requests:
        await message.answer(
            f"Пользователь: {req['name']}, ID: {req['client_id']}\n"
            f"Номер: {req['current_phone']}\n"
            f"Новый номер: {req['new_phone']}\n"
            f"Статус: {req['status']}"
        )

@router.message(F.text == "📜 История запросов(Смена номера)")
async def show_my_change_history_requests(message: types.Message):

    phone_number = user_phone_numbers.get(message.from_user.id)
    history_requests = get_change_requests()
    history_requests = [
        req for req in history_requests
        if
        req["status"] in ["decline", "done"] and (req["current_phone"] == phone_number or req["new_phone"] == phone_number)
    ]

    if not history_requests:
        await message.answer("Ваша история о смене номера пуста")
        return

    for req in history_requests:
        await message.answer(
            f"Пользователь: {req['name']}, ID: {req['client_id']}\n"
            f"Номер: {req['current_phone']}\n"
            f"Новый номер: {req['new_phone']}\n"
            f"Статус: {req['status']}"
        )

@router.message(F.text == "📌 Активные запросы")
async def show_my_parts_requests(message: types.Message):

    phone_number = user_phone_numbers.get(message.from_user.id)
    user_id = message.from_user.id
    history_requests = load_part_requests()
    history_requests = [
        req for req in history_requests
        if
        req["status"] in ["active"] and (req["user_id"] == user_id or req["phone_number"] == phone_number)
    ]

    if not history_requests:
        await message.answer("Активные запросы для подбора запчастей отсутствуют.")
        return

    text = "📦 <b>Активные запросы:</b>\n\n"

    for req in history_requests:
        # Последние ответы (без индексов)
        last_answer = req.get("answer", None)
        last_admin_answer = req.get("admin_answer", None)

        # Проверяем, есть ли история переписки (ключ "history" и он не пустой)
        has_history = "history" in req and req["history"]

        # Формируем текст с последними ответами
        last_answer_text = f"🗣 <b>Последний ответ клиента:</b> {last_answer}\n\n" if last_answer else ""
        last_admin_answer_text = f"🗣 <b>Последний ответ администратора:</b> {last_admin_answer}\n" if last_admin_answer else ""

        text += (
            f"🆔 <b>Запрос:</b> {req['request_id']}\n"
            f"👤 <b>Клиент:</b> {req['name']}\n"
            f"📞 <b>Телефон:</b> {req['phone_number']}\n"
            f"🚗 <b>Авто:</b> {req['car_info']}\n"
            f"🔍 <b>Деталь:</b> {req['part_name']}\n\n"
            f"{last_admin_answer_text}"
            f"{last_answer_text}"
            f"💬 <b>Ответить:</b> /reply_{req['request_id']}\n"
        )

        # Добавляем кнопку "Показать всю переписку", если есть история
        if has_history:
            text += (
                f"📜 <b>Показать всю переписку:</b> /details_{req['request_id']}\n"
                f"-------------------------------------------------------\n"
            )
        else:
            text += "\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📖 История запросов")
async def show_my_parts_history_requests(message: types.Message):

    phone_number = user_phone_numbers.get(message.from_user.id)
    user_id = message.from_user.id
    history_requests = load_part_requests()
    history_requests = [
        req for req in history_requests
        if
        req["status"] in ["answered", "closed"] and (req["user_id"] == user_id or req["phone_number"] == phone_number)
    ]

    if not history_requests:
        await message.answer("Ваша история о запросах запчастей пуста.")
        return
    text = "📦 <b>Ваша история запросов:</b>\n\n"

    for req in history_requests:
        # Последние ответы (без индексов)
        last_answer = req.get("answer", None)
        last_admin_answer = req.get("admin_answer", None)

        # Проверяем, есть ли история переписки (ключ "history" и он не пустой)
        has_history = "history" in req and req["history"]

        # Формируем текст с последними ответами
        last_answer_text = f"🗣 <b>Последний ответ клиента:</b> {last_answer}\n\n" if last_answer else ""
        last_admin_answer_text = f"🗣 <b>Последний ответ администратора:</b> {last_admin_answer}\n" if last_admin_answer else ""

        text += (
            f"🆔 <b>Запрос:</b> {req['request_id']}\n"
            f"👤 <b>Клиент:</b> {req['name']}\n"
            f"📞 <b>Телефон:</b> {req['phone_number']}\n"
            f"🚗 <b>Авто:</b> {req['car_info']}\n"
            f"🔍 <b>Деталь:</b> {req['part_name']}\n\n"
            f"{last_admin_answer_text}"
            f"{last_answer_text}"
            f"✅ <b>Запрос завершен по причине:</b> {req['canceled_message']}\n"
        )

        # Добавляем кнопку "Показать всю переписку", если есть история
        if has_history:
            text += (
                f"📜 <b>Показать всю переписку:</b> /details_{req['request_id']}\n"
                f"-------------------------------------------------------\n"
            )
        else:
            text += "\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text.startswith("/details_"))
async def show_detail_request(message: types.Message):
    """Показываем историю запроса с полными деталями."""
    request_id = message.text.split("_")[1]  # Извлекаем ID запроса

    details_requests = load_part_requests()
    request = next((req for req in details_requests if req["request_id"] == request_id), None)

    if not request:
        return await message.answer("⚠ Запрос уже закрыт или не найден.")

    # Начинаем формировать сообщение
    text = (
        f"📦 <b>Подробнее о запросе ID: {request_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {request['name']}\n"
        f"📞 <b>Телефон:</b> {request['phone_number']}\n"
        f"🚗 <b>Авто:</b> {request['car_info']}\n"
        f"🔍 <b>Деталь:</b> {request['part_name']}\n"
        f"📌 <b>Статус:</b> {request['status']}\n\n"
    )

    # Проверяем, есть ли история
    if "history" in request and request["history"]:
        text += "📜 <b>История переписки:</b>\n"
        for msg in request["history"]:
            sender = f"👤 {request['name']}" if msg["role"] == "client" else "👨‍💼 Менеджер"
            text += f"{sender}: {msg['message']}\n"

    await message.answer(text, parse_mode="HTML")


