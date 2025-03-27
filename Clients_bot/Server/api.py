from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from flask_cors import CORS
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Постоянные данные
URL = "https://sort1.pro/api/index.php"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
SESSION.cookies.set("SORT1SESSID", "7b57jh260595ll819hj3fi5o1g")

# Функция для получения даты 180 месяц назад
def get_default_start_date():
    return (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

def get_car_info(vin):
    """Запрашивает полную информацию о авто."""
    payload = {"action": "get_car_by_vin", "vin": vin}
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        car_info = response.json().get("car", [])

        if car_info:  # Если клиент найден
            return {
                "engine_num": car_info.get("engine_num", 'Нет данных'),
                "made_date": car_info.get("made_date", 'Нет данных')
            }

    return None

def get_client_id(phone_number):
    """Ищет клиента по номеру телефона и возвращает всю информацию о нём."""
    payload = {
        "action": "get_clients",
        "page": "1",
        "search_clients_client_name": phone_number  # Передаём телефон сразу в запрос
    }

    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        clients = response.json().get("clients", [])

        if clients:  # Если клиент найден
            client = clients[0]  # Берём первого (так как API должен вернуть одного)
            return {
                "id": client.get("id"),
                "name": client.get("name"),
                "balance": client.get("company_balance"),
                "create_date": client.get("create_date"),
                "sum_trade": client.get("sum_trade")
            }

    return None



def get_client_orders(client_id):
    """Запрашивает заказы клиента."""
    payload = {"action": "get_client_zakaz_details", "company_id": int(client_id)}
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json().get("zakaz_details", [])

    return []


def get_client_cars(client_id):
    """Запрашивает автомобили клиента."""
    payload = {"action": "get_company_cars", "company_id": int(client_id)}
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json().get("company_cars", [])

    return []

def get_client_data(client_id):
    """Запрашивает полную информацию о клиенте. Берет только кэшбек (Можно вытащить всю инфу)"""
    payload = {"action": "get_company", "company_id": int(client_id)}
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()

    return []



@app.route("/get_client", methods=["GET"])
def get_client_info():
    """Обрабатывает запрос, получает данные клиента и возвращает JSON-ответ."""
    phone_number = request.args.get("phone")

    if not phone_number:
        return jsonify({"error": "Введите номер телефона"}), 400

    client_data = get_client_id(phone_number)

    if not client_data:
        return jsonify({"error": "Клиент не найден"}), 404

    # Теперь достаём данные из словаря
    client_id = client_data["id"]
    client_name = client_data["name"]
    balance = client_data["balance"]
    create_date = client_data["create_date"]
    sum_trade = client_data["sum_trade"]

    if not client_id:
        return jsonify({"error": "Клиент не найден"}), 404

    orders = get_client_orders(client_id)
    cars = get_client_cars(client_id)
    cashback = get_client_data(client_id).get("company_cashback", [])

    return jsonify({
        "client_id": client_id,
        "name": client_name,
        "balance": balance,
        "reg_date": create_date,
        "oborot": sum_trade,
        "orders": orders,
        "cars": cars,
        "cashback": cashback
    })

@app.route("/get_payments", methods=["GET"])
def get_payments():
    # start_date = get_default_start_date()
    # end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    payload = {
        "action": "get_payments",
        "from_date": start_date,
        "to_date":  end_date  # Передаём телефон сразу в запрос
    }
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()

@app.route("/register_client", methods=["GET"])
def register_client():
    # Получаем параметры из запроса
    name = request.args.get("name")
    phone = request.args.get("phone")
    client_type = request.args.get("type")
    bonuses = request.args.get("bonuses")
    vin = request.args.get("vin")  # Может быть None, если не передан

    # Формируем payload
    payload = {
        "action": "fast_save_company",
        "company_name": name,
        "mphone": phone,
        "okopf": client_type,
        "price_type": bonuses,
        "vin": vin if vin else ""  # Добавляем vin, даже если он не передан
    }

    # Отправляем POST-запрос
    response = SESSION.post(URL, json=payload)

    # Возвращаем ответ
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to process request", "status_code": response.status_code}, response.status_code

@app.route("/add_car", methods=["GET"])
def add_car():
    # Получаем параметры из запроса
    vin = request.args.get("vin")  # Может быть None, если не передан
    client_id = request.args.get("id")

    # Проверяем, передан ли VIN-код
    if not vin:
        return {"error": "VIN is required"}, 400

    # Получаем информацию об автомобиле
    car_info = get_car_info(vin)

    # Проверяем, найдены ли данные об авто
    if not car_info or car_info.get("engine_num") == "" or car_info.get("made_date") == "":
        return {"error": "Vehicle information not found", "vin": vin}, 404

    # Формируем payload для основного API
    payload = {
        "action": "save_company_car",
        "company_id": client_id,
        "vin": vin,
        "engine_num": car_info["engine_num"],
        "made_date": car_info["made_date"]
    }

    # Отправляем POST-запрос
    response = SESSION.post(URL, json=payload)

    # Возвращаем ответ
    if response.status_code == 200:
        return response.json(), car_info
    else:
        return {"error": "Failed to process request", "status_code": response.status_code}, response.status_code


