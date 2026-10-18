# rate-notifier

날씨, 환율, 주요 원자재(금, 은, 구리) 가격을 매일 텔레그램으로 알려 주는 봇입니다.

## 개요

[Open-Meteo API](https://open-meteo.com)로 오늘의 날씨를, [Frankfurter API](https://frankfurter.dev)로 USD, EUR, 100엔(JPY)의 원화 환율을, [gold-api.com](https://gold-api.com)으로 금, 은, 구리 가격(USD)을 가져와 텔레그램으로 보냅니다. GitHub Actions가 매일 한국 시간 오전 9시에 실행합니다.

메시지 예시:

```
날씨 (서울)
맑음, 현재 15.2°C (체감 15.4°C)
최저 14.6°C / 최고 21.0°C
강수확률: 100%

환율 (2026-10-18 기준)
USD 1달러: 1,338.31원
EUR 1유로: 1,503.02원
JPY 100엔: 846.65원

원자재 (USD / 원화)
금: $4,166.10/oz (179,258원/g)
은: $57.12/oz (2,457,568원/kg)
구리: $6.6167/lb (19,522원/kg)
```

날씨는 현재 기온과 체감 온도, 오늘의 최저/최고 기온, 하루 중 최대 강수확률입니다. 금과 은은 트로이온스(oz)당, 구리는 파운드(lb)당 가격입니다. 괄호 안은 위 USD 환율로 환산한 원화 금액이며, 금은 g당, 은과 구리는 kg당입니다(1oz = 31.1035g, 1lb = 0.4536kg).

### 구조

```
.
├── send_rate.py                  # 날씨, 환율 조회 후 텔레그램 전송
└── .github/workflows/
    └── send-rate.yml             # 매일 09:00 KST(00:00 UTC)에 실행
```

- `send_rate.py`: 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다.
  - `fetch_krw_rate(base)`: Frankfurter v2 API에서 KRW 환율 조회
  - `fetch_usd_price(symbol)`: gold-api.com에서 원자재 USD 가격 조회 (`XAU` 금, `XAG` 은, `HG` 구리)
  - `fetch_weather(latitude, longitude)`: Open-Meteo에서 현재 날씨와 오늘 예보 조회
  - `send_telegram(token, chat_id, text)`: 텔레그램 Bot API로 메시지 전송
  - `build_text()`: 위 함수들을 조합해 날씨, 환율, 원자재 메시지를 만듦
  - `main()`: 메시지를 만들어 전송
- `send-rate.yml`: cron 또는 수동 실행(`workflow_dispatch`)으로 시작됩니다.

### 설정

1. [@BotFather](https://t.me/BotFather)에서 봇을 만들어 토큰을 받습니다.
2. 봇에게 메시지를 한 번 보낸 뒤 `https://api.telegram.org/bot<TOKEN>/getUpdates`에서 채팅 ID를 확인합니다.
3. 저장소 Settings → Secrets and variables → Actions에 다음 시크릿을 등록합니다.

   | 이름 | 설명 |
   | --- | --- |
   | `TELEGRAM_TOKEN` | 봇 토큰 |
   | `TELEGRAM_CHAT_ID` | 메시지를 받을 채팅 ID |

4. Actions 탭에서 **Send exchange rate** 워크플로를 수동 실행해 전송을 확인합니다.

### 날씨 지역 변경

기본값은 서울입니다. 다음 환경 변수로 지역을 바꿀 수 있으며, 모두 선택 사항입니다.

| 이름 | 설명 | 기본값 |
| --- | --- | --- |
| `WEATHER_CITY` | 메시지에 표시할 지역 이름 | `서울` |
| `WEATHER_LATITUDE` | 위도 | `37.5665` |
| `WEATHER_LONGITUDE` | 경도 | `126.9780` |

GitHub Actions에서 쓰려면 Variables 탭에 같은 이름으로 등록하고, `send-rate.yml`의 `env`에 `WEATHER_CITY: ${{ vars.WEATHER_CITY }}`처럼 추가하면 됩니다.

### 로컬 실행

```bash
export TELEGRAM_TOKEN=<봇 토큰>
export TELEGRAM_CHAT_ID=<채팅 ID>
# 선택: 지역 변경 (기본값은 서울)
export WEATHER_CITY=부산
export WEATHER_LATITUDE=35.1796
export WEATHER_LONGITUDE=129.0756
python send_rate.py
```

### 참고

- GitHub의 예약 실행은 몇 분 늦게 시작될 수 있습니다.
- Python 기본 User-Agent는 API에서 403으로 거부되어, 스크립트에서 User-Agent를 직접 지정합니다.
- 날씨 시간대는 `Asia/Seoul`로 고정되어 있습니다.
