import json
import os
import urllib.parse
import urllib.request

API_URL = "https://api.frankfurter.dev/v2/rates"
METAL_URL = "https://api.gold-api.com/price"
HEADERS = {"User-Agent": "send-rate/1.0"}


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


def send_telegram(token, chat_id, text):
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=body, timeout=10) as res:
        res.read()


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    usd, date = fetch_krw_rate("USD")
    eur, _ = fetch_krw_rate("EUR")
    jpy, _ = fetch_krw_rate("JPY")

    gold = fetch_usd_price("XAU")
    silver = fetch_usd_price("XAG")
    copper = fetch_usd_price("HG")

    text = (
        f"환율 ({date} 기준)\n"
        f"USD 1달러: {usd:,.2f}원\n"
        f"EUR 1유로: {eur:,.2f}원\n"
        f"JPY 100엔: {jpy * 100:,.2f}원\n"
        f"\n"
        f"원자재 (USD, 원화 환산)\n"
        f"금: ${gold:,.2f}/oz ({gold * usd:,.0f}원)\n"
        f"은: ${silver:,.2f}/oz ({silver * usd:,.0f}원)\n"
        f"구리: ${copper:,.4f}/lb ({copper * usd:,.0f}원)"
    )
    send_telegram(token, chat_id, text)
    print(text)


if __name__ == "__main__":
    main()
