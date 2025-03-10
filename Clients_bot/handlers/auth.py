import aiohttp
import json
from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from Clients_bot.utils.helpers import clean_phone_number
from Clients_bot.utils.storage import user_phone_numbers, verification_codes
from Clients_bot.handlers.start import process_phone
from Clients_bot.handlers.keyboards import unAuth_keyboard, register_keyboard, confirmation_keyboard, main_kb, approved_keyboard
from Clients_bot.utils.admin_utils import is_admin,create_change_request, load_admins
from Clients_bot.config import SERVER_URL
from Clients_bot.utils.auth import load_sessions, save_sessions, is_phone_bound, bind_phone_to_user, USERS_FILE, unbind_phone
from Clients_bot.utils.auth import generate_verification_code, send_verification_code,is_user_bound, get_phone_by_telegram_id,delete_phone_from_db





router = Router()

async def check_phone(message: Message, phone_number: str):
    """Проверяет номер телефона по API, очищает его и сохраняет сессию"""
    user_id = message.from_user.id

    username = message.from_user.username or "Не указан"
    full_name_tg = message.from_user.full_name  # Имя в Telegram

    # Очищаем номер телефона
    phone_number = clean_phone_number(phone_number)
    user_phone_numbers[user_id] = phone_number  # Сохранение номера в глобальную переменную
    print(f'Получили номер для чек_фона {phone_number} и {user_phone_numbers}')
    # Проверяем номер в API
    api_url = SERVER_URL + phone_number
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            try:
                data = await response.json()
            except Exception as e:
                print(f"❌ Ошибка запроса к API: {e}")
                return await message.answer("🚨 Ошибка сервера. Попробуйте позже.")

    # Если API вернул ошибку, клиент не найден – предлагаем регистрацию
    if data.get("error") == "Клиент не найден":
        return await message.answer(
            "🚨 Вашего номера нет в системе. Желаете зарегистрироваться?",
            reply_markup=register_keyboard
        )

    # ✅ Клиент найден – продолжаем авторизацию
    client_id = data.get("client_id", "Неизвестно")
    name = data.get("name", "Неизвестно")

    # Загружаем текущие сессии
    sessions = load_sessions()

    # Сохраняем данные пользователя в JSON
    sessions[user_id] = {
        "phone": phone_number,   # Очищенный номер
        "username": username,    # Telegram username
        "full_name_tg": full_name_tg,  # Полное имя в Telegram
        "client_id": client_id,  # ID клиента из API
        "name": name  # Имя клиента из базы API
    }
    save_sessions(sessions)

    await message.answer(f"✅ Вы успешно авторизованы!")
    await process_phone(message, phone_number)


class ChangePhoneState(StatesGroup):
    waiting_for_code = State()  # Состояние ожидания ввода кода

@router.message(F.contact)
async def get_contact_phone(message: Message, bot, state: FSMContext):
    """Обработчик контакта (автоматическая авторизация)."""
    if not message.contact:
        return await message.answer("❌ Не удалось получить номер.")

    # Очистка номера
    phone_number = clean_phone_number(message.contact.phone_number)
    # Проверка, является ли пользователь админом
    if is_admin(message.from_user.id):
        await message.answer("✅ Доступ разрешен (админ).")
        await check_phone(message, phone_number)
        return

    # Проверка, привязан ли telegram_id к какому-либо номеру
    if is_user_bound(message.from_user.id):
        # Получаем номер, привязанный к текущему пользователю
        bound_phone = get_phone_by_telegram_id(message.from_user.id)

        # Если отправленный номер совпадает с привязанным
        if bound_phone == phone_number:
            await message.answer("⏳ Подождите идет верификации клиента")
            await check_phone(message, phone_number)
            return
        else:
            # Предложение сменить номер
            await message.answer(
                "❌ Ваш аккаунт уже привязан к другому номеру.\n"
                "Если вы хотите сменить номер, нажмите кнопку ниже.",
                reply_markup=approved_keyboard
            )
            # Сохраняем номер телефона в состоянии
            await state.update_data(phone_number=phone_number)
            return

    # Проверка, привязан ли номер к другому аккаунту
    if is_phone_bound(message.from_user.id, phone_number):
        # Предложение подтвердить смену номера
        await message.answer(
            "❌ Этот номер уже зарегистрирован на другом аккаунте.\n"
            "Если вы владелец этого номера, нажмите кнопку ниже, чтобы подтвердить смену.",
            reply_markup=approved_keyboard
        )
        # Сохраняем номер телефона в состоянии
        await state.update_data(phone_number=phone_number)
        return

    # Если номер не привязан ни к кому, добавляем его
    if bind_phone_to_user(message.from_user.id, phone_number):
        await message.answer("⏳ Подождите идет верификации клиента")
        await check_phone(message, phone_number)
    else:
        await message.answer("❌ Ошибка при привязке номера.")


