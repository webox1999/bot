# utils/helpers.py

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

# Функция для подсчета активных и завершенных заказов
