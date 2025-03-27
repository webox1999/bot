import json
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import re
from Clients_bot.utils.helpers import PARTS_CACHE, normalize_article
from Clients_bot.config import PARTS_ID_FILE, PARTS_DETAILS_FILE, PARTS_ID_CACHE_FILE, PARTS_CACHE_FILE

GOOD_BRANDS = {
    "TRW", "LUCAS", "TEXTAR", "ATE", "FERODO", "BOSCH", "MINTEX", "REMSA",
    "NK", "Kayaba", "KYB", "BOGE", "SACHS", "BILSTEIN", "DELPHI", "MEYLE",
    "MANN", "FILTRON", "HENGST", "KNECHT", "MAHLE", "SKF", "SNR", "FAG",
    "INA", "SASIC", "LOBRO", "GKN", "SPIDAN", "METELLI", "ELRING",
    "VICTOR REINZ", "PAYEN", "HEPU", "DOLZ", "NISSENS", "HELLA",
    "DENSO", "NGK", "BERU", "LUK", "VALEO", "BOSAL" , "WIX",
}
short_names = {
    "Детали подвески и рулевого управления": "Подвеска и рулевое",
    "Приводные ремни, компоненты привода ремня": "Приводные ремни",
    "Амортизаторы, пружины и их компоненты": "Амортизаторы и пружины",
    "Цепи ГРМ и их компоненты": "К-т ГРМ",
    "Ступицы, подшипники ступиц": "Ступицы и подшипники",
    "Опоры двигателя и трансмиссии": "Опоры двигателя",
    "Прокладки, уплотнительные кольца": "Прокладки и кольца",
    "Стартеры, генераторы": "Стартеры и генераторы",
    "Щетки стеклоочистителя": "Дворники",
    "Газовые упоры": "Газовые упоры"
}

cached_menus = {}  # 🔥 Кешируем меню для возврата


def load_parts_by_id_cache():
    """Загружает кеш запчастей по модификациям с сокращенными категориями"""
    if os.path.exists(PARTS_ID_CACHE_FILE):
        with open(PARTS_ID_CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    try:
        with open(PARTS_ID_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        parts_cache = {}

        for item in data:
            modification_id = str(item["modification_id"])
            categorized_parts = {}

            for part in item["parts"]:
                category = part.get("category", "Без категории")
                short_category = short_names.get(category, category)  # Заменяем на короткое название

                if short_category not in categorized_parts:
                    categorized_parts[short_category] = []

                categorized_parts[short_category].append(part)

            parts_cache[modification_id] = categorized_parts

        with open(PARTS_ID_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(parts_cache, file, ensure_ascii=False, indent=4)

        return parts_cache

    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Глобальный кеш запчастей по модификациям
PARTS_BY_ID_CACHE = load_parts_by_id_cache()


def load_parts_by_id(modification_id):
    """Быстрый поиск запчастей по modification_id (O(1))"""
    return PARTS_BY_ID_CACHE.get(str(modification_id), None)


def load_parts_cache():
    """Загружает кеш деталей (если есть), иначе создает."""
    if os.path.exists(PARTS_CACHE_FILE):
        with open(PARTS_CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    try:
        with open(PARTS_DETAILS_FILE, "r", encoding="utf-8") as file:
            parts_data = json.load(file)

        parts_cache = {item["_id"].upper(): item for item in parts_data}  # Храним в верхнем регистре

        with open(PARTS_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(parts_cache, file, ensure_ascii=False, indent=4)

        return parts_cache

    except (FileNotFoundError, json.JSONDecodeError):
        return {}


async def create_parts_menu(articles):
    """Создаёт inline-клавиатуру с названиями деталей."""
    builder = InlineKeyboardBuilder()
    seen_names = {}

    menu_text = "**Выберите запчасть:**\n\n"
    for article in articles:
        part = PARTS_CACHE.get(normalize_article(article))  # Теперь поиск мгновенный (O(1))
        if not part:
            continue

        name = part.get("name", "Неизвестная деталь")
        count = seen_names.get(name, 0) + 1
        seen_names[name] = count
        display_name = f"{name} [{count} вариант]" if count > 1 else name

        builder.button(text=display_name, callback_data=f"show_{article}")

    builder.adjust(1)
    return menu_text, builder.as_markup()

