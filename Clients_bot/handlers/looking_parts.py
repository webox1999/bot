from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from Clients_bot.utils.search_parts import load_parts_by_id, GOOD_BRANDS, create_parts_menu, cached_menus,PARTS_DETAILS_FILE
from Clients_bot.filters import IsAuthenticated
from Clients_bot.handlers.add_car_by_brand import add_car_by_brand
from Clients_bot.utils.storage import user_phone_numbers, user_cars_ids,user_cars_names
from Clients_bot.handlers.keyboards import unAuth_keyboard, add_info_car, main_kb
from Clients_bot.handlers.start import get_cars_for_delete, get_info, get_car_info
from Clients_bot.handlers.ask_parts import process_part_request
from Clients_bot.utils.helpers import get_parts_details,normalize_article
from Clients_bot.handlers.orders import send_long_message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from Clients_bot.utils.matching_vin import find_modifications_by_vin
from datetime import datetime
import json
router = Router()

# Словарь для сокращения названий категорий
short_names = {
    "Детали подвески и рулевого управления": "Подвеска и рулевое",
    "Приводные ремни, компоненты привода ремня": "Приводные ремни",
    "Амортизаторы, пружины и их компоненты": "Амортизаторы и пружины",
    "Цепи ГРМ и их компоненты": "К-т ГРМ",
    "Ступицы, подшипники ступиц": "Ступицы и подшипники",
    "Опоры двигателя и трансмиссии": "Опоры двигателя",
    "Прокладки, уплотнительные кольца": "Прокладки и кольца",
    "Стартеры, генераторы": "Стартеры и генераторы",
    "Щетки стеклоочистителя": "Дворники",
    "Газовые упоры": "Газовые упоры"
}

# Состояние для ввода названия детали
class SearchPartState(StatesGroup):
    waiting_for_car_choice = State()

@router.message(F.text == "🛠️ Детали для Т/О", IsAuthenticated())
@router.message(Command("parts"))
async def ask_for_car_choice(message: types.Message, state: FSMContext):
    """Проверяем авторизацию у клиента перед запросом детали."""
    await message.answer('⏳ Загружаем подходящие детали...')
    phone_number = user_phone_numbers.get(message.from_user.id)
    sended_from = 'user'
    name, client_id = get_info(phone_number)
    vin = 'NotAllowed'
    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    """Запрашивает у клиента выбор автомобиля перед запросом детали."""
    # ✅ Получаем JSON-список авто клиента
    cars = get_cars_for_delete(phone_number)
    if not cars:
        await state.update_data(car_info="🚗 Авто не указано")
        await message.answer('У вас еще нет автомобилей в гараже. Необходимо добавить авто чтобы продолжить!')
        return await add_car_by_brand(message, vin, client_id, sended_from)  # ✅ Если авто нет, добавляем его через ручной метод

    formatted_cars = []  # Список для кнопок
    car_types = []
    car_mapping = {}  # Словарь для быстрого поиска ID авто
    car_mapping_type = {}

    # ✅ Формируем текст для каждой машины
    for car_id, car_data in cars.items():
        brand = car_data.get("brand", "Неизвестный бренд")
        model = car_data.get("model", "Информация отсутствует")
        year = car_data.get("year", "Год не указан")
        vin = car_data.get("vin", "VIN не указан")
        type = car_data.get("type", "Нет модификации")
        car_id = car_data.get("id", "ID не указан")
        car_text = f"🚗 {brand} {model} {year}| {vin}"
        car_type = f"{type}"
        formatted_cars.append(car_text)
        car_types.append(car_type)
        car_mapping[car_text] = car_id  # Связываем текст с ID авто
        car_mapping_type[car_text] = car_type
        user_cars_names[message.from_user.id] = car_text


    # ✅ Если у пользователя только 1 авто, пропускаем выбор
    if len(formatted_cars) == 1:
        selected_car_text = formatted_cars[0]
        selected_car_id = car_mapping[selected_car_text]
        selected_car_type = car_mapping_type[selected_car_text]
        user_cars_names[message.from_user.id] = selected_car_text
        print(car_mapping)
        await state.update_data(car_info=selected_car_type, car_id=selected_car_id)
        data = await state.get_data()
        modification_id = data.get("car_info", [])
        car_id = data.get("car_id")
        print(car_id)
        user_cars_ids[message.from_user.id] = car_id
        info_data = get_car_info(car_id)
        car_data = info_data.get('company_car')
        if modification_id == '' or modification_id == 'Нет модификации':
            message_text = (
                f"⚠️ *Ой-ой!* Кажется, ваше авто *{car_data.get('auto_maker_name')}*  было добавлено автоматически через VIN-код "
                "и не содержит всех данных для поиска запчастей. 😕\n\n"
                "🔧 *Что делать?*\n"
                "Пожалуйста, дополните недостающую информацию вручную, чтобы мы могли подобрать детали для вашего автомобиля. 🛠\n\n"
                "📌 _Как только всё будет заполнено, поиск станет доступным!_ 🚀"
            )

            await message.answer(message_text, parse_mode=ParseMode.MARKDOWN, reply_markup=add_info_car)
            await state.clear()
            return

        parts = load_parts_by_id(modification_id)
        await state.clear()
        keyboard_parts = await create_category_keyboard(parts)

        return await message.answer("Выберите категорию:", reply_markup=keyboard_parts)
    # ✅ Создаём клавиатуру с авто
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
                     [KeyboardButton(text=car)] for car in formatted_cars  # Создаем строки для каждой машины
                 ] + [
                     [KeyboardButton(text="🔙 Назад")]  # Добавляем кнопку "Назад" в отдельной строке
                 ],
        resize_keyboard=True
    )

    await state.update_data(car_list=car_mapping_type, car_id=car_mapping)
    await state.set_state(SearchPartState.waiting_for_car_choice)
    await message.answer("🚗 Выберите авто для поиска запчастей:", reply_markup=keyboard)



