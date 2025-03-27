import json
import os
import datetime
from pathlib import Path
import random
from Clients_bot.utils.storage import user_phone_numbers

# # Файл для хранения сессий пользователей
# SESSIONS_FILE = "Clients_bot/data/sessions.json"
# SESSIONS_CHECKIN = Path("Clients_bot/data/sessions.json")
# DATA_PATH = "Clients_bot/data/new_users.json"
# USERS_FILE = Path("Clients_bot/data/proccessing_users.json")

# Файл для хранения сессий пользователей
SESSIONS_FILE = "data/sessions.json"
SESSIONS_CHECKIN = Path("data/sessions.json")
DATA_PATH = "data/new_users.json"
USERS_FILE = Path("data/proccessing_users.json")

# Проверяем, существует ли файл, если нет – создаем
if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "w") as f:
        json.dump({"sessions": {}}, f, indent=4)


def load_sessions():
    """Загружает текущие сессии пользователей, автоматически создаёт файл при ошибке"""
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:  # Добавили encoding="utf-8"
            data = json.load(f)
            return data.get("sessions", {})  # Если "sessions" нет, возвращаем пустой словарь
    except (json.JSONDecodeError, FileNotFoundError):
        print("⚠️ Ошибка загрузки JSON. Создаю новый файл.")
        save_sessions({})
        return {}


async def update_last_active(user_id):
    """Обновляет дату последней активности пользователя, если у него есть все нужные данные"""
    sessions = load_sessions()

    # Если пользователь уже есть в сессиях, просто обновляем `last_active`
    if str(user_id) in sessions:
        sessions[str(user_id)]["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_sessions(sessions)
        return

    # Проверяем, есть ли все важные данные
    user_data = sessions.get(str(user_id), {})
    phone_number = user_data.get("phone")
    client_id = user_data.get("client_id")
    name = user_data.get("name")

    if not phone_number or not client_id or not name:
        return  # ❌ Не добавляем пользователя в `sessions.json`, если данных нет

    # Если все данные есть — добавляем запись в `sessions.json`
    sessions[str(user_id)]["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_sessions(sessions)

def save_sessions(sessions):
    """Сохраняет сессии пользователей с нормальной кодировкой"""
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"sessions": sessions}, f, indent=4, ensure_ascii=False)


def is_authorized(user_id):
    """Проверяет, авторизован ли пользователь"""
    sessions = load_sessions()
    return str(user_id) in sessions

# Путь к файлу с данными пользователей


def bind_phone_to_user(telegram_id: int, phone_number: str) -> bool:
    """Привязывает номер телефона к telegram_id, удаляя старую привязку."""
    if not USERS_FILE.exists():
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)

    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)

    # Удаляем старую привязку для этого номера
    unbind_phone(phone_number)

    # Привязываем номер к новому telegram_id
    users_data[str(telegram_id)] = phone_number

    # Сохраняем обновленные данные
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

    return True

def is_phone_bound(telegram_id: int, phone_number: str) -> bool:
    """Проверяет, привязан ли номер к другому аккаунту."""
    if not USERS_FILE.exists():
        return False

    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)

    # Проверяем, привязан ли номер к другому пользователю
    for user_id, user_phone in users_data.items():
        if user_phone == phone_number and user_id != str(telegram_id):
            return True

    return False

def is_user_bound(telegram_id: int) -> bool:
    """Проверяет, привязан ли telegram_id к какому-либо номеру."""
    if not USERS_FILE.exists():
        return False

    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)

    return str(telegram_id) in users_data

def get_phone_by_telegram_id(telegram_id: int) -> str:
    """Возвращает номер телефона, привязанный к telegram_id."""
    if not USERS_FILE.exists():
        return None

    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)

    return users_data.get(str(telegram_id))

def change_phone_number(telegram_id, new_phone_number):
    if not USERS_FILE.exists():
        return False

    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)

    # Проверяем, привязан ли новый номер к другому пользователю
    for user_id, user_phone in users_data.items():
        if user_phone == new_phone_number and user_id != str(telegram_id):
            return False

    # Удаляем старый номер телефона, если он был привязан к текущему пользователю
    old_phone_number = users_data.get(str(telegram_id))
    if old_phone_number:
        unbind_phone(old_phone_number)

    # Меняем номер телефона для текущего пользователя
    users_data[str(telegram_id)] = new_phone_number

    # Сохраняем обновленные данные
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

    return True

def unbind_phone(phone_number: str):
    """Удаляет привязку для указанного номера телефона."""
    if not USERS_FILE.exists():
        return

    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)

    # Удаляем все записи, где номер телефона совпадает
    users_data = {user_id: user_phone for user_id, user_phone in users_data.items() if user_phone != phone_number}
    # Сохраняем обновленные данные
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

def generate_verification_code() -> str:
    """Генерирует случайный 6-значный код."""
    return str(random.randint(100000, 999999))

async def send_verification_code(bot, telegram_id: int, code: str):
    """Отправляет код подтверждения на указанный telegram_id."""

    await bot.send_message(
        chat_id=telegram_id,
        text=f"🔐 Код для смены номера: {code}"#,
       # reply_markup=approved_keyboard
    )

def delete_phone_from_db(user_id):
    # Удаляем номер телефона, если он есть в user_phone_numbers
    user_id = int(user_id)
    if user_id in user_phone_numbers:
        removed_phone = user_phone_numbers.pop(user_id)
        print(f"Номер {removed_phone} удален для user_id {user_id}")

def auto_check_in():
    """Загружает user_id и номера телефонов из файла sessions.json в глобальную переменную user_phone_numbers."""

    # Проверяем, существует ли файл
    if not SESSIONS_CHECKIN.exists():
        print(f"Файл {SESSIONS_CHECKIN} не найден.")
        return

    # Читаем данные из файла
    with open(SESSIONS_CHECKIN, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Извлекаем данные о сессиях
    sessions = data.get("sessions", {})

    # Проходимся по всем пользователям и добавляем их user_id и номер телефона в user_phone_numbers
    for user_id, user_data in sessions.items():
        phone_number = user_data.get("phone")
        if phone_number:
            user_phone_numbers[int(user_id)] = phone_number  # Преобразуем user_id в число

    print(f"Данные успешно загружены: {user_phone_numbers}")

auto_check_in()