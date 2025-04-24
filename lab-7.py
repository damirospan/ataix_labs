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
        print(f"⚠️ Ордер {order_id} не табылды: {data.get('message')}")
        return None
    return data.get("result", {}).get("status", "unknown").lower()

def create_sell_order(symbol, price, quantity):
    url = f"{BASE_URL}/api/orders"
    payload = {
        "symbol": symbol,
        "side": "sell",
        "type": "limit",
        "quantity": round(quantity, 8),
        "price": round(price, 6)
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    data = response.json()

    if data.get("status", False):
        return data
    else:
        return None

def main():
    orders = load_orders()
    updated_orders = []

    for order in orders:
        order_id = order.get("id", "unknown")
        status = check_order_status(order_id)
        time.sleep(0.5)

        if status == "filled" and "sell_reference" not in order:
            print(f"✅ Ордер {order_id} орындалған. Сатуға ордер жасаймыз...")
            sell_price = round_to_step(order["price"] * 1.02, 0.001)
            quantity = order["amount"]
            symbol = order["symbol"]

            sell_order = create_sell_order(symbol, sell_price, quantity)
            if sell_order:
                sell_order_id = (
                    sell_order.get("result", {}).get("orderID") or
                    sell_order.get("orderID") or
                    "unknown"
                )
                order["sell_reference"] = sell_order_id
                print(f"🆕 Новый sell-ордер создан для {order_id} → Sell ID: {sell_order_id}")
            else:
                print(f"❌ Ошибка создания sell-ордера для {order_id}.")

        elif status == "new":
            print(f"🟡 Ордер {order_id} пока активен (статус: new)")
        elif status == "cancelled":
            print(f"🚫 Ордер {order_id} отменен")
        elif status is None:
            print(f"⚠️ Статус ордера {order_id} не определен")
        else:
            print(f"ℹ️ Ордер {order_id}: статус {status}")

        updated_orders.append(order)

    save_orders(updated_orders)
    print("\n✅ Барлық өзгерістер orders.json файлына сақталды.")

if __name__ == "__main__":
    main()