@app.route("/add_by_brand", methods=["GET"])
def add_by_brand():
    # Получаем параметры из запроса vin=${VIN}&brand=${brand}&model=${model}&engine=${engineCode}&year=${year}
    vin = request.args.get("vin")  # Может быть None, если не передан
    client_id = request.args.get("id")
    brand = request.args.get("brand")
    model = request.args.get("model")
    car_engine = request.args.get("engine")
    year = request.args.get("year")
    modification = request.args.get("type")
    car_id = request.args.get("car_id")
    # Формируем payload
    payload = {
        "action": "save_company_car",
        "company_id": client_id,
        "company_car_id": car_id,
        "vin": vin,
        "engine_num": car_engine,
        "made_year": year,
        "auto_maker_id": brand,
        "auto_model": model,
        "auto_doc_num": modification
    }

    # Отправляем POST-запрос
    response = SESSION.post(URL, json=payload)

    # Возвращаем ответ
    if response.status_code == 200:
        return response.json() , payload

    else:
        return {"error": "Failed to process request", "status_code": response.status_code}, response.status_code



@app.route("/car_delete", methods=["GET"])
def car_delete():
    car_id = request.args.get("id")

    payload = {
        "action": "delete_company_car",
        "company_car_id": car_id,
    }
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()

@app.route("/car_info", methods=["GET"])
def get_car_info_by_id():
    car_id = request.args.get("id")

    payload = {
        "action": "get_company_car",
        "company_car_id": car_id,
    }
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()


@app.route("/get_brands", methods=["GET"])
def get_brands():

    payload = {
        "action": "get_auto_makers",
    }
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()

@app.route("/get_models", methods=["GET"])
def get_models():
    car_id = request.args.get("id")

    payload = {
        "action": "get_auto_models",
        "auto_maker_id": car_id,
    }
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()

@app.route("/get_profit", methods=["GET"])
def get_profit():
    phone = request.args.get("phone")
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    data = get_client_id(phone)
    client_id = data.get("id")
    client_name = data.get("name")
    payload = {
        "action": "get_report_profit",
        "contragent_id":  client_id,
        "date_from": start_date,
        "date_to":  end_date  # Передаём телефон сразу в запрос
    }
    response = SESSION.post(URL, json=payload)
    dealer_sum = response.json().get("dealer_sum")
    sale_sum = response.json().get("sale_sum")
    if response.status_code == 200:
        return jsonify({
            "client_id": client_id,
            "name": client_name,
            "dealer_sum": dealer_sum,
            "sale_sum": sale_sum
        })

@app.route("/add_code", methods=["GET"])
def add_codes():
    client_id = request.args.get("client_id")
    codes = request.args.get("code")
    client_data = get_client_data(client_id)
    check = client_data.get("descr")
    if check == "":
        code = f'Действующие купоны: {codes}'
    else:
        code = f'{check}, {codes}'
    payload = {
        "action": "save_company",
        "company_id": client_id,
        "descr": code,
        "show_descr": "on",
    }
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()

@app.route("/delete_code", methods=["GET"])
def delete_codes():
    client_id = request.args.get("client_id")
    codes = request.args.get("code")
    client_data = get_client_data(client_id)
    check = client_data.get("descr")
    payload = {}
    if codes in check:
        payload = {
            "action": "save_company",
            "company_id": client_id,
            "descr": check.replace(f", {codes}", ""),
            "show_descr": "on"
        }
    else:
        return {'error': 'код не найден'}
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json()


def match_any(text, keywords):
    return any(word in text.lower() for word in keywords)


