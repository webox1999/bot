from aiogram import Router, types, F
from Clients_bot.handlers.start import router


#Обработчик для кнопки бонусов
@router.message(F.text == "✨ Подробнее о бонусах")
async def show_bonus_info(message: types.Message):
    text = (
        "✨ *Как работает наша бонусная система?* ✨\n\n"
        "💰 Копите бонусы при каждой покупке свыше 1000₽!\n"
        "🎁 Используйте бонусы для оплаты любых товаров в нашем магазине.\n\n"
        "🔹 Бонусы начисляются автоматически.\n"
        "🔹 Оплатить покупку можно, если накоплено 200 бонусов и более.\n"
        "🔹 1 бонус = 1 рубль скидки.\n\n"
        "🛒 Покупайте, накапливайте и экономьте вместе с нами! 🚀"
    )
    await message.answer(text, parse_mode="Markdown")