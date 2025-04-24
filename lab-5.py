import requests
import json

API_KEY = ""
BASE_URL = "https://api.ataix.kz"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

FIXED_BASE = "IMX"
QUOTE = "USDT"
MAX_DEVIATION = 0.05  
def get_balance():
    url = f"{BASE_URL}/api/user/balances"
    response = requests.get(url, headers=HEADERS)

    try:
        data = response.json()
    except Exception as e:
        print(f"❌ Невозможно декодировать JSON: {e}")
        print("📦 Ответ от API:")
        print(response.text)
        raise Exception("❌ API не вернул JSON")

    print("📦 DEBUG balance response:", json.dumps(data, indent=4))

    try:
        # Здесь правильный путь доступа к балансу
        balance_str = data.get("result", {}).get("available", {}).get("USDT", "0.0")
        balance = float(balance_str)
        print(f"💰 Баланс USDT: {balance}")
        return balance
    except Exception as e:
        print("❌ Ошибка разбора ответа:", e)

    raise Exception("❌ Ошибка получения баланса USDT")

def get_symbols():
    url = f"{BASE_URL}/api/symbols"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    symbols = data.get("result", [])
    
    if not symbols:
        print("❌ symbols не получены. Ответ:")
        print(json.dumps(data, indent=4))
    
    return symbols

def find_imx_pair(symbols):
    print("🔍 Ищем пару IMX/USDT...")
    for s in symbols:
        if s.get("base", "").upper() == FIXED_BASE and s.get("quote", "").upper() == QUOTE:
            symbol = s["symbol"]
            min_amount = float(s.get("minTradeSize", 0.01))
            price_to_compare = float(s.get("ask", 0) or s.get("priceToCompare", 0))
            print(f"✅ Найдена пара: {symbol}, minTradeSize = {min_amount}, ask = {price_to_compare}")
            return symbol, min_amount, price_to_compare
    raise Exception("❌ Пара IMX/USDT не найдена")

def round_to_step(value, step):
    return round(round(value / step) * step, 6)

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

    print(f"📦 Ответ от биржи:\n{json.dumps(data, indent=4)}")

    if not data.get("status", False):
        raise Exception(f"❌ Ошибка создания ордера:\n{json.dumps(data, indent=2)}")

    return data

def main():
    balance = get_balance()
    symbols = get_symbols()
    if not symbols:
        raise Exception("❌ Не удалось получить список символов")

    symbol, min_amount, best_price = find_imx_pair(symbols)
    print(f"📊 Расчёт ордеров от цены: {best_price}")
    
    percent_list = [0.02, 0.05, 0.08]
    orders = []
    created_total = 0

    for percent in percent_list:
        raw_price = best_price * (1 - percent)
        price = round_to_step(raw_price, 0.001)

        # Проверка ограничения ±5%
        min_allowed = round_to_step(best_price * (1 - MAX_DEVIATION), 0.001)
        if price < min_allowed:
            print(f"⚠️ Цена {price:.6f} ниже допустимого предела {min_allowed:.6f}, заменена.")
            price = min_allowed

        cost = price * min_amount
        if created_total + cost > balance:
            print(f"⚠️ Недостаточно средств для ордера по цене {price:.6f}")
            break

        response_data = create_order(symbol, price, min_amount)
        order_id = (
            response_data.get("result", {}).get("orderID") or
            response_data.get("result", {}).get("id") or
            response_data.get("id") or
            response_data.get("orderId") or
            "unknown"
        )

        orders.append({
            "id": order_id,
            "symbol": symbol,
            "price": price,
            "amount": min_amount,
            "status": "NEW"
        })
        created_total += cost

    # Сохранение в файл
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Создано ордеров: {len(orders)}. Сохранено в orders.json")

if __name__ == "__main__":
    main()