# Состояния
class LogoutState(StatesGroup):
    waiting_for_confirmation = State()  # Состояние ожидания подтверждения

    @router.message(F.text == "Подтвердить аккаунт")
    async def confirm_account_change(message: Message, bot, state: FSMContext):
        """Обработчик подтверждения смены номера."""
        data = await state.get_data()
        phone_number = data.get("phone_number")

        if not phone_number:
            await message.answer("❌ Ошибка: номер телефона не найден.")
            return

        # Проверяем, привязан ли номер к другому аккаунту
        with open(USERS_FILE, "r") as f:
            users_data = json.load(f)

        old_telegram_id = None
        for user_id, user_phone in users_data.items():
            if user_phone == phone_number:
                old_telegram_id = int(user_id)
                break

        if old_telegram_id:
            # Если номер привязан к другому аккаунту, отправляем код подтверждения
            code = generate_verification_code()
            verification_codes[phone_number] = {
                "code": code,
                "new_telegram_id": message.from_user.id
            }

            await send_verification_code(bot, old_telegram_id, code)
            await message.answer("🔐 Код для смены номера был отправлен. Введите его тут.")
            await state.set_state(ChangePhoneState.waiting_for_code)
        else:
            # Если номер новый, создаем запрос на смену
            client_id = message.from_user.id
            name = message.from_user.full_name
            current_phone = get_phone_by_telegram_id(client_id)

            request_id = create_change_request(client_id, current_phone, phone_number, name)

            # Уведомляем админов
            admins = load_admins()
            for admin_id in admins:
                await bot.send_message(
                    admin_id,
                    f"Запрос о смене номера:\n"
                    f"Пользователь: {name}, ID: {client_id}\n"
                    f"Номер: {current_phone}\n"
                    f"Новый номер: {phone_number}\n"
                    f"Подтвердить: /confirm_change_{request_id}\n"
                    f"Отклонить: /decline_change_{request_id}"
                )

            await message.answer("✅ Запрос на смену номера отправлен. Дождитесь рассмотрения администратором.", reply_markup=unAuth_keyboard)
            await state.clear()

@router.message(ChangePhoneState.waiting_for_code)
async def handle_verification_code(message: Message, state: FSMContext):
    """Обработчик ввода кода подтверждения."""
    user_code = message.text.strip()

    # Получаем номер телефона из состояния
    data = await state.get_data()
    phone_number = data.get("phone_number")

    if not phone_number:
        await message.answer("❌ Ошибка: номер телефона не найден.")
        await state.clear()
        return

    # Проверка кода
    user_id = str(message.from_user.id)
    sessions = load_sessions()
    if phone_number in verification_codes and user_code == verification_codes[phone_number]["code"]:
        # Удаляем старую привязку номера
        unbind_phone(phone_number)
        # Удаляем из сессии и переменной
        if user_id not in sessions:
            print('Пользователь не найден в сессии')
        else:
            del sessions[user_id]
            save_sessions(sessions)
            delete_phone_from_db(user_id)
        # Привязываем номер к новому пользователю
        bind_phone_to_user(message.from_user.id, phone_number)

        await message.answer("✅ Номер успешно изменен!")
        del verification_codes[phone_number]  # Удаляем код из временного хранилища
    else:
        await message.answer("❌ Неверный код. Попробуйте еще раз.")

    await state.clear()

@router.message(F.text == "Отменить")
async def cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Вы отменили смену номера.", reply_markup=unAuth_keyboard)

# Обработчик команды /logout и текста "🚪 Выйти"
@router.message(Command("logout"))
@router.message(F.text == "🚪 Выйти")
async def logout_user(message: Message, state: FSMContext):
    """Команда /logout – выход из системы"""
    user_id = str(message.from_user.id)
    sessions = load_sessions()

    if user_id not in sessions:
        return await message.answer("❌ Вы не авторизованы.")



    # Переводим пользователя в состояние ожидания подтверждения
    await message.answer(
        "⚠️ Вы уверены, что хотите выйти?\n\n"
        "Если вы выйдете, вы больше не будете получать уведомления о статусе ваших заказов.",
        reply_markup=confirmation_keyboard
    )
    await state.set_state(LogoutState.waiting_for_confirmation)


# Обработчик подтверждения выхода
@router.message(LogoutState.waiting_for_confirmation)
async def confirm_logout(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    sessions = load_sessions()

    if message.text == "Да":
        # Удаляем пользователя из сессий
        del sessions[user_id]
        save_sessions(sessions)

        delete_phone_from_db(user_id)
        await message.answer(
            "🔴 Вы успешно вышли из системы.\n\nЧтобы войти снова, отправьте свой контакт.",
            reply_markup=unAuth_keyboard  # Показываем клавиатуру для неавторизованных пользователей
        )

        print(user_phone_numbers)
    elif message.text == "Нет":
        await message.answer(
            "🚪 Выход отменен.",
            reply_markup=main_kb(message.from_user.id)  # Возвращаем основную клавиатуру
        )
    else:
        await message.answer(
            "❌ Пожалуйста, выберите один из предложенных вариантов: ✅ Да или ❌ Нет.",
            reply_markup=confirmation_keyboard  # Показываем клавиатуру снова
        )

    # Сбрасываем состояние
    await state.clear()

# Обработчик для не авторизированых клиентов

@router.message()
async def handle_unauthorized(message: types.Message):
    """Этот обработчик ловит ВСЕ сообщения от неавторизованных пользователей"""

    user_id = str(message.from_user.id)

    sessions = load_sessions()
    if user_id not in sessions:
        return await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для входа.", reply_markup=unAuth_keyboard)

