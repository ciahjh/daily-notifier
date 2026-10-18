# rate-notifier

환율과 주요 원자재(금, 은, 구리) 가격을 매일 텔레그램으로 알려 주는 봇입니다.

## 개요

[Frankfurter API](https://frankfurter.dev)로 USD, EUR, 100엔(JPY)의 원화 환율을, [gold-api.com](https://gold-api.com)으로 금, 은, 구리 가격(USD)을 가져와 텔레그램으로 보냅니다. GitHub Actions가 매일 한국 시간 오전 9시에 실행합니다.

메시지 예시:

```
환율 (2026-10-18 기준)
USD 1달러: 1,338.31원
EUR 1유로: 1,503.02원
JPY 100엔: 846.65원

원자재 (USD, 원화 환산)
금: $4,166.10/oz (5,575,533원)
은: $57.12/oz (76,439원)
구리: $6.6167/lb (8,855원)
```

금과 은은 트로이온스(oz)당, 구리는 파운드(lb)당 가격입니다. 괄호 안은 같은 단위의 가격을 위 USD 환율로 환산한 원화 금액입니다.

### 구조

```
.
├── send_rate.py                  # 환율 조회 후 텔레그램 전송
└── .github/workflows/
    └── send-rate.yml             # 매일 09:00 KST(00:00 UTC)에 실행
```

- `send_rate.py`: 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다.
  - `fetch_krw_rate(base)`: Frankfurter v2 API에서 KRW 환율 조회
  - `fetch_usd_price(symbol)`: gold-api.com에서 원자재 USD 가격 조회 (`XAU` 금, `XAG` 은, `HG` 구리)
  - `send_telegram(token, chat_id, text)`: 텔레그램 Bot API로 메시지 전송
  - `main()`: 위 함수들을 조합해 환율과 원자재 메시지를 만들어 전송
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

### 로컬 실행

```bash
export TELEGRAM_TOKEN=<봇 토큰>
export TELEGRAM_CHAT_ID=<채팅 ID>
python send_rate.py
```

### 참고

- GitHub의 예약 실행은 몇 분 늦게 시작될 수 있습니다.
- Python 기본 User-Agent는 API에서 403으로 거부되어, 스크립트에서 User-Agent를 직접 지정합니다.