# Обработчик ввода названия машины
@router.message(SearchPartState.waiting_for_car_choice)
async def save_car_choice_search(message: types.Message, state: FSMContext):
    """Сохраняет выбранное авто"""
    user_id = message.from_user.id
    data = await state.get_data()
    car_list = data.get("car_list", [])
    car_info = data.get("car_id", [])
    await state.update_data(car_info=message.text)
    modification_id = car_list.get(message.text)
    car_id = car_info.get(message.text)
    parts = load_parts_by_id(modification_id)
    info_data = get_car_info(car_id)
    car_data = info_data.get('company_car')

    if message.text not in car_list:
        return await message.answer("⚠ Пожалуйста, выберите авто из списка!")
    if modification_id == '' or modification_id == 'Нет модификации':
        message_text = (
            f"⚠️ *Ой-ой!* Кажется, ваше авто *{car_data.get('auto_maker_name')}*  было добавлено автоматически через VIN-код "
            "и не содержит всех данных для поиска запчастей. 😕\n\n"
            "🔧 *Что делать?*\n"
            "Пожалуйста, дополните недостающую информацию вручную, чтобы мы могли подобрать детали для вашего автомобиля. 🛠\n\n"
            "📌 _Как только всё будет заполнено, поиск станет доступным!_ 🚀"
        )
        user_cars_ids[user_id] = car_id
        await message.answer(message_text, parse_mode=ParseMode.MARKDOWN, reply_markup=add_info_car)
        await state.clear()
        return



        # Создаем клавиатуру с категориями

    await state.clear()
    keyboard = await create_category_keyboard(parts)
    await message.answer("Выберите категорию:", reply_markup=keyboard)

# Кеш для хранения данных
parts_cache = {}


# Функция для создания Inline-клавиатуры с категориями
async def create_category_keyboard(parts_list):
    builder = InlineKeyboardBuilder()
    for category_data in parts_list:
        category = category_data["category"]
        short_name = short_names.get(category, category)
        safe_callback_data = short_name.replace(" ", "_")
        parts_cache[safe_callback_data] = category_data["articles"]
        builder.button(text=short_name, callback_data=safe_callback_data)
    builder.adjust(2)
    keyboard = builder.as_markup()

    # Сохраняем меню категорий в кеше
    cached_menus["categories_menu"] = ("Выберите категорию:", keyboard)

    return keyboard



