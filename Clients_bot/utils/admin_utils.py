import json
import os
from pathlib import Path
import uuid

# REQUESTS_FILE = Path("Clients_bot/data/change_phone_request.json")
# ADMINS_FILE = 'Clients_bot/data/admins.json'
# clients_file = "Clients_bot/data/sessions.json"
# new_users = Path('Clients_bot/data/new_users.json')

REQUESTS_FILE = Path("data/change_phone_request.json")
ADMINS_FILE = 'data/admins.json'
clients_file = "data/sessions.json"
new_users = Path('data/new_users.json')

# Проверяем, существует ли файл, если нет — создаем
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w') as f:
        json.dump({"admins": []}, f)



def init_requests_file():
    """Инициализирует файл для хранения запросов."""
    if not REQUESTS_FILE.exists():
        REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f,ensure_ascii=False)

init_requests_file()


def load_admins():
    """ Загружает список админов из файла """
    with open(ADMINS_FILE, 'r', encoding="utf-8") as f:
        data = json.load(f)
        admins = data.get("admins", [])

        # Проверяем старую структуру (список ID) и обновляем её
        if admins and isinstance(admins[0], int):
            admins = [{"id": admin, "name": "Неизвестный"} for admin in admins]
            save_admins(admins)  # Сразу обновляем JSON

        return admins  # Теперь всегда возвращает список словарей

def save_admins(admins):
    """ Сохраняет список админов в файл """
    with open(ADMINS_FILE, 'w', encoding="utf-8") as f:
        json.dump({"admins": admins}, f, indent=4, ensure_ascii=False)

def is_admin(user_id):
    """ Проверяет, является ли пользователь администратором """
    admins = load_admins()
    return any(admin["id"] == user_id for admin in admins)  # Работает с новой структурой

def get_admin_name(user_id):
    """ Получает имя админа по его ID """
    admins = load_admins()
    admin = next((admin for admin in admins if admin["id"] == user_id), None)
    return admin["name"] if admin else None



def create_change_request(client_id: int, current_phone: str, new_phone: str, name: str):
    """Создает запрос на смену номера."""
    with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
        requests = json.load(f)

    request_id = str(uuid.uuid4())[:8]  # Генерируем уникальный ID запроса
    new_request = {
        "id": request_id,
        "client_id": client_id,
        "name": name,
        "current_phone": current_phone,
        "new_phone": new_phone,
        "status": "active"
    }

    requests.append(new_request)

    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=4, ensure_ascii=False)

    return request_id

def get_change_requests(status: str = None):
    """Возвращает запросы по статусу."""
    with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
        requests = json.load(f)

    if status:
        return [req for req in requests if req["status"] == status]
    return requests

def get_client_id_by_request_id( request_id):
    """Возвращает client_id для запроса с указанным request_id."""
    with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
        requests = json.load(f)
    for req in requests:
        if req["id"] == request_id:
            return req["client_id"]
    return None  # Если запрос с таким id не найден

def update_change_request(request_id: str, status: str):
    """Обновляет статус запроса."""
    with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
        requests = json.load(f)

    for req in requests:
        if req["id"] == request_id:
            req["status"] = status
            break

    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=4, ensure_ascii=False)

def get_new_users():
    """Получаем список новых пользователей."""
    # Убедимся, что файл существует
    if not Path(new_users).exists():
        print(f"Файл {new_users} не найден.")
        return []

    try:
        # Чтение данных из файла
        with open(new_users, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Извлекаем список пользователей из ключа "users"
        users = data.get("users", [])

        # Проверка, что данные — это список
        if not isinstance(users, list):
            print(f"Ошибка: данные в файле {new_users} не являются списком.")
            return []

        # Фильтруем, оставляя только словари
        filtered_users = [user for user in users if isinstance(user, dict)]

        if len(filtered_users) != len(users):
            print(f"Предупреждение: в файле {new_users} найдены некорректные данные (не словари).")

        return filtered_users

    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении файла {new_users}: {e}")
        return []
    except Exception as e:
        print(f"Неизвестная ошибка при чтении файла {new_users}: {e}")
        return []
