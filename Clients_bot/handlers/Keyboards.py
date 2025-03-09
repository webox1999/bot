from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from Clients_bot.utils.admin_utils import load_admins
# Клавиатура с основными кнопками

def main_kb(user_id):
    admins = load_admins()

    # Базовая клавиатура
    keyboard = [
        [KeyboardButton(text="🚗 Гараж"), KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="💳 История платежей"), KeyboardButton(text="✨ Подробнее о бонусах")],
        [KeyboardButton(text="🔍 Запрос детали"), KeyboardButton(text="🚪 Выйти")]
    ]

    # Если пользователь администратор, добавляем кнопку "Админ панель"
    if user_id in admins:
        keyboard.append([KeyboardButton(text="Админ панель")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# Меню "История платежей"
payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💵 Платежи"), KeyboardButton(text="💰 Бонусы")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Клавиатура для админов
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Онлайн пользователи"), KeyboardButton(text="👑 Список админов")],
        [KeyboardButton(text="🔎 Проверить клиента"), KeyboardButton(text="📜 Активные запросы")],
        [KeyboardButton(text="📜 История запросов")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

unAuth_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️Войти с помощью номера телефона📞", request_contact=True)],
        [KeyboardButton(text="✨ Подробнее о бонусах")]
    ],
    resize_keyboard=True
)

Auth_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️Войти в личный кабинет", request_contact=True)],
        [KeyboardButton(text="✨ Подробнее о бонусах")]
    ],
    resize_keyboard=True
)

back_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True
)

cancel_keyboard_garage = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
)

cancel_keyboard_parts = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Вернуться")]], resize_keyboard=True
)

garage_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить авто"),KeyboardButton(text="➖ Удалить авто")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)
yes_no_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да"),KeyboardButton(text="Нет")],
    ],
    resize_keyboard=True
)

confirmation_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
    ],
    resize_keyboard=True
)

register_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
    ],
    resize_keyboard=True
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить контакт", request_contact=True)]],
    resize_keyboard=True
)