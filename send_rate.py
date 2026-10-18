import json
import os
import urllib.parse
import urllib.request

API_URL = "https://api.frankfurter.dev/v2/rates"
METAL_URL = "https://api.gold-api.com/price"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
HEADERS = {"User-Agent": "send-rate/1.0"}
G_PER_OZ = 31.1034768
OZ_PER_KG = 1000 / G_PER_OZ
LB_PER_KG = 1 / 0.45359237

# 강수 알림 대상 도시 (이름, 위도, 경도)
CITIES = [
    ("서울", 37.5665, 126.9780),
    ("부산", 35.1796, 129.0756),
    ("대구", 35.8714, 128.6014),
    ("광주", 35.1595, 126.8526),
    ("대전", 36.3504, 127.3845),
    ("인천", 37.4563, 126.7052),
    ("울산", 35.5384, 129.3114),
]
DEFAULT_RAIN_THRESHOLD = 50


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


def fetch_rain_probabilities(cities):
    """도시별 오늘의 최대 강수확률(%)을 (이름, 확률) 목록으로 반환한다."""
    query = urllib.parse.urlencode(
        {
            "latitude": ",".join(str(lat) for _, lat, _ in cities),
            "longitude": ",".join(str(lon) for _, _, lon in cities),
            "daily": "precipitation_probability_max",
            "timezone": "Asia/Seoul",
            "forecast_days": 1,
        }
    )
    req = urllib.request.Request(f"{WEATHER_URL}?{query}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.load(res)
    # 위치가 여러 개면 위치별 결과의 배열로 응답한다.
    if isinstance(data, dict):
        data = [data]
    return [
        (name, item["daily"]["precipitation_probability_max"][0])
        for (name, _, _), item in zip(cities, data)
    ]


def send_telegram(token, chat_id, text):
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=body, timeout=10) as res:
        res.read()


def build_rate_text():
    usd, date = fetch_krw_rate("USD")
    eur, _ = fetch_krw_rate("EUR")
    jpy, _ = fetch_krw_rate("JPY")

    gold = fetch_usd_price("XAU")
    silver = fetch_usd_price("XAG")
    copper = fetch_usd_price("HG")

    return (
        f"환율 ({date} 기준)\n"
        f"USD 1달러: {usd:,.2f}원\n"
        f"EUR 1유로: {eur:,.2f}원\n"
        f"JPY 100엔: {jpy * 100:,.2f}원\n"
        f"\n"
        f"원자재 (USD / 원화)\n"
        f"금: ${gold:,.2f}/oz ({gold / G_PER_OZ * usd:,.0f}원/g)\n"
        f"은: ${silver:,.2f}/oz ({silver * OZ_PER_KG * usd:,.0f}원/kg)\n"
        f"구리: ${copper:,.4f}/lb ({copper * LB_PER_KG * usd:,.0f}원/kg)"
    )


def build_rain_text(threshold):
    """강수확률이 threshold% 이상인 도시가 없으면 None을 반환한다."""
    rainy = [
        (name, prob)
        for name, prob in fetch_rain_probabilities(CITIES)
        if prob is not None and prob >= threshold
    ]
    if not rainy:
        return None
    rainy.sort(key=lambda item: item[1], reverse=True)
    lines = [f"강수 알림 (오늘 강수확률 {threshold}% 이상)"]
    lines += [f"{name}: {prob}%" for name, prob in rainy]
    return "\n".join(lines)


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    # 비어 있는 환경 변수가 넘어와도 기본값을 쓰도록 or를 사용한다.
    threshold = int(os.environ.get("RAIN_THRESHOLD") or DEFAULT_RAIN_THRESHOLD)

    rate_text = build_rate_text()
    send_telegram(token, chat_id, rate_text)
    print(rate_text)

    rain_text = build_rain_text(threshold)
    if rain_text:
        send_telegram(token, chat_id, rain_text)
        print()
        print(rain_text)
    else:
        print(f"\n강수확률 {threshold}% 이상인 도시가 없어 강수 알림은 보내지 않았습니다.")


if __name__ == "__main__":
    main()
