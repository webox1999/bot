from aiogram.filters import BaseFilter
from aiogram.types import Message
from Clients_bot.handlers.auth import load_sessions

class IsAuthenticated(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = str(message.from_user.id)
        sessions = load_sessions()
        return user_id in sessions
