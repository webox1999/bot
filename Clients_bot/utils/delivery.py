# utils/delivery.py
from datetime import datetime, timedelta

def calculate_delivery_date(create_date_str: str, delivery_days: int, deliverer_id: str) -> str:
    """Расчет даты доставки с учетом поставщика."""
    create_date = datetime.strptime(create_date_str, "%Y-%m-%d %H:%M:%S")
    delivery_days = int(delivery_days) + 1

    if deliverer_id not in ["372", "1105"]:
        return (create_date + timedelta(days=delivery_days)).strftime("%Y-%m-%d")

    supplier_schedule = {
        "372": [0, 3],  # Понедельник и Четверг
        "1105": [2, 5]  # Среда и Суббота
    }
    allowed_days = supplier_schedule[deliverer_id]

    estimated_arrival = create_date + timedelta(days=delivery_days)
    while estimated_arrival.weekday() not in allowed_days:
        estimated_arrival += timedelta(days=1)

    final_delivery = estimated_arrival + timedelta(days=1)
    while final_delivery.weekday() not in allowed_days:
        final_delivery += timedelta(days=1)

    return f"{estimated_arrival.strftime('%Y-%m-%d')} или {final_delivery.strftime('%Y-%m-%d')}"