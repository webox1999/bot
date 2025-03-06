from Clients_bot.handlers.start import *
import json
import os

# Создаем роутер
router = Router()

# Файл для хранения админов
ADMINS_FILE = "data/admins.json"

# Проверяем, существует ли файл, если нет - создаем
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w") as f:
        json.dump({"admins": []}, f)


# Функция для загрузки админов из JSON
def load_admins():
    with open(ADMINS_FILE, "r") as f:
        return json.load(f)["admins"]


# Функция для сохранения админов в JSON
def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump({"admins": admins}, f, indent=4)


# Функция проверки, является ли пользователь админом
def is_admin(user_id):
    return user_id in load_admins()


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


