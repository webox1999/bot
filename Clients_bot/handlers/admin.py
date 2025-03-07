from Clients_bot.handlers.start import *
import datetime
from Clients_bot.utils.admin_utils import load_admins, save_admins, is_admin
from Clients_bot.handlers.auth import load_sessions

# Создаем роутер
router = Router()

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
async def who_online(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    admins = load_admins()
    if not admins:
        return await message.answer("📌 В списке админов никого нет.")

    admins_list = "\n".join([str(a) for a in admins])
    await message.answer(f"📌 Список админов:\n{admins_list}")



# Команда проверки номера телефона (заглушка, пока без БД)
@router.message(Command("check_phone"))
async def check_phone(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ У вас нет прав на выполнение этой команды.")

    try:
        phone_number = message.text.split()[1]
    except IndexError:
        return await message.answer("❌ Использование: /check_phone [номер]")

    # Сохраняем номер пользователя
    cleaned_phone_number = clean_phone_number(phone_number)
    user_phone_numbers[message.from_user.id] = cleaned_phone_number
    await process_phone(message, cleaned_phone_number)


@router.message(Command("users_online"))
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

