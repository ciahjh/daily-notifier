# claude-playground

A playground for experimenting with Claude Code and MCP

## 환율 텔레그램 알림

[Frankfurter API](https://frankfurter.dev)로 USD, EUR, 100엔(JPY)의 원화 환율을 가져와 텔레그램으로 보냅니다. GitHub Actions가 매일 한국 시간 오전 9시에 실행합니다.

메시지 예시:

```
환율 (2026-10-18 기준)
USD 1달러: 1,338.31원
EUR 1유로: 1,503.02원
JPY 100엔: 846.65원
```

### 구조

```
.
├── send_rate.py                  # 환율 조회 후 텔레그램 전송
└── .github/workflows/
    └── send-rate.yml             # 매일 09:00 KST(00:00 UTC)에 실행
```

- `send_rate.py`: 표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다.
  - `fetch_krw_rate(base)`: Frankfurter v2 API에서 KRW 환율 조회
  - `send_telegram(token, chat_id, text)`: 텔레그램 Bot API로 메시지 전송
  - `main()`: 위 둘을 조합해 USD, EUR, JPY(100엔 환산) 메시지 생성 및 전송
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
