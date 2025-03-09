# utils/storage.py
import json
import os

user_phone_numbers = {}  # Глобальный словарь для хранения номеров телефонов

PART_REQUESTS_FILE = "data/part_requests.json"

def load_part_requests():
    """Загружает список запросов на детали."""
    if not os.path.exists(PART_REQUESTS_FILE):
        return []
    try:
        with open(PART_REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_part_requests(requests):
    """Сохраняет список запросов на детали."""
    with open(PART_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=4)