from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# Клавиатура с основными кнопками
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚗 Гараж"), KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="💳 История платежей"), KeyboardButton(text="✨ Подробнее о бонусах")],
        [KeyboardButton(text="📦 Запрос детали")]

    ],
    resize_keyboard=True
)

# Меню "История платежей"
payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💵 Платежи"), KeyboardButton(text="💰 Бонусы")],
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

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
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