# Функция для обработки выбора категории
@router.callback_query(F.data.in_(parts_cache.keys()))  # 🔥 Теперь ловит ТОЛЬКО категории
async def handle_category_selection(callback: types.CallbackQuery):
    try:
        callback_data = callback.data
        print(f"Received callback_data (CATEGORY): {callback_data}")

        if callback_data in parts_cache:
            articles = parts_cache[callback_data]
            menu_text, keyboard = await create_parts_menu(articles)

            # Кешируем меню запчастей с использованием user_id
            cached_menus[callback.from_user.id] = (menu_text, keyboard)

            keyboard.inline_keyboard.append([types.InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_categories")])

            await callback.message.edit_text(menu_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

        else:
            await callback.message.answer("❌ Категория не найдена в кеше.")

    except Exception as e:
        print(f"Ошибка в handle_category_selection: {e}")
        await callback.message.answer("Произошла ошибка при обработке запроса.")

    finally:
        await callback.answer()




MAX_ANALOGS = 10  # Максимальное количество аналогов
MAX_OE_NUMBERS = 10  # Максимальное количество оригинальных номеров

@router.callback_query(F.data.startswith("show_"))
async def show_full_details(callback: types.CallbackQuery):
    """Редактирует сообщение, показывая детали запчасти."""
    try:
        article = callback.data.replace("show_", "")  # Убираем "show_"
        print(f"Received callback_data (DETAILS): {article}")  # Логируем

        part = get_parts_details(article)

        if not part:
            await callback.message.answer("❌ Артикул не найден в базе.")
            return

        name = part.get("name", "Неизвестная запчасть")
        specs = part.get("specifications", {})
        specs_text = "\n".join([f"🔹 {key}: {value}" for key, value in specs.items()]) if specs else "🚫 Нет данных"

        # Ограничиваем количество оригинальных номеров
        oe_numbers = part.get("oe_numbers", [])[:MAX_OE_NUMBERS]
        oe_text = "\n".join([f"🔸 {item['brand']}: {item['article']}" for item in oe_numbers]) if oe_numbers else "🚫 Нет данных"
        if len(part.get("oe_numbers", [])) > MAX_OE_NUMBERS:
            oe_text += f"\n... и ещё {len(part['oe_numbers']) - MAX_OE_NUMBERS} оригинальных номеров"

        # Ограничиваем количество аналогов
        analogs = part.get("analogs", [])
        filtered_analogs = [f"✅ {item['brand']}: {item['article']}" for item in analogs if item["brand"] in GOOD_BRANDS][:MAX_ANALOGS]
        analogs_text = "\n".join(filtered_analogs) if filtered_analogs else "🚫 Нет качественных аналогов"
        if len([item for item in analogs if item["brand"] in GOOD_BRANDS]) > MAX_ANALOGS:
            analogs_text += f"\n... и ещё {len([item for item in analogs if item['brand'] in GOOD_BRANDS]) - MAX_ANALOGS} аналогов"

        image_url = part.get("images", ["https://lynxauto.info/image/trumb/400x300/no_image.jpg"])[0]

        message_text = (
            f"🔹 <b>{name}</b>\n\n"
            f"⚙ <b>Характеристики:</b>\n{specs_text}\n"
            f"🏷️ <b>Узнать цену:</b> /price_{normalize_article(article)}\n\n"
            f"🔍 <b>Оригинальные номера:</b>\n{oe_text}\n\n"
            f"🔄 <b>Аналоги:</b> \n{analogs_text}\n"
        )

        # Добавляем кнопку "⬅ Назад" для возврата к списку деталей
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="⬅ Назад", callback_data="go_back_to_parts")
        keyboard = keyboard.as_markup()

        await callback.message.edit_media(
            media=types.InputMediaPhoto(media=image_url, caption=message_text, parse_mode="HTML"),
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Ошибка в show_full_details: {e}")
        await callback.message.answer("❌ Ошибка при загрузке полной информации.")

    finally:
        await callback.answer()


@router.callback_query(F.data == "go_back_to_parts")
async def go_back_to_menu(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id

        if user_id in cached_menus:
            menu_text, keyboard = cached_menus[user_id]

            if callback.message.photo:
                await callback.message.delete()
                await callback.message.answer(menu_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            else:
                await callback.message.edit_text(menu_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

        else:
            await callback.message.answer("❌ Меню запчастей не найдено. Попробуйте снова.")

    except Exception as e:
        print(f"Ошибка в go_back_to_menu: {e}")
        await callback.message.answer("❌ Ошибка при возврате в меню запчастей.")

    finally:
        await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def go_back_to_categories(callback: types.CallbackQuery):
    """Возвращает список категорий."""
    try:
        if "categories_menu" in cached_menus:
            menu_text, keyboard = cached_menus["categories_menu"]

            if callback.message.photo:  # ✅ Если сообщение содержит фото – удаляем его
                await callback.message.delete()
                await callback.message.answer(menu_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            else:
                await callback.message.edit_text(menu_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

        else:
            await callback.message.answer("❌ Меню категорий не найдено. Попробуйте снова.")



    except Exception as e:
        print(f"Ошибка в go_back_to_categories: {e}")
        await callback.message.answer("❌ Ошибка при возврате в меню категорий.")

    finally:
        await callback.answer()


@router.message(F.text == "Добавить информацию", IsAuthenticated())
async def add_information_car(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone_number = user_phone_numbers.get(message.from_user.id)
    car_id = user_cars_ids.get(message.from_user.id)
    await message.answer("Начало редактирования автомобиля...", reply_markup=main_kb(user_id))
    if not phone_number:
        await message.answer("❌ Вы не авторизованы! Пожалуйста, отправьте свой контакт для авторизации.", reply_markup=unAuth_keyboard)
        return
    car_data = get_car_info(car_id)
    name, client_id = get_info(phone_number)
    data = car_data.get('company_car')
    vin = data.get('vin')
    await add_car_by_brand(message, vin, client_id, "change", car_id)


@router.message(F.text.startswith("/show_"))
async def showing_details(message: types.Message, state: FSMContext):
    """Запрашиваем у администратора ответ на запрос."""
    arictle = message.text.split("_")[1]  # Извлекаем ID запроса
    print(arictle)
    part = get_parts_details(arictle)
    print(part)
    name = part.get("name", "Неизвестная запчасть")
    specs = part.get("specifications", {})
    specs_text = "\n".join([f"🔹 {key}: {value}" for key, value in specs.items()]) if specs else "🚫 Нет данных"

    # Ограничиваем количество оригинальных номеров
    oe_numbers = part.get("oe_numbers", [])[:MAX_OE_NUMBERS]
    oe_text = "\n".join(
        [f"🔸 {item['brand']}: {item['article']}" for item in oe_numbers]) if oe_numbers else "🚫 Нет данных"
    if len(part.get("oe_numbers", [])) > MAX_OE_NUMBERS:
        oe_text += f"\n... и ещё {len(part['oe_numbers']) - MAX_OE_NUMBERS} оригинальных номеров"

    # Ограничиваем количество аналогов
    analogs = part.get("analogs", [])
    filtered_analogs = [f"✅ {item['brand']}: {item['article']}" for item in analogs if item["brand"] in GOOD_BRANDS][
                       :MAX_ANALOGS]
    analogs_text = "\n".join(filtered_analogs) if filtered_analogs else "🚫 Нет качественных аналогов"
    if len([item for item in analogs if item["brand"] in GOOD_BRANDS]) > MAX_ANALOGS:
        analogs_text += f"\n... и ещё {len([item for item in analogs if item['brand'] in GOOD_BRANDS]) - MAX_ANALOGS} аналогов"

    image_url = part.get("images", ["https://lynxauto.info/image/trumb/400x300/no_image.jpg"])[0]
    if not specs_text:
        specs_text = 'Нет информации о детали'

    message_text = (
            f"🔹 <b>{name} {arictle}</b>\n\n"
            f"⚙ <b>Характеристики:</b>\n{specs_text}\n\n"
            f"🔍 <b>Оригинальные номера:</b>\n{oe_text}\n\n"
            f"🔄 <b>Аналоги:</b>\n{analogs_text}"
        )

    await message.answer_photo(photo=image_url, caption=message_text, parse_mode="HTML")


@router.message(F.text.startswith("/price_"))
async def showing_details(message: types.Message, state: FSMContext, bot):
    """Обрабатывает нажатие кнопки 'Узнать цену' и вызывает process_part_request"""
    arictle = message.text.split("_")[1]  # Извлекаем ID запроса
    await message.answer(f'Уточнение цены: {arictle}')
    # Вызываем обработчик process_part_request, передавая сообщение
    await process_part_request(message, state, bot, arictle)

@router.message(F.text.startswith("/vin_"))
async def get_car_by_vin_info(message: types.Message, state: FSMContext, bot):
    """Обрабатывает нажатие кнопки 'Узнать цену' и вызывает process_part_request"""
    vin = message.text.split("_")[1]  # Извлекаем ID запроса
    await message.answer(f'Обработка vin: {vin}')
    #find_modifications_by_vin(vin)
    matches = find_modifications_by_vin(vin)

    for m in matches:
        print(f"[{m['score']}★] {m['modification']} (ID: {m['modification_id']}) — Причины: {', '.join(m['reasons'])}")


