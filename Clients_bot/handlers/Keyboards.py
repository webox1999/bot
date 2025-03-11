from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from Clients_bot.utils.admin_utils import load_admins
# Клавиатура с основными кнопками

def main_kb(user_id):
    admins = load_admins()

    # Базовая клавиатура
    keyboard = [
        [KeyboardButton(text="🚗 Гараж"), KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="💳 История платежей"),KeyboardButton(text="📜 Мои запросы") ],
        [KeyboardButton(text="🔍 Запрос детали"), KeyboardButton(text="ℹ Информация и бонусы")],
        [KeyboardButton(text="🚨 Сообщить о проблеме"), KeyboardButton(text="🚪 Выйти")]
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
        [KeyboardButton(text="🔎 Проверить клиента"), KeyboardButton(text="💲 Доход от клиента")],
        [KeyboardButton(text="👤 Новые клиенты"), KeyboardButton(text="📜 Запросы")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

admin_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Запросы запчастей клиентов"), KeyboardButton(text="Запросы смены номера клиентов")],
        [KeyboardButton(text="Админ панель")]
    ],
    resize_keyboard=True
)

my_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Запросы запчастей"), KeyboardButton(text="Запросы смены номера")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

admin_parts_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Активные запросы клиентов"), KeyboardButton(text="📜 История запросов клиентов")],
        [KeyboardButton(text="📜 Запросы")]
    ],
    resize_keyboard=True
)

my_parts_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Активные запросы"), KeyboardButton(text="📜 История запросов")],
        [KeyboardButton(text="📜 Мои запросы")]
    ],
    resize_keyboard=True
)

admin_change_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Активные запросы клиентов(Смена номера)"), KeyboardButton(text="📜 История запросов клиентов(Смена номера)")],
        [KeyboardButton(text="📜 Запросы")]
    ],
    resize_keyboard=True
)

my_change_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📜 Активные запросы(Смена номера)"), KeyboardButton(text="📜 История запросов(Смена номера)")],
        [KeyboardButton(text="📜 Мои запросы")]
    ],
    resize_keyboard=True
)

unAuth_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️Войти с помощью номера телефона📞", request_contact=True)],
        [KeyboardButton(text="ℹ Информация и бонусы")]
    ],
    resize_keyboard=True
)

Auth_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➡️Войти в личный кабинет", request_contact=True)],
        [KeyboardButton(text="ℹ Информация и бонусы")]
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

approved_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Подтвердить аккаунт")],
        [KeyboardButton(text="Отменить")]
    ],

    resize_keyboard=True
)