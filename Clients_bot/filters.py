from Clients_bot.handlers.auth import load_sessions

import json
from pathlib import Path
from aiogram.types import Message
from aiogram.filters import BaseFilter

# Загрузка списка админов
def load_admins():
    admins_path = Path("data/admins.json")
    if admins_path.exists():
        with open(admins_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("admins", [])
    return []

class IsAuthenticated(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        sessions = load_sessions()
        admins = load_admins()

        # Если пользователь админ, разрешаем доступ
        if user_id in admins:
            return True

        # Если пользователь есть в сессиях, разрешаем доступ
        return str(user_id) in sessions