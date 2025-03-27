
from Clients_bot.config import makers_id, models_id, modifications_id


def normalize(text):
    return text.lower().replace("'", "").replace("lci", "").replace("n", "").replace("-", "").strip()

def find_modifications_by_vin(vin_code: str):
    import requests
    import json
    from datetime import datetime

    print(f"\n🚗 Поиск модификации для VIN: {vin_code}")

    # 1. Получаем данные по VIN
    try:
        resp = requests.get(f"http://127.0.0.1:8050/laximo?vin={vin_code}", timeout=10)
        resp.raise_for_status()
        vehicles = resp.json()
    except Exception as e:
        print(f"❌ Ошибка запроса VIN: {e}")
        return []

    print(f"🔎 Получено {len(vehicles)} записей от VIN-API\n")

    # 2. Загружаем JSON-файлы
    with open(makers_id, "r", encoding="utf-8") as f:
        makers = json.load(f)
    with open(models_id, "r", encoding="utf-8") as f:
        models = json.load(f)
    with open(modifications_id, "r", encoding="utf-8") as f:
        modifications = json.load(f)

    results = []

    for vehicle in vehicles:
        print(f"🧩 VIN данные: {vehicle}\n")

        vin_brand = vehicle.get("brand", "").lower()
        vin_model_name = vehicle.get("model_name", "").lower()
        vin_model_code = vehicle.get("model_code", "").lower()
        vin_engine = vehicle.get("engine_code", "").upper()
        vin_power = vehicle.get("power_kw", "").strip()
        vin_release = vehicle.get("release_date", "")

        print(f"🔍 Ищем brand_id по названию: {vin_brand}")
        brand_id = None
        for b in makers:
            if b["brand"].lower() == vin_brand:
                brand_id = b["id"]
                print(f"✅ Найден brand_id: {brand_id}")
                break
        if not brand_id:
            print("❌ Бренд не найден\n")
            continue

        print(f"🔍 Ищем model_id по названию: {vin_model_name} или коду: {vin_model_code}")
        model_id = None
        vin_model_name_norm = normalize(vin_model_name)
        vin_model_code_norm = normalize(vin_model_code)
        for m in models:
            if m["brand_id"] != brand_id:
                continue

            model_name_norm = normalize(m["model"])

            if vin_model_name_norm in model_name_norm or vin_model_code_norm in model_name_norm:
                model_id = m["model_id"]
                print(f"✅ Найден model_id: {model_id} по модели: {m['model']}")
                break
        if not model_id:
            print("❌ Модель не найдена\n")
            continue

        print(f"📦 Ищем модификации модели {model_id}")
        possible_mods = [mod for mod in modifications if mod["model_id"] == model_id]
        print(f"🔧 Найдено {len(possible_mods)} модификаций\n")

        for mod in possible_mods:
            score = 0
            reasons = []

            if vin_engine and vin_engine in mod["modification"]:
                score += 2
                reasons.append("код двигателя совпал")

            if vin_power and vin_power in mod["power_engine"]:
                score += 1
                reasons.append("мощность совпала")

            try:
                start_str, end_str = mod["years"].split("-")
                start_date = datetime.strptime(start_str.strip() + "/01", "%m/%y/%d").date()
                end_date = datetime.strptime(end_str.strip() + "/01", "%m/%y/%d").date()
                release_date = datetime.strptime(vin_release, "%Y-%m-%d").date()
                if start_date <= release_date <= end_date:
                    score += 2
                    reasons.append("дата выпуска в диапазоне")
            except Exception as e:
                print(f"⚠️ Ошибка при проверке даты: {e}")

            if score > 0:
                print(f"✅ Совпадение: {mod['modification']} ({mod['years']}) — {score} ★")
                results.append({
                    "modification_id": mod["modification_id"],
                    "modification": mod["modification"],
                    "years": mod.get("years", ""),
                    "power_engine": mod.get("power_engine", ""),
                    "score": score,
                    "reasons": reasons
                })
            else:
                print(f"❌ Не подошло: {mod['modification']}")

        print("-" * 50)

    # Сортируем по убыванию совпадения
    results.sort(key=lambda x: x["score"], reverse=True)

    # Фильтруем только хорошие результаты (3★ и выше)
    results = [r for r in results if r["score"] >= 3]

    print(f"\n🎯 Всего найдено совпадений: {len(results)}\n")
    return results


