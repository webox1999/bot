# utils/helpers.py
from Clients_bot.utils.storage import load_part_requests,save_part_requests
from datetime import datetime, timedelta

def clean_phone_number(phone_number: str) -> str:
    """Очищает номер телефона, оставляя только цифры."""
    return "".join(filter(str.isdigit, phone_number))

def get_field_value(data: dict, key: str, default: str = "Информация отсутствует") -> str:
    """
    Возвращает значение из словаря или значение по умолчанию, если поле пустое или содержит только пробелы.
    :param data: Словарь с данными.
    :param key: Ключ для поиска.
    :param default: Значение по умолчанию.
    :return: Значение поля или default.
    """
    value = data.get(key, default)
    return value if value and value.strip() else default  # Проверяем, что строка не пустая и не состоит из пробелов

#Обрабатываем кол-во символов в сообщения

def split_text(text: str, max_length: int = 4000) -> list[str]:
    """
    Разделяет текст на части, не превышающие max_length символов.
    :param text: Исходный текст.
    :param max_length: Максимальная длина части (по умолчанию 4096).
    :return: Список частей текста.
    """
    parts = []
    while len(text) > max_length:
        # Находим последний перенос строки или пробел перед max_length
        split_index = text.rfind("\n", 0, max_length)
        if split_index == -1:
            # Если перенос строки не найден, делим по пробелу
            split_index = text.rfind(" ", 0, max_length)
        if split_index == -1:
            # Если пробел не найден, делим по max_length
            split_index = max_length

        # Добавляем часть текста в список
        parts.append(text[:split_index].strip())
        # Убираем добавленную часть из исходного текста
        text = text[split_index:].strip()

    # Добавляем оставшийся текст
    if text:
        parts.append(text)
    return parts

# Функция для добавления истории переписки в запрос
def add_message_to_request(request_id, role, message):
    """Добавляет сообщение в историю переписки"""
    requests = load_part_requests()
    request = next((req for req in requests if req["request_id"] == request_id), None)

    if not request:
        return False  # Запрос не найден

    # Если истории еще нет, создаем пустой список
    if "history" not in request:
        request["history"] = []

    # Добавляем новое сообщение в историю

    if role == 'admin':
        request["admin_answer"] = message  # Последний ответ админа (не история)
        request["history"].append({"role": role, "message": message})
        # Сохраняем обновленный список запросов
        save_part_requests(requests)
        return True
    elif role == 'client':
        request["answer"] = message  # Последний ответ клиента (не история)
        request["history"].append({"role": role, "message": message})
        # Сохраняем обновленный список запросов
        save_part_requests(requests)
        return True
    else:
        print(f'История не записана')

# Функция для получения даты 180 месяц назад
def get_default_dates():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    return start_date, end_date


