from Clients_bot.utils.admin_utils import load_admins

async def send_to_admins(bot, message: str):
    """Отправляет сообщение всем администраторам."""
    admins = load_admins()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, message, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки сообщения админу {admin_id}: {e}")
