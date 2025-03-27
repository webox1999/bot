# utils/helpers.py
from Clients_bot.utils.storage import load_part_requests,save_part_requests
from Clients_bot.config import PARTS_DETAILS_FILE, PARTS_CACHE_FILE
from datetime import datetime, timedelta
import json
import re
import os

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


def normalize_article(article):
    """Нормализует артикул: убирает '-', пробелы и приводит к верхнему регистру."""
    return re.sub(r'[-\s]', '', article).upper()


def load_parts_database():
    """Загружает базу данных из кеша или пересоздаёт его при необходимости."""
    if os.path.exists(PARTS_CACHE_FILE):
        # Если кеш уже есть — загружаем его
        with open(PARTS_CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    # Если кеша нет — создаем его
    with open(PARTS_DETAILS_FILE, "r", encoding="utf-8") as file:
        parts_data = json.load(file)

    # Создаём словарь {нормализованный_артикул: данные_о_детали}
    parts_cache = {normalize_article(item["_id"]): item for item in parts_data}

    # Сохраняем кеш в файл
    with open(PARTS_CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(parts_cache, file, ensure_ascii=False, indent=4)

    return parts_cache


# Глобальный кеш (загружается 1 раз при запуске)
PARTS_CACHE = load_parts_database()


def get_parts_details(article):
    """Быстрый поиск артикула в кеше (O(1))"""
    article_norm = normalize_article(article)  # Нормализуем ввод пользователя
    return PARTS_CACHE.get(article_norm, 'Артикул не найден в базе')

