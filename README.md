# rate-notifier

환율과 주요 원자재(금, 은, 구리) 가격을 매일 텔레그램으로 알려 주고, 주요 도시의 강수 소식도 매일 아침 알려 주는 봇입니다.

## 개요

두 가지 알림이 따로 동작합니다.

| 알림 | 스크립트 | 워크플로 | 실행 시각 | 받는 채팅 |
| --- | --- | --- | --- | --- |
| 환율/원자재 | `send_rate.py` | `send-rate.yml` | 매일 09:00 KST | `TELEGRAM_CHAT_ID` |
| 강수 | `weather_alert.py` | `weather-alert.yml` | 매일 06:00 KST | `WEATHER_CHAT_ID` |

### 환율/원자재 알림

[Frankfurter API](https://frankfurter.dev)로 USD, EUR, 100엔(JPY)의 원화 환율을, [gold-api.com](https://gold-api.com)으로 금, 은, 구리 가격(USD)을 가져와 텔레그램으로 보냅니다.

메시지 예시:

```
환율 (2026-10-18 기준)
USD 1달러: 1,338.31원
EUR 1유로: 1,503.02원
JPY 100엔: 846.65원

원자재 (USD / 원화)
금: $4,166.10/oz (179,258원/g)
은: $57.12/oz (2,457,568원/kg)
구리: $6.6167/lb (19,522원/kg)
```

금과 은은 트로이온스(oz)당, 구리는 파운드(lb)당 가격입니다. 괄호 안은 위 USD 환율로 환산한 원화 금액이며, 금은 g당, 은과 구리는 kg당입니다(1oz = 31.1035g, 1lb = 0.4536kg).

### 강수 알림

[Open-Meteo API](https://open-meteo.com)로 서울, 부산, 대구, 광주, 대전, 인천, 울산의 오늘 강수확률을 조회해 매일 텔레그램으로 보냅니다. 제목에 예보 날짜와 요일이 함께 표시됩니다. 강수확률은 오늘 하루 중 가장 높은 값입니다.

- 50% 이상인 도시가 있으면 해당 도시를 확률이 높은 순으로 알립니다.
- 모든 도시가 50% 미만이면 비 소식이 없다고 알립니다.

비 소식이 있을 때:

```
강수 알림 - 2026-10-18 (일)
강수확률 50% 이상인 도시
대구: 100%
서울: 80%
부산: 60%
```

비 소식이 없을 때:

```
강수 알림 - 2026-10-18 (일)
오늘은 강수확률 50% 이상인 도시가 없습니다. 비 소식 없음
```

### 구조

```
.
├── send_rate.py                  # 환율 조회 후 텔레그램 전송
├── weather_alert.py              # 강수확률 확인 후 텔레그램 전송
└── .github/workflows/
    ├── send-rate.yml             # 매일 09:00 KST(00:00 UTC)에 실행
    └── weather-alert.yml         # 매일 06:00 KST(전날 21:00 UTC)에 실행
```

- `send_rate.py`: 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다.
  - `fetch_krw_rate(base)`: Frankfurter v2 API에서 KRW 환율 조회
  - `fetch_usd_price(symbol)`: gold-api.com에서 원자재 USD 가격 조회 (`XAU` 금, `XAG` 은, `HG` 구리)
  - `send_telegram(token, chat_id, text)`: 텔레그램 Bot API로 메시지 전송
  - `main()`: 위 함수들을 조합해 환율과 원자재 메시지를 만들어 전송
- `weather_alert.py`: 마찬가지로 표준 라이브러리만 사용합니다.
  - `fetch_rain_probabilities(cities)`: Open-Meteo에서 예보 날짜와 여러 도시의 오늘 강수확률을 한 번에 조회
  - `format_date(date)`: `2026-10-18 (일)` 형식으로 날짜와 요일을 만듦
  - `build_rain_text(threshold)`: 기준 이상인 도시의 알림 메시지를 만들고, 없으면 비 소식이 없다는 메시지를 만듦
  - `main()`: 메시지를 `WEATHER_CHAT_ID`로 전송
- 두 워크플로 모두 cron 또는 수동 실행(`workflow_dispatch`)으로 시작됩니다.

### 설정

1. [@BotFather](https://t.me/BotFather)에서 봇을 만들어 토큰을 받습니다.
2. 봇에게 메시지를 한 번 보낸 뒤 `https://api.telegram.org/bot<TOKEN>/getUpdates`에서 채팅 ID를 확인합니다.
3. 저장소 Settings → Secrets and variables → Actions에 다음 시크릿을 등록합니다.

   | 이름 | 설명 |
   | --- | --- |
   | `TELEGRAM_TOKEN` | 봇 토큰 (두 알림이 함께 사용) |
   | `TELEGRAM_CHAT_ID` | 환율/원자재 알림을 받을 채팅 ID |
   | `WEATHER_CHAT_ID` | 강수 알림을 받을 채팅 ID |

4. Actions 탭에서 **Send exchange rate**, **Send rain alert** 워크플로를 수동 실행해 전송을 확인합니다.

### 강수 알림 설정

- 대상 도시는 `weather_alert.py`의 `CITIES`에서 바꿀 수 있습니다(이름, 위도, 경도).
- 기준 확률은 기본 50%이며, `RAIN_THRESHOLD` 환경 변수로 바꿀 수 있습니다. GitHub Actions에서 쓰려면 `weather-alert.yml`의 `env`에 `RAIN_THRESHOLD: ${{ vars.RAIN_THRESHOLD }}`를 추가하고 Variables 탭에 값을 등록합니다.

### 로컬 실행

```bash
export TELEGRAM_TOKEN=<봇 토큰>

# 환율/원자재
export TELEGRAM_CHAT_ID=<채팅 ID>
python send_rate.py

# 강수 알림 (기준(%)은 선택, 기본값 50)
export WEATHER_CHAT_ID=<채팅 ID>
export RAIN_THRESHOLD=70
python weather_alert.py
```

### 참고

- GitHub의 예약 실행은 몇 분 늦게 시작될 수 있습니다.
- Python 기본 User-Agent는 API에서 403으로 거부되어, 스크립트에서 User-Agent를 직접 지정합니다.
- 날씨 시간대는 `Asia/Seoul`로 고정되어 있습니다.
