# 다정 Fake MCP HTTP Tool 명세

이 서버는 공식 MCP SDK를 사용하지 않는 MVP용 HTTP 어댑터입니다. HTTP 요청을 MCP tool 호출과 비슷한 형태로 받아 기존 FastAPI 백엔드 API를 호출합니다. 주문, 결제, 영수증, 최근 주문 처리는 MCP 서버가 직접 구현하지 않고 백엔드 파이프라인을 그대로 사용합니다.

## 실행 방법

백엔드를 먼저 실행한 뒤 MCP 서버를 실행합니다.

```powershell
cd mcp-server/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
$env:BACKEND_API_BASE_URL = "http://127.0.0.1:8000"
.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8010
```

확인:

```powershell
Invoke-RestMethod http://127.0.0.1:8010/health
Invoke-RestMethod http://127.0.0.1:8010/mcp/tools
```

## HTTP API

### `GET /mcp/tools`

등록된 tool 이름, 설명, 입력 스키마, 출력 스키마를 반환합니다.

### `POST /mcp/tools/call`

```http
POST /mcp/tools/call
Authorization: Bearer <다정 백엔드 access token>
Content-Type: application/json
```

```json
{
  "name": "dajung.get_menu",
  "arguments": {}
}
```

성공 응답:

```json
{
  "ok": true,
  "tool": "dajung.get_menu",
  "content": {
    "items": []
  },
  "error": null
}
```

백엔드 오류 변환 응답:

```json
{
  "ok": false,
  "tool": "dajung.list_recent_orders",
  "content": null,
  "error": {
    "code": "backend_api_error",
    "message": "백엔드 API 오류: 관리자 권한이 필요합니다.",
    "backend_status": 403,
    "detail": "관리자 권한이 필요합니다."
  }
}
```

요청 형식 오류 응답:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_request",
    "message": "요청 형식이 올바르지 않습니다.",
    "detail": []
  }
}
```

## Tool 목록

### `dajung.get_menu`

- 입력: `{}`
- 출력: `{ "items": [...] }`
- 백엔드 호출: `GET /menu`
- 인증: 필요 없음

### `dajung.submit_order`

- 입력:

```json
{
  "source": "mcp",
  "items": [
    {
      "menu_item_id": "menu_dajung_teriyaki_set",
      "quantity": 1,
      "selected_options": [
        {
          "group_id": "og_dajung_teriyaki_drink",
          "choice_ids": ["opt_dajung_teriyaki_drink_cola"]
        },
        {
          "group_id": "og_dajung_teriyaki_side",
          "choice_ids": ["opt_dajung_teriyaki_side_fries"]
        }
      ]
    }
  ]
}
```

- 출력: 백엔드 `OrderRead`
- 백엔드 호출: `POST /orders`
- 인증: 일반 사용자, Agent, 관리자 token 필요
- 비고: `source`가 없으면 `mcp`로 전달합니다.

### `dajung.approve_dummy_payment`

- 입력:

```json
{
  "order_id": 1,
  "idempotency_key": "mcp-payment-1"
}
```

- 출력: 백엔드 `PaymentRead`
- 백엔드 호출: `POST /payments/dummy/approve`
- 인증: 주문 소유자 또는 관리자 token 필요

### `dajung.get_receipt`

- 입력:

```json
{
  "order_id": 1
}
```

- 출력: 백엔드 `ReceiptRead`
- 백엔드 호출: `GET /orders/{order_id}/receipt`
- 인증: 주문 소유자 또는 관리자 token 필요

### `dajung.list_recent_orders`

- 입력:

```json
{
  "limit": 10
}
```

- 출력: `{ "orders": [...] }`
- 백엔드 호출: `GET /admin/orders?limit=...`
- 인증: 관리자 token 필요
- 제한: `limit`은 1부터 100까지로 보정합니다.

## 제한사항

- 공식 MCP SDK 서버가 아닙니다.
- MCP resources와 prompts는 구현하지 않았습니다.
- 비즈니스 규칙은 MCP 서버가 직접 처리하지 않습니다.
- 백엔드가 꺼져 있으면 tool 호출은 `backend_api_error`로 실패합니다.
- 실제 결제 PG, RAG, 음성, STT, TTS와 연결하지 않습니다.

## 공식 MCP SDK 전환 지점

추후 공식 Python MCP SDK를 도입할 때는 `app/tools/*`의 tool handler와 schema를 유지하고, `app/adapter.py`의 HTTP adapter만 SDK server adapter로 교체합니다. `BackendClient`는 그대로 재사용해 MCP 서버가 비즈니스 로직을 직접 소유하지 않도록 유지합니다.
