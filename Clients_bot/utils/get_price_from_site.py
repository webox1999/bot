import requests
import json
import re
from bs4 import BeautifulSoup


def get_product_info(brand: str, article: str):
    """
    Функция отправляет запрос к API и возвращает информацию о товаре, парся HTML-ответ.

    :param brand: Название бренда
    :param article: Артикул товара
    :return: Словарь с данными о товаре или сообщение об ошибке
    """
    url = "https://zarulem.online/search/get-results"

    payload = {
        "is_new_search": 1,
        "order_id": 0,
        "clid": 0,
        "vin_query_id": 0,
        "exoid": 0,
        "search_article": article,
        "search_brand": brand,
        "search_type": 0
    }

    try:
        response = requests.post(url, data=payload)
        response.encoding = "utf-8"

        if response.status_code != 200:
            return {"Ошибка": f"Не удалось получить данные, код ответа: {response.status_code}"}

        decoded_response = response.text.encode().decode('unicode-escape')

        # Используем BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(decoded_response, "html.parser")
        try:
            description_tag = soup.find("span", class_="name_info_container")
            if description_tag:
                raw_description = description_tag.text.strip()
                # Убираем всё после </span>
                description = re.split(r'<\\/span>', raw_description, maxsplit=1)[0]
            else:
                description = "Описание не найдено"

            quantity_match = re.search(r'(\d+) шт\.', soup.text)
            quantity = int(quantity_match.group(1)) if quantity_match else "Нет данных"

            delivery_match = re.search(r'Поставка (\d+) дня', soup.text)
            delivery_days = int(delivery_match.group(1)) if delivery_match else "Нет данных"

            price_tag = soup.find("div", class_="price_inner")
            price = int(price_tag.text.strip().split()[0]) if price_tag else "Нет данных"

            product_info = {
                "brand": brand,
                "article": article,
                "description": description,
                "quantity": quantity,
                "delivery_days": delivery_days,
                "price": price
            }
            return product_info
        except AttributeError:
            return {"Ошибка": "Не удалось извлечь данные о товаре"}

    except requests.RequestException as e:
        return {"Ошибка": f"Сетевая ошибка: {e}"}


# Пример вызова функции
if __name__ == "__main__":
    result = get_product_info("MANN-FILTER", "w753")
    print(result)
