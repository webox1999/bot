# handlers/buttons.py
from aiogram import Router, types, F
from Clients_bot.handlers.start import user_phone_numbers, logger, process_phone
from Clients_bot.handlers.orders import group_orders, show_orders_list
from Clients_bot.utils.messaging import send_to_admins
from Clients_bot.handlers.start import get_info
from Clients_bot.handlers.keyboards import main_kb,back_keyboard
from Clients_bot.config import SERVER_URL
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import requests

router = Router()


# 🔹 Обработчик кнопки "🔙 Назад"
@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    # Получаем номер телефона клиента
    phone_number = user_phone_numbers.get(message.from_user.id)

    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return
    await state.clear()
    await process_phone(message, phone_number)

# Обработчик кнопки "🟡 Активные заказы"
@router.message(F.text.startswith("🟡 Активные заказы"))
async def show_active_orders(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()
        data = response.json()

        if "orders" not in data or not data["orders"]:
            await message.answer("⛔ У вас нет заказов.")
            return

        orders_grouped = group_orders(data["orders"])  # Группируем заказы
        await show_orders_list(message, orders_grouped, only_active=True)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о заказах.")

# Обработчик кнопки "🟢 Завершенные заказы"
@router.message(F.text.startswith("🟢 Завершенные заказы"))
async def show_completed_orders(message: types.Message):
    phone_number = user_phone_numbers.get(message.from_user.id)
    if not phone_number:
        await message.answer("⛔ Сначала введите номер телефона клиента.")
        return

    try:
        response = requests.get(SERVER_URL + phone_number)
        response.raise_for_status()
        data = response.json()

        if "orders" not in data or not data["orders"]:
            await message.answer("⛔ У вас нет заказов.")
            return

        orders_grouped = group_orders(data["orders"])  # Группируем заказы
        await show_orders_list(message, orders_grouped, only_completed=True)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("⛔ Ошибка при получении данных о заказах.")


class FeedbackProblemsRequest(StatesGroup):
    waiting_for_problem = State()

@router.message(F.text == "🚨 Сообщить о проблеме")
async def feedback_problems(message: types.Message, state: FSMContext):
    report_problem_text = """
    🔹 <b>Помогите нам стать лучше!</b>  

    Наш бот постоянно развивается, и ваша обратная связь очень важна для нас! 💡  
    Если вы столкнулись с проблемой, нашли ошибку или у вас есть идея, как улучшить бота – сообщите нам об этом.  

    ✍️ <b>Введите сообщение с описанием проблемы и отправьте его в этот чат.</b>  
    Мы внимательно рассмотрим ваш отзыв и постараемся исправить проблему как можно быстрее.  

    <b>Спасибо, что помогаете сделать бота лучше!</b> 🚀
    """

    await message.answer(report_problem_text, parse_mode="HTML" ,reply_markup=back_keyboard )
    await state.set_state(FeedbackProblemsRequest.waiting_for_problem)

@router.message(FeedbackProblemsRequest.waiting_for_problem)
async def process_reply(message: types.Message, state: FSMContext, bot):
    """Отправляем текст всем админам """
    phone_number = user_phone_numbers.get(message.from_user.id)
    name, client_id = get_info(phone_number)
    problem_text = message.text
    problem_message = (
        f"🚨 <b>Новое сообщение о проблеме!</b> 🚨\n\n"
        f"👤 <b>Пользователь:</b> {name}\n"
        f"🆔 <b>ID клиента:</b> {client_id}\n"
        f"📱 <b>Telegram ID:</b> {message.from_user.id}\n\n"
        f"📝 <b>Описание проблемы:</b>\n{problem_text}\n\n"
        f"🔔 <b>Пожалуйста, проверьте и решите проблему как можно скорее.</b>"
    )

    # Отправляем сообщение админу
    await send_to_admins(bot, problem_message)
    success_report_text = """
    ✅ <b>Спасибо за ваш отзыв!</b>  

    Мы получили ваше сообщение и постараемся разобраться с проблемой в ближайшее время.  
    Ваш вклад помогает нам сделать бота ещё лучше! 🚀  

    Если у нас появятся уточняющие вопросы, мы свяжемся с вами.  
    <b>Спасибо, что помогаете нам развиваться!</b> 💡
    """

    await message.answer(success_report_text, parse_mode="HTML", reply_markup=main_kb(message.from_user.id))
    await state.clear()
