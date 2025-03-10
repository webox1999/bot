import json
import os
from pathlib import Path
import uuid

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
    with open(ADMINS_FILE, 'r') as f:
        return json.load(f)['admins']

def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump({"admins": admins}, f, indent=4)

def is_admin(user_id):
    return user_id in load_admins()



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
