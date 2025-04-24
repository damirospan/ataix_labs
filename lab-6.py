import requests
import json
import time

API_KEY = ""
BASE_URL = "https://api.ataix.kz"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

ORDERS_FILE = "orders.json"


def round_to_step(value, step):
    return round(round(value / step) * step, 6)


def load_orders():
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)


def check_order_status(order_id):
    url = f"{BASE_URL}/api/orders/{order_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    if not data.get("status", False):
        print(f"⚠️ Ордер {order_id} не найден или ошибка: {data.get('message')}")
        return None

    return data.get("result", {}).get("status", "unknown").lower()


def delete_order(order_id):
    url = f"{BASE_URL}/api/orders/{order_id}"
    response = requests.delete(url, headers=HEADERS)
    data = response.json()
    return data.get("status", False)


def create_order(symbol, price, quantity):
    url = f"{BASE_URL}/api/orders"
    payload = {
        "symbol": symbol,
        "side": "buy",
        "type": "limit",
        "quantity": round(quantity, 8),
        "price": round(price, 6)
    }

    response = requests.post(url, headers=HEADERS, json=payload)
    data = response.json()

    print(f"📦 Ответ при создании ордера:\n{json.dumps(data, indent=4)}")

    if data.get("status", False):
        return data
    else:
        print(f"❌ Ошибка создания ордера:\n{json.dumps(data, indent=4)}")
        return None


def main():
    orders = load_orders()
    updated_orders = []

    for order in orders:
        order_id = order["id"]
        status = check_order_status(order_id)
        time.sleep(0.5)

        if status == "filled":
            print(f"✅ Ордер {order_id} исполнен.")
            order["status"] = "filled"
            updated_orders.append(order)

        elif status == "new":
            print(f"🕒 Ордер {order_id} активен, но не исполнен. Удаляем...")

            if delete_order(order_id):
                order["status"] = "cancelled"
                print(f"🗑️ Ордер {order_id} удалён.")

                new_price = round_to_step(order["price"] * 1.01, 0.001)
                new_order = create_order(order["symbol"], new_price, order["amount"])

                if new_order:
                    new_order_id = (
                        new_order.get("result", {}).get("orderID") or
                        new_order.get("orderID") or
                        "unknown"
                    )

                    new_entry = {
                        "id": new_order_id,
                        "symbol": order["symbol"],
                        "price": new_price,
                        "amount": order["amount"],
                        "status": "NEW"
                    }

                    updated_orders.append(new_entry)
                    print(f"🔁 Новый ордер создан по цене {new_price}")
                else:
                    print("⚠️ Новый ордер не был создан.")
            else:
                print(f"⚠️ Не удалось удалить ордер {order_id}")
                updated_orders.append(order)

        else:
            print(f"🟡 Ордер {order_id} имеет неожиданный статус: {status}")
            updated_orders.append(order)

    save_orders(updated_orders)
    print("\n📝 Обновлённый orders.json сохранён.")


if __name__ == "__main__":
    main()
