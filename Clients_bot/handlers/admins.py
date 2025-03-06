import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from Clients_bot.config import BOT_TOKEN
import os

# Загрузка токена бота
TOKEN = BOT_TOKEN


# Файл для хранения админов
ADMINS_FILE = "admins.json"

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
@dp.message_handler(commands=["add_admin"])
async def add_admin(message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ У вас нет прав на выполнение этой команды.")

    try:
        new_admin_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.reply("❌ Использование: /add_admin [TG ID]")

    admins = load_admins()
    if new_admin_id in admins:
        return await message.reply("✅ Этот пользователь уже является админом.")

    admins.append(new_admin_id)
    save_admins(admins)
    await message.reply(f"✅ Пользователь {new_admin_id} добавлен в админы.")


# Команда для удаления админа
@dp.message_handler(commands=["remove_admin"])
async def remove_admin(message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ У вас нет прав на выполнение этой команды.")

    try:
        admin_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.reply("❌ Использование: /remove_admin [TG ID]")

    admins = load_admins()
    if admin_id not in admins:
        return await message.reply("❌ Этот пользователь не является админом.")

    admins.remove(admin_id)
    save_admins(admins)
    await message.reply(f"✅ Пользователь {admin_id} удалён из админов.")


# Команда для просмотра списка админов
@dp.message_handler(commands=["who_online"])
async def who_online(message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ У вас нет прав на выполнение этой команды.")

    admins = load_admins()
    if not admins:
        return await message.reply("📌 В списке админов никого нет.")

    admins_list = "\n".join([str(a) for a in admins])
    await message.reply(f"📌 Список админов:\n{admins_list}")


# Команда проверки номера телефона (заглушка, пока без БД)
@dp.message_handler(commands=["check_phone"])
async def check_phone(message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("❌ У вас нет прав на выполнение этой команды.")

    try:
        phone_number = message.text.split()[1]
    except IndexError:
        return await message.reply("❌ Использование: /check_phone [номер]")

    # Здесь можно добавить логику проверки номера телефона в БД
    await message.reply(f"🔍 Проверка номера: {phone_number}\n(Функция пока не реализована)")
