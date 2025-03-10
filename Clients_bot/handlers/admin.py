from Clients_bot.handlers.start import *
import datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from Clients_bot.utils.admin_utils import load_admins, save_admins, is_admin,update_change_request, get_change_requests, get_client_id_by_request_id, get_new_users
from Clients_bot.handlers.auth import load_sessions
from Clients_bot.utils.storage import load_part_requests, save_part_requests
from Clients_bot.utils.auth import bind_phone_to_user, save_sessions, delete_phone_from_db
from Clients_bot.filters import IsAuthenticated
from Clients_bot.handlers.keyboards import admin_keyboard, admin_request_kb, admin_parts_request_kb, admin_change_request_kb

# Создаем роутер
router = Router()

@router.message(Command("admin"), IsAuthenticated())
@router.message(F.text == "Админ панель", IsAuthenticated())
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Выводит меню админа с клавиатурой"""
    await message.answer("🔧 *Админ-панель активирована!*\nВыберите действие:", reply_markup=admin_keyboard)

# Команда для добавления админа
@router.message(Command("add_admin"))
async def add_admin(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    try:
        new_admin_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("❌ Использование: /add_admin [TG ID]")

    admins = load_admins()
    if new_admin_id in admins:
        return await message.answer("✅ Этот пользователь уже является админом.")

    admins.append(new_admin_id)
    save_admins(admins)
    await message.answer(f"✅ Пользователь {new_admin_id} добавлен в админы.")


# Команда для удаления админа
@router.message(Command("remove_admin"))
async def remove_admin(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    try:
        admin_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.answer("❌ Использование: /remove_admin [TG ID]")

    admins = load_admins()
    if admin_id not in admins:
        return await message.answer("❌ Этот пользователь не является админом.")

    admins.remove(admin_id)
    save_admins(admins)
    await message.answer(f"✅ Пользователь {admin_id} удалён из админов.")


# Команда для просмотра списка админов
@router.message(Command("who_online"))
@router.message(F.text == "👑 Список админов")
async def who_online(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    admins = load_admins()
    if not admins:
        return await message.answer("📌 В списке админов никого нет.")

    admins_list = "\n".join([str(a) for a in admins])
    await message.answer(f"📌 Список админов:\n{admins_list}")



# Состояния
class CheckPhoneState(StatesGroup):
    waiting_for_phone = State()  # Состояние ожидания ввода номера

# Обработчик команды /check_phone и текста "🔎 Проверить клиента"
@router.message(Command("check_phone"))
@router.message(F.text == "🔎 Проверить клиента")
async def check_phone(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    # Если команда вызвана как /check_phone [номер]
    if message.text.startswith("/check_phone"):
        try:
            phone_number = message.text.split()[1]
            cleaned_phone_number = clean_phone_number(phone_number)
            await process_phone(message, cleaned_phone_number)
        except IndexError:
            await message.answer("❌ Использование: /check_phone [номер]")
        return

    # Если команда вызвана как "🔎 Проверить клиента"
    await message.answer("Введите номер клиента:")
    await state.set_state(CheckPhoneState.waiting_for_phone)  # Переводим в состояние ожидания

# Обработчик ввода номера телефона
@router.message(CheckPhoneState.waiting_for_phone)
async def process_phone_input(message: Message, state: FSMContext):
    phone_number = message.text
    cleaned_phone_number = clean_phone_number(phone_number)

    # Сохраняем номер пользователя
    user_phone_numbers[message.from_user.id] = cleaned_phone_number

    # Обрабатываем номер
    await process_phone(message, cleaned_phone_number)

    # Сбрасываем состояние
    await state.clear()


@router.message(Command("users_online"))
@router.message(F.text == "👥 Онлайн пользователи")
async def users_online(message: types.Message):
    """Отображает список активных пользователей"""
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав для просмотра активных пользователей.")

    sessions = load_sessions()
    if not sessions:
        return await message.answer("📭 Нет активных пользователей.")

    online_users = []
    now = datetime.datetime.now()

    for tg_id, data in sessions.items():
        phone = data.get("phone", "Не указан")
        name = data.get("name", "Неизвестный клиент")
        client_id = data.get("client_id", "Не указан")
        tg_name = data.get("full_name_tg", "Имя в тг не указано")
        username = data.get("username", "Не указан")
        last_active = data.get("last_active", "Нет данных")  # Добавляем дату последней активности

        # Форматируем время последней активности
        if isinstance(last_active, str):
            try:
                last_active = datetime.datetime.strptime(last_active, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                last_active = "Нет данных"

        if isinstance(last_active, datetime.datetime):
            time_diff = now - last_active
            last_active_text = f"{time_diff.seconds // 60} минут назад" if time_diff.seconds < 3600 else f"{time_diff.days} дн. назад"
        else:
            last_active_text = "Неизвестно"

        online_users.append(f"👤 {name} | TG {tg_name} \n📱 {phone} | Client ID {client_id} \n🤖 Username: {username} \n⏳ Был активен: {last_active_text}\n")

    # Собираем итоговый список
    response_text = "📌 *Список активных пользователей:*\n\n" + "\n".join(online_users)
    await message.answer(response_text, parse_mode="Markdown")

@router.message(F.text == "📜 Запросы")
async def show_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    await message.answer("*Меню запросов. Выберите категорию*", reply_markup=admin_request_kb)

@router.message(F.text == "Запросы запчастей клиентов")
async def show_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    await message.answer("*Меню запросов запчастей*", reply_markup=admin_parts_request_kb)

@router.message(F.text == "Запросы смены номера клиентов")
async def show_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    await message.answer("*Меню запросов для смены номера*", reply_markup=admin_change_request_kb)

@router.message(Command("requests_list"))
@router.message(F.text == "📜 Активные запросы клиентов")
async def show_active_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Показывает список активных запросов на детали."""
    requests = load_part_requests()
    active_requests = [req for req in requests if req["status"] == "active"]

    if not active_requests:
        return await message.answer("✅ Нет активных запросов на детали.")

    text = "📦 <b>Активные запросы:</b>\n\n"
    for req in active_requests:
        text += (
            f"🆔 <b>Запрос:</b> {req['request_id']}\n"
            f"👤 <b>Клиент:</b> {req['name']}\n"
            f"📞 <b>Телефон:</b> {req['phone_number']}\n"
            f"🚗 <b>Авто:</b> {req['car_info']}\n"
            f"🔍 <b>Деталь:</b> {req['part_name']}\n\n"
            f"💬 <b>Ответить:</b> /answer_{req['request_id']}\n"
            f"💬 <b>Отклонить:</b> /cancel_{req['request_id']}\n\n"
        )


    await message.answer(text, parse_mode="HTML")

