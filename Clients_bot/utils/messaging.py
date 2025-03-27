from Clients_bot.utils.admin_utils import load_admins, get_admin_name
from Clients_bot.utils.auth import load_sessions
from Clients_bot.config import CODES,API_URL
from typing import Optional
import random
import json
import os
from datetime import datetime
import aiohttp

def load_codes():
    """Загружает список запросов на детали."""
    if not os.path.exists(CODES):
        return []
    try:
        with open(CODES, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_codes(codes):
    """Сохраняет список кодов в файл."""
    with open(CODES, "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=4)


async def send_to_admins(bot, message: str):
    """Отправляет сообщение всем администраторам."""
    admins = load_admins()
    for admin in admins:
        try:
            await bot.send_message(admin["id"], message, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки сообщения админу {admin['id']}: {e}")


async def send_to_all(bot, admin_id, message: str, percent: Optional[str] = None, validity: Optional[str] = None ):
    users = load_sessions()
    code_history = load_codes()
    admin_name = get_admin_name(admin_id)
    for user_id, user_data in users.items():
        name = user_data.get("name")
        client_id = user_data.get("client_id")
        phone = user_data.get("phone")
        text = (f'Уважаемый {name}!\n\n {message}\n\n')
        if percent:
            code = generate_unique_code(code_history)
            text += (f'Ваш скидочный купон на {percent}% №: {code}\n'
                     f'При оформлении заказа, скажите его продавцу.'
                     )

            new_code = {
                "name": name,
                "user_id": user_id,
                "client_id": client_id,
                "phone_number": phone,
                "admin": admin_name,
                "sale_code": code,
                "percent": percent,
                "validity": int(validity),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "used_date": None,
                "status": "active"
            }
            await add_code_in_profile(client_id, code)
            code_history.append(new_code)
            save_codes(code_history)

            try:
                await bot.send_message(user_id, text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки сообщения  {user_id}: {e}")
        else:
            try:
                await bot.send_message(user_id, text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки сообщения  {user_id}: {e}")

async def add_code_in_profile(client_id: str, code: str):
    """Добавляет код в профиль клиента через API"""
    url = f"{API_URL}/add_code?client_id={client_id}&code={code}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data.get("status") == "ok":
                    data = await response.json()
                    return data  # Возвращаем данные ответа
                else:
                    print(f"Ошибка API: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Ошибка сети: {e}")
        return None

async def delete_code_from_profile(client_id: str, code: str):
    """Добавляет код в профиль клиента через API"""
   # url = f"{API_URL}/delete_code?client_id={client_id}&code={code}"
    url = f"http://127.0.0.1:8050/delete_code?client_id={client_id}&code={code}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data.get("status") == "ok":
                    data = await response.json()
                    return data  # Возвращаем данные ответа
                else:
                    print(f"Ошибка API: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Ошибка сети: {e}")
        return None



def generate_unique_code(code_history):
    """Генерирует уникальный 6-значный код, который отсутствует в базе"""
    while True:
        code = str(random.randint(100000, 999999))  # Генерируем 6-значный код
        if not any(entry["sale_code"] == code for entry in code_history):  # Проверяем уникальность
            return code