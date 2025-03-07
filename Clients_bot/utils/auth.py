import json
import os
import datetime


# Файл для хранения сессий пользователей
SESSIONS_FILE = "data/sessions.json"
DATA_PATH = "data/new_users.json"
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