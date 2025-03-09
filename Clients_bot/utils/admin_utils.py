import json
import os
from pathlib import Path
import uuid

REQUESTS_FILE = Path("data/change_phone_request.json")
ADMINS_FILE = 'data/admins.json'
clients_file = "data/sessions.json"
# Проверяем, существует ли файл, если нет — создаем
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w') as f:
        json.dump({"admins": []}, f)



def init_requests_file():
    """Инициализирует файл для хранения запросов."""
    if not REQUESTS_FILE.exists():
        REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REQUESTS_FILE, "w") as f:
            json.dump([], f)

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
    with open(REQUESTS_FILE, "r") as f:
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

    with open(REQUESTS_FILE, "w") as f:
        json.dump(requests, f, indent=4)

    return request_id

def get_change_requests(status: str = None):
    """Возвращает запросы по статусу."""
    with open(REQUESTS_FILE, "r") as f:
        requests = json.load(f)

    if status:
        return [req for req in requests if req["status"] == status]
    return requests

def update_change_request(request_id: str, status: str):
    """Обновляет статус запроса."""
    with open(REQUESTS_FILE, "r") as f:
        requests = json.load(f)

    for req in requests:
        if req["id"] == request_id:
            req["status"] = status
            break

    with open(REQUESTS_FILE, "w") as f:
        json.dump(requests, f, indent=4)

