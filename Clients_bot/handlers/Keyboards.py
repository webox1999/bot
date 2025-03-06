from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# Клавиатура с основными кнопками
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚗 Гараж"), KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="💳 История платежей"), KeyboardButton(text="✨ Подробнее о бонусах")],
        [KeyboardButton(text="📞 Отправить номер телефона", request_contact=True)]

    ],
    resize_keyboard=True
)

# Меню "История платежей"
payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Бонусы"), KeyboardButton(text="💵 Платежи")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

unAuth_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Отправить контакт", request_contact=True)],
        [KeyboardButton(text="✨ Подробнее о бонусах")]
    ],
    resize_keyboard=True
)