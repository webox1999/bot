# utils/delivery.py
from datetime import datetime, timedelta


def calculate_delivery_date(create_date_str: str, delivery_days: int, deliverer_id: str) -> str:
    """Расчет даты доставки с учетом поставщика и выходных (воскресенье)."""
    create_date = datetime.strptime(create_date_str, "%Y-%m-%d %H:%M:%S")
    delivery_days = int(delivery_days) + 1  # Добавляем +1 день для перестраховки

    # Обычные поставщики (без особого графика)
    if deliverer_id not in ["372", "1105"]:
        estimated_delivery = create_date + timedelta(days=delivery_days)
        if estimated_delivery.weekday() == 6:  # Если воскресенье, переносим на понедельник
            estimated_delivery += timedelta(days=1)
        return estimated_delivery.strftime("%Y-%m-%d")

    # Поставщики с особым графиком
    supplier_schedule = {
        "372": [0, 3],  # Понедельник и Четверг
        "1105": [2, 5]  # Среда и Суббота
    }

    allowed_days = supplier_schedule[deliverer_id]

    # Первичная дата прибытия до поставщика
    estimated_arrival = create_date + timedelta(days=delivery_days)
    while estimated_arrival.weekday() not in allowed_days:
        estimated_arrival += timedelta(days=1)

    # Если дата выпадает на воскресенье, переносим на следующий день
    if estimated_arrival.weekday() == 6:
        estimated_arrival += timedelta(days=1)

    # Дата доставки в магазин (следующий день поставки)
    final_delivery = estimated_arrival + timedelta(days=1)
    while final_delivery.weekday() not in allowed_days:
        final_delivery += timedelta(days=1)

    return f"{estimated_arrival.strftime('%Y-%m-%d')} или {final_delivery.strftime('%Y-%m-%d')}"
