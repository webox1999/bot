from aiogram import types, F
from Clients_bot.handlers.start import router
from Clients_bot.handlers.keyboards import kupon_kb
from Clients_bot.utils.messaging import load_codes, save_codes, delete_code_from_profile
from datetime import datetime, timedelta
from Clients_bot.utils.storage import user_phone_numbers
from aiogram.filters import Command
import asyncio


#Обработчик для кнопки бонусов
@router.message(F.text == "ℹ Информация и бонусы")
async def show_bonus_info(message: types.Message):
    text = (
        "🚗 <b>За Рулем Бот – ваш личный помощник в мире автозапчастей!</b> 🔧\n\n"
        "🤖 <b>Что умеет бот?</b>\n\n"
        "📌 <b>Гараж</b> – добавьте свои автомобили, и бот автоматически подберет запчасти для ТО "
        "и ускорит поиск нужных деталей! 🏎️\n"
        "📌 <b>Заказы</b> – следите за статусами ваших заказов в реальном времени и просматривайте историю покупок. 📦\n"
        "📌 <b>История платежей</b> – контролируйте свои расходы, бонусные начисления и доступные скидки. 💳\n"
        "📌 <b>Подобрать запчасть</b> – отправьте запрос администратору, чтобы уточнить наличие, цену или аналоги детали. 🚀\n"
        "📌 <b>Поиск запчастей для ТО</b> – бот подберет все необходимое для технического обслуживания вашего автомобиля "
        "на основе данных из вашего <b>Гаража</b>. 🛠️\n"
        "📌 <b>Мои запросы</b> – храните историю всех ваших обращений и следите за активными подборками. 📨\n"
        "📌 <b>Автоматические уведомления</b> – бот мгновенно оповестит вас об изменении статуса заказа: "
        "от оформления до выдачи. 🔔\n"
        "📌 <b>Сообщить о проблеме</b> – если что-то не работает или есть предложения по улучшению, "
        "напишите нам прямо через бота! ❗\n\n"
        "✨ <b>Как работает бонусная система?</b> ✨\n\n"
        "💰 <b>Копите бонусы при каждой покупке свыше 1000₽!</b>\n"
        "🎁 <b>Используйте бонусы для оплаты товаров в магазине.</b>\n\n"
        "🔹 Бонусы начисляются <b>автоматически</b>.\n"
        "🔹 Оплатить покупку можно, если накоплено <b>200 бонусов и более</b>.\n"
        "🔹 <b>1 бонус = 1 рубль скидки.</b>\n\n"
        "🛒 <b>Покупайте, накапливайте и экономьте вместе с нами!</b> 🚀"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🎟 Купоны")
async def show_coupon(message: types.Message):
    await message.answer('Выберите категорию:', reply_markup=kupon_kb)







async def update_code_status(data_code):
    """ Проверяет и обновляет статусы кодов в JSON """
    print(f'Фунция обновления вызывается: {data_code}')
    now = datetime.now()
    updated = False

    for request in data_code:
        client_id = request.get("client_id")  # Используем get(), чтобы избежать ошибок
        code = request.get("sale_code")
        print(f'Выводим что получили : {client_id} , {code}')
        if not client_id or not code:
            continue  # Если данных нет, пропускаем этот код

        status = request.get("status")

        if status == "active":
            code_date = datetime.strptime(request["date"], "%Y-%m-%d %H:%M:%S")
            validity_days = int(request.get("validity", 0))  # Преобразуем в число
            expiry_date = code_date + timedelta(days=validity_days)

            if now > expiry_date:
                request["status"] = "expired"
                await delete_code_from_profile(client_id, code)  # Удаляем купон у клиента
                print(f'Купон {code} удален из профиля для {client_id}')
                updated = True  # Фиксируем, что данные изменились



    if updated:
        save_codes(data_code)


async def get_codes(search_value, status, search_by="phone_number"):
    """ Возвращает список кодов по номеру телефона или client_id и статусу """
    data_code = load_codes()
    await update_code_status(data_code)  # Проверяем и обновляем просроченные коды

    # Фильтруем коды в зависимости от типа поиска
    filtered_codes = [req for req in data_code if req.get(search_by) == search_value and req["status"] in status]

    return filtered_codes

async def auto_check_codes():
    while True:
        data_code = load_codes()
        await update_code_status(data_code)
        print('Автоматическое обновление купонов запущено...')
        await asyncio.sleep(30)


@router.message(F.text == "✅ Действующие")
async def show_active_codes(message: types.Message):
    """ Выводит список активных кодов для пользователя """
    phone_number = user_phone_numbers.get(message.from_user.id)  # Получаем номер телефона пользователя
    active_codes = await get_codes(phone_number, status=["active"])

    if not active_codes:
        return await message.answer("✅ У вас нет активных купонов.")

    text = "🎟 **Ваши активные купоны:**\n\n"
    for code in active_codes:
        text += (
            f"🔹 Код: `{code['sale_code']}`\n"
            f"📅 Дата создания: {code['date']}\n"
            f"💰 Скидка: {code['percent']}%\n"
            f"📆 Действует до: {datetime.strptime(code['date'], '%Y-%m-%d %H:%M:%S') + timedelta(days=int(code['validity']))}\n"
            f"———————————————\n"
        )

    await message.answer(text)


@router.message(F.text == "🗄 Архив купонов")
async def show_archive_codes(message: types.Message):
    """ Выводит список использованных и просроченных купонов """
    phone_number = user_phone_numbers.get(message.from_user.id)  # Получаем номер телефона пользователя
    archive_codes = await get_codes(phone_number, status=["used", "expired"])

    if not archive_codes:
        return await message.answer("🗄 У вас нет архивных купонов.")

    text = "📁 **Архив купонов:**\n\n"
    for code in archive_codes:
        used_date = "Не использовался" if code["used_date"] == None else code["used_date"]
        status_text = "🟠 **Просрочен**" if code["status"] == "expired" else "✅ **Использован**"
        text += (
            f"🔹 Код: `{code['sale_code']}`\n"
            f"📅 Дата создания: {code['date']}\n"
            f"📅 Дата использования: {used_date}\n"
            f"💰 Скидка: {code['percent']}%\n"
            f"📆 Действовал до: {datetime.strptime(code['date'], '%Y-%m-%d %H:%M:%S') + timedelta(days=int(code['validity']))}\n"
            f"📌 Статус: {status_text}\n"
            f"———————————————\n"
        )

    await message.answer(text)

