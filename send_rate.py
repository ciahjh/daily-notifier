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

# 기본 위치: 서울
DEFAULT_LATITUDE = "37.5665"
DEFAULT_LONGITUDE = "126.9780"
DEFAULT_CITY = "서울"

# WMO 날씨 코드 -> 설명
WEATHER_CODES = {
    0: "맑음",
    1: "대체로 맑음",
    2: "구름 조금",
    3: "흐림",
    45: "안개",
    48: "안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    56: "얼어붙는 이슬비",
    57: "얼어붙는 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    66: "얼어붙는 비",
    67: "얼어붙는 비",
    71: "약한 눈",
    73: "눈",
    75: "강한 눈",
    77: "싸락눈",
    80: "약한 소나기",
    81: "소나기",
    82: "강한 소나기",
    85: "약한 눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "우박 동반 뇌우",
    99: "우박 동반 뇌우",
}


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


def fetch_weather(latitude, longitude):
    query = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Asia/Seoul",
            "forecast_days": 1,
        }
    )
    req = urllib.request.Request(f"{WEATHER_URL}?{query}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.load(res)
    current = data["current"]
    daily = data["daily"]
    return {
        "desc": WEATHER_CODES.get(current["weather_code"], "알 수 없음"),
        "temp": current["temperature_2m"],
        "feels": current["apparent_temperature"],
        "high": daily["temperature_2m_max"][0],
        "low": daily["temperature_2m_min"][0],
        "rain": daily["precipitation_probability_max"][0],
    }


def send_telegram(token, chat_id, text):
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=body, timeout=10) as res:
        res.read()


def build_text():
    # 비어 있는 환경 변수가 넘어와도 기본값을 쓰도록 or를 사용한다.
    city = os.environ.get("WEATHER_CITY") or DEFAULT_CITY
    latitude = os.environ.get("WEATHER_LATITUDE") or DEFAULT_LATITUDE
    longitude = os.environ.get("WEATHER_LONGITUDE") or DEFAULT_LONGITUDE

    usd, date = fetch_krw_rate("USD")
    eur, _ = fetch_krw_rate("EUR")
    jpy, _ = fetch_krw_rate("JPY")

    gold = fetch_usd_price("XAU")
    silver = fetch_usd_price("XAG")
    copper = fetch_usd_price("HG")

    weather = fetch_weather(latitude, longitude)

    return (
        f"날씨 ({city})\n"
        f"{weather['desc']}, 현재 {weather['temp']:.1f}°C (체감 {weather['feels']:.1f}°C)\n"
        f"최저 {weather['low']:.1f}°C / 최고 {weather['high']:.1f}°C\n"
        f"강수확률: {weather['rain']}%\n"
        f"\n"
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


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    text = build_text()
    send_telegram(token, chat_id, text)
    print(text)


if __name__ == "__main__":
    main()
