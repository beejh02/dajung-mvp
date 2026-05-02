# 다정 Fake MCP HTTP Tool 명세

이 서버는 공식 MCP SDK를 사용하지 않는 MVP용 HTTP 어댑터입니다. HTTP 요청을 MCP tool 호출과 비슷한 형태로 받아 기존 FastAPI 백엔드 API를 호출합니다. 주문, 결제, 영수증, 최근 주문 처리는 MCP 서버가 직접 구현하지 않고 백엔드 파이프라인을 그대로 사용합니다.

## 공통 호출 방식

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

응답은 항상 tool 호출 결과 형태를 따릅니다.

```json
{
  "ok": true,
  "tool": "dajung.get_menu",
  "content": {}
}
```

오류는 다음 형태로 변환됩니다.

```json
{
  "ok": false,
  "tool": "dajung.submit_order",
  "error": {
    "code": "backend_api_error",
    "message": "백엔드 API 오류: ...",
    "backend_status": 400,
    "detail": "..."
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
        }
      ]
    }
  ]
}
```

- 출력: 백엔드 `OrderRead`
- 백엔드 호출: `POST /orders`
- 인증: 일반 사용자 또는 Agent 토큰 필요

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
- 인증: 주문 소유자 또는 관리자 토큰 필요

### `dajung.get_receipt`

- 입력:

```json
{
  "order_id": 1
}
```

- 출력: 백엔드 `ReceiptRead`
- 백엔드 호출: `GET /orders/{order_id}/receipt`
- 인증: 주문 소유자 또는 관리자 토큰 필요

### `dajung.list_recent_orders`

- 입력:

```json
{
  "limit": 10
}
```

- 출력: `{ "orders": [...] }`
- 백엔드 호출: `GET /admin/orders?limit=...`
- 인증: 관리자 토큰 필요

## 공식 MCP SDK 전환 지점

추후 공식 Python MCP SDK를 도입할 때는 `app/tools/*`의 tool handler와 schema를 유지하고, `app/adapter.py`의 HTTP adapter만 SDK server adapter로 교체합니다. `BackendClient`는 그대로 재사용해 MCP 서버가 비즈니스 로직을 직접 소유하지 않도록 유지합니다.
