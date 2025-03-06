from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Постоянные данные
URL = "https://sort1.pro/api/index.php"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
SESSION.cookies.set("SORT1SESSID", "7b57jh260595ll819hj3fi5o1g")


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
