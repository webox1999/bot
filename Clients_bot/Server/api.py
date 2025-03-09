from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
from flask_cors import CORS

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

def get_client_cashback(client_id):
    """Запрашивает полную информацию о клиенте. Берет только кэшбек (Можно вытащить всю инфу)"""
    payload = {"action": "get_company", "company_id": int(client_id)}
    response = SESSION.post(URL, json=payload)

    if response.status_code == 200:
        return response.json().get("company_cashback", [])

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
    cashback = get_client_cashback(client_id)

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

    # Формируем payload
    car_info = get_car_info(vin)
    car_engine = car_info["engine_num"]
    made_date = car_info["made_date"]
    payload = {
        "action": "save_company_car",
        "company_id": client_id,
        "vin": vin,
        "engine_num": car_engine,
        "made_date": made_date
    }

    # Отправляем POST-запрос
    response = SESSION.post(URL, json=payload)

    # Возвращаем ответ
    if response.status_code == 200:
        car_info = get_car_info(vin)
        return response.json(), car_info

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