class AnswerPartRequest(StatesGroup):
    waiting_for_answer = State()
    waiting_for_cancel = State()

@router.message(F.text.startswith("/answer_"))
async def start_answering_request(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Запрашиваем у администратора ответ на запрос."""
    request_id = message.text.split("_")[1]  # Извлекаем ID запроса
    requests = load_part_requests()

    request = next((req for req in requests if req["request_id"] == request_id and req["status"] == "active"), None)
    if not request:
        return await message.answer("⚠ Запрос уже закрыт или не найден.")

    await state.update_data(request_id=request_id)
    await state.set_state(AnswerPartRequest.waiting_for_answer)
    await message.answer(f"✍️ Введите ответ на запрос «{request['part_name']}» от {request['name']}:")

@router.message(AnswerPartRequest.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext, bot):
    """Отправляем ответ клиенту и обновляем статус запроса."""
    admin_answer = message.text
    data = await state.get_data()
    request_id = data["request_id"]

    requests = load_part_requests()
    request = next((req for req in requests if req["request_id"] == request_id), None)

    if not request:
        return await message.answer("⚠ Ошибка! Запрос не найден.")

    # Отправляем клиенту сообщение с ответом
    client_message = (
        f"📦 <b>Ответ на ваш запрос:</b>\n"
        f"🔹 {request['part_name']}\n"
        f"📩 <b>Сообщение от администратора:</b> {admin_answer}"
    )
    # Обновляем статус запроса
    request["status"] = "answered"
    request["answer"] = admin_answer
    save_part_requests(requests)
    await bot.send_message(request["user_id"], client_message, parse_mode="HTML")

    await message.answer("✅ Ответ отправлен клиенту.", reply_markup=admin_keyboard)
    await state.clear()

@router.message(F.text.startswith("/cancel_"))
async def start_answering_request(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Запрашиваем у администратора ответ на запрос."""
    request_id = message.text.split("_")[1]  # Извлекаем ID запроса
    requests = load_part_requests()

    request = next((req for req in requests if req["request_id"] == request_id and req["status"] == "active"), None)
    if not request:
        return await message.answer("⚠ Запрос уже закрыт или не найден.")

    await state.update_data(request_id=request_id)
    await state.set_state(AnswerPartRequest.waiting_for_cancel)
    await message.answer(f"✍️ Введите причину отказа для запроса: «{request['part_name']}» от {request['name']}:")

@router.message(AnswerPartRequest.waiting_for_cancel)
async def process_closing(message: types.Message, state: FSMContext, bot):
    """Отправляем ответ клиенту и обновляем статус запроса."""
    admin_answer = message.text
    data = await state.get_data()
    request_id = data["request_id"]

    requests = load_part_requests()
    request = next((req for req in requests if req["request_id"] == request_id), None)

    if not request:
        return await message.answer("⚠ Ошибка! Запрос не найден.")



    # Отправляем клиенту сообщение с ответом
    client_message = (
        f"📦 <b>Ваш запрос был отклонен:</b>\n"
        f"🔹 {request['part_name']}\n"
        f"📩 <b>Сообщение от администратора:</b> {admin_answer}"
    )

    # Обновляем статус запроса
    request["status"] = "closed"
    request["answer"] = admin_answer
    save_part_requests(requests)

    await bot.send_message(request["user_id"], client_message, parse_mode="HTML")

    await message.answer("✅ Ответ отправлен клиенту.", reply_markup=admin_keyboard)
    await state.clear()

@router.message(Command("requests_history"))
@router.message(F.text == "📜 История запросов клиентов")
async def show_request_history(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Показывает историю обработанных запросов."""
    requests = load_part_requests()
    answered_requests = [req for req in requests if req["status"] in ["answered", "closed"]]

    if not answered_requests:
        return await message.answer("📂 Нет обработанных запросов.")

    text = "📂 <b>История запросов:</b>\n\n"
    for req in answered_requests:
        text += (
            f"🆔 <b>Запрос:</b> {req['request_id']}\n"
            f"👤 <b>Клиент:</b> {req['name']}\n"
            f"📞 <b>Телефон:</b> {req['phone_number']}\n"
            f"🚗 <b>Авто:</b> {req['car_info']}\n"
            f"🔍 <b>Деталь:</b> {req['part_name']}\n\n"
            f"💬 <b>Статус:</b> {req['status']}\n"
            f"💬 <b>Ответ:</b> {req['answer']}\n\n"

        )

    await message.answer(text, parse_mode="HTML")

@router.message(Command("request_change"))
@router.message(F.text == "📜 Активные запросы клиентов(Смена номера)")
async def show_active_requests(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Показывает активные запросы на смену номера."""
    active_requests = get_change_requests(status="active")

    if not active_requests:
        await message.answer("Нет активных запросов на смену номера.")
        return

    for req in active_requests:
        await message.answer(
            f"Пользователь: {req['name']}, ID: {req['client_id']}\n"
            f"Номер: {req['current_phone']}\n"
            f"Новый номер: {req['new_phone']}\n"
            f"Подтвердить: /confirm_change_{req['id']}\n"
            f"Отклонить: /decline_change_{req['id']}"
        )

@router.message(Command("history_change"))
@router.message(F.text == "📜 История запросов клиентов(Смена номера)")
async def show_history_requests(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Показывает завершенные запросы на смену номера."""
    history_requests = get_change_requests()
    history_requests = [req for req in history_requests if req["status"] in ["done", "decline"]]

    if not history_requests:
        await message.answer("Нет завершенных запросов на смену номера.")
        return

    for req in history_requests:
        await message.answer(
            f"Пользователь: {req['name']}, ID: {req['client_id']}\n"
            f"Номер: {req['current_phone']}\n"
            f"Новый номер: {req['new_phone']}\n"
            f"Статус: {req['status']}"
        )

@router.message(F.text.startswith("/confirm_change_"))
async def confirm_change_request(message: Message,bot):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Подтверждает запрос на смену номера."""
    # Извлекаем request_id из текста сообщения
    request_id = message.text.split("_")[-1]

    if not request_id:
        await message.answer("❌ Не указан ID запроса.")
        return

    # Обновляем статус запроса
    update_change_request(request_id, status="done")


    # Удаляем из сессии и переменной
    user_id = str(get_client_id_by_request_id(request_id))
    sessions = load_sessions()
    if user_id not in sessions:
        print('Пользователь не найден в сессии')
    else:
        del sessions[user_id]
        save_sessions(sessions)
        delete_phone_from_db(user_id)



    # Привязываем новый номер

    requests = get_change_requests()
    for req in requests:
        if req["id"] == request_id:
            bind_phone_to_user(req["client_id"], req["new_phone"])
            client_message = (
                f"📦 <b>Ваш запрос на смену номера был подтвержден</b>\n"
                f"Новый номер телефона: {req['new_phone']}"
            )
            await message.answer(f"✅ Запрос {request_id} подтвержден. Номер изменен.")
            await bot.send_message(req["client_id"], client_message, parse_mode="HTML")
            break

@router.message(F.text.startswith("/decline_change_"))
async def decline_change_request(message: Message, bot):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Отклоняет запрос на смену номера."""
    # Извлекаем request_id из текста сообщения
    request_id = message.text.split("_")[-1]

    if not request_id:
        await message.answer("❌ Не указан ID запроса.")
        return
    client_message = (
        f"📦 <b>Ваш запрос на смену номера был отклонен</b>\n"
    )
    # Обновляем статус запроса
    update_change_request(request_id, status="decline")
    requests = get_change_requests()
    for req in requests:
        if req["id"] == request_id:
            await bot.send_message(req["client_id"], client_message, parse_mode="HTML")
            break

@router.message(Command("new_users"))
@router.message(F.text == "👤 Новые клиенты")
async def show_new_users(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")
    """Показывает завершенные запросы на смену номера."""
    show_users = get_new_users()

    if not show_users:
        await message.answer("Нет новый пользователей")
        return

    for req in show_users:
        if isinstance(req, dict):  # Проверяем, что req — это словарь
            await message.answer(
                f"Пользователь: {req['name']}, ID: {req['client_id']}\n"
                f"Номер: {req['phone']}\n"
                f"Имя в ТГ: {req['tg_name']}\n"
                f"Telegram ID: {req['tg_id']}"
            )
        else:
            print(f"Ошибка: req не является словарем. Тип req: {type(req)}")