def parse_vehicle_html(soup):
    vehicles = []

    table = soup.select_one("table.vehicle-modifications")
    if not table:
        print("⚠️ Таблица не найдена.")
        return []

    # Извлекаем заголовки таблицы
    headers = table.select("thead th")
    column_map = {}

    for i, header in enumerate(headers):
        text = header.text.strip()

        if match_any(text, ['двигатель', 'engine', 'номер двигателя']):
            column_map['engine'] = i
        elif match_any(text, ['дата выпуска', 'release date']):
            column_map['release_date'] = i
        elif match_any(text, ['код модели', 'model code']):
            column_map['model_code'] = i
        elif match_any(text, ['модель']) and 'код' not in text.lower():
            column_map['model_name'] = i
        elif match_any(text, ['регион']):
            column_map['region'] = i
        elif match_any(text, ['кпп', 'трансмиссия', 'gearbox']):
            column_map['gearbox'] = i
        elif match_any(text, ['привод', 'drive']):
            column_map['drive'] = i
        elif match_any(text, ['кузов', 'body']):
            column_map['body'] = i
        elif match_any(text, ['салон', 'цвет', 'interior']):
            column_map['interior'] = i
        elif match_any(text, ['дверей']):
            column_map['doors'] = i
        elif match_any(text, ['руль', 'рулевое управление']):
            column_map['steering'] = i

    # Заголовок с брендом и моделью из <h3>
    h3 = soup.select_one("div.grouped-vehicles h3")
    brand, model_from_h3 = None, None
    if h3:
        parts = h3.text.strip().split(" ", 1)
        if len(parts) == 2:
            brand, model_from_h3 = parts

    # Парсим строки таблицы
    rows = table.select("tbody tr")
    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) < 5:
            continue

        try:
            vehicle = {
                "brand": brand,
                "model_from_h3": model_from_h3
            }

            # Извлекаем по column_map
            for key, idx in column_map.items():
                if idx < len(cells):
                    vehicle[key] = cells[idx].text.strip()
                else:
                    vehicle[key] = ""

            # Нормализуем дату
            if "release_date" in vehicle:
                try:
                    release = vehicle["release_date"]
                    vehicle["release_date"] = datetime.strptime(release, "%d.%m.%Y").strftime("%Y-%m-%d")
                except:
                    vehicle["release_date"] = ""

            # Разбор мощности и двигателя
            if "engine" in vehicle:
                engine = vehicle["engine"]
                vehicle["engine_code"] = engine.split()[0] if engine else ""
                if "/" in engine:
                    vehicle["power_kw"] = engine.split("/")[-1].replace("kW", "").strip(")")
                else:
                    vehicle["power_kw"] = ""

            vehicles.append(vehicle)

        except Exception as e:
            print(f"⚠️ Ошибка при разборе строки: {e}")
            continue

    return vehicles


@app.route("/laximo", methods=["GET"])
def parse_vehicle_info_from_vin():
    vin = request.args.get("vin")
    url = f"https://sort1.pro/laximo/index.php?task=vehicles&ft=FindVehicle&c=&identString={vin}&ssd="

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://sort1.pro/laximo/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Ошибка запроса: {str(e)}"}

    soup = BeautifulSoup(response.text, "html.parser")
    result = parse_vehicle_html(soup)
    return result

@app.route("/tecdoc_brands", methods=["GET"])
def get_tecdoc_linkage_targets():
    url = "https://tecdoc-catalog.p.rapidapi.com/manufacturers/list/lang-id/4/country-filter-id/62/type-id/1"

    headers = {
        "x-rapidapi-key": "4707c00030msh0e31199d8eff5c1p14242bjsn1effc6003ae4",
        "x-rapidapi-host": "tecdoc-catalog.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    return response.json()

@app.route("/tecdoc_models", methods=["GET"])
def get_tecdoc_models():
    brand = request.args.get("brand_id")
    url = f"https://tecdoc-catalog.p.rapidapi.com/models/list/manufacturer-id/{brand}/lang-id/4/country-filter-id/62/type-id/1"

    headers = {
        "x-rapidapi-key": "4707c00030msh0e31199d8eff5c1p14242bjsn1effc6003ae4",
        "x-rapidapi-host": "tecdoc-catalog.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)


    return response.json()

@app.route("/tecdoc_mod", methods=["GET"])
def get_tecdoc_modif():
    brand = request.args.get("brand_id")
    model = request.args.get("m_id")
    url = f"https://tecdoc-catalog.p.rapidapi.com/types/list-vehicles-types/{model}/manufacturer-id/{brand}/lang-id/4/country-filter-id/62/type-id/1"

    headers = {
        "x-rapidapi-key": "4707c00030msh0e31199d8eff5c1p14242bjsn1effc6003ae4",
        "x-rapidapi-host": "tecdoc-catalog.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)


    return response.json()

@app.route("/tecdoc_car", methods=["GET"])
def get_tecdoc_carInfo():
    brand = request.args.get("brand_id")
    model = request.args.get("car_id")

    url = f"https://tecdoc-catalog.p.rapidapi.com/types/vehicle-type-details/{model}/manufacturer-id/{brand}/lang-id/16/country-filter-id/62/type-id/1"

    headers = {
        "x-rapidapi-key": "4707c00030msh0e31199d8eff5c1p14242bjsn1effc6003ae4",
        "x-rapidapi-host": "tecdoc-catalog.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)


    return response.json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
