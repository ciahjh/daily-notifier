import datetime
import json
import os
import urllib.parse
import urllib.request

API_URL = "https://api.frankfurter.dev/v2/rates"
METAL_URL = "https://api.gold-api.com/price"
HEADERS = {"User-Agent": "send-rate/1.0"}
G_PER_OZ = 31.1034768
OZ_PER_KG = 1000 / G_PER_OZ
LB_PER_KG = 1 / 0.45359237
WEEKDAYS = "월화수목금토일"


def fetch_krw_rate(base):
    query = urllib.parse.urlencode({"base": base, "quotes": "KRW"})
    req = urllib.request.Request(f"{API_URL}?{query}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.load(res)[0]
    return data["rate"], data["date"]


def fetch_usd_price(symbol):
    req = urllib.request.Request(f"{METAL_URL}/{symbol}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.load(res)["price"]


def format_date(date):
    day = datetime.date.fromisoformat(date)
    return f"{date} ({WEEKDAYS[day.weekday()]})"


def send_telegram(token, chat_id, text):
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=body, timeout=10) as res:
        res.read()


def build_text():
    usd, date = fetch_krw_rate("USD")
    eur, _ = fetch_krw_rate("EUR")
    jpy, _ = fetch_krw_rate("JPY")

    gold = fetch_usd_price("XAU")
    silver = fetch_usd_price("XAG")
    copper = fetch_usd_price("HG")

    return (
        f"환율 - {format_date(date)} 기준\n"
        f"USD 1달러: {usd:,.2f}원\n"
        f"EUR 1유로: {eur:,.2f}원\n"
        f"JPY 100엔: {jpy * 100:,.2f}원\n"
        f"\n"
        f"원자재 (USD / 원화)\n"
        f"금: ${gold:,.2f}/oz ({gold / G_PER_OZ * usd:,.0f}원/g)\n"
        f"은: ${silver:,.2f}/oz ({silver * OZ_PER_KG * usd:,.0f}원/kg)\n"
        f"구리: ${copper:,.4f}/lb ({copper * LB_PER_KG * usd:,.0f}원/kg)"
    )


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    text = build_text()
    send_telegram(token, chat_id, text)
    print(text)


if __name__ == "__main__":
    main()
