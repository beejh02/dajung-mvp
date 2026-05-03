# 다정 MVP API 명세

기준 서버: FastAPI 백엔드 `backend/app`.

로컬 기본 주소는 `http://127.0.0.1:8000`입니다. 보호된 API는 `Authorization: Bearer <access_token>` 헤더를 사용합니다.

## 공통 정책

- 주문 금액은 클라이언트 입력을 신뢰하지 않고 백엔드가 메뉴/옵션 기준으로 재계산합니다.
- 더미 결제 승인 시 주문 상태 변경, 포인트 적립, 영수증 생성을 한 트랜잭션에서 처리합니다.
- 더미 결제 재시도는 idempotent하게 처리되어 결제, 포인트, 영수증이 중복 생성되지 않습니다.
- 관리자 API는 `role=admin` 사용자만 접근할 수 있습니다.
- Agent와 MCP 서버는 DB에 직접 접근하지 않고 백엔드 API만 호출합니다.

## Auth

### `POST /auth/signup`

회원가입 후 access token을 반환합니다.

```json
{
  "email": "user@example.test",
  "password": "demo-password",
  "name": "다정 사용자",
  "phone": "000-0000-0000"
}
```

응답: `TokenResponse`

### `POST /auth/login`

로그인 후 access token을 반환합니다.

```json
{
  "email": "user@example.test",
  "password": "demo-password"
}
```

### `GET /auth/me`

현재 access token의 사용자 정보를 반환합니다.

### `POST /auth/agent-handoff`

로그인된 일반 access token으로 3분 만료 일회성 handoff token을 발급합니다.

### `POST /auth/agent-session`

handoff token을 Agent용 JWT로 교환합니다. 성공한 token은 즉시 사용 처리되어 재사용할 수 없습니다.

```json
{
  "handoff_token": "<handoff token>"
}
```

## Menu

### `GET /menu`

전체 메뉴 목록을 반환합니다.

### `GET /menu/{menu_item_id}`

단일 메뉴 상세를 반환합니다.

## Orders

### `POST /orders`

로그인 사용자의 주문을 생성합니다.

```json
{
  "source": "kiosk_premium",
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

지원 `source`: `kiosk_classic`, `kiosk_guided`, `kiosk_premium`, `ai_agent`, `mcp`

### `GET /orders/my`

현재 사용자의 주문 목록을 반환합니다.

### `GET /orders/{order_id}`

현재 사용자가 접근할 수 있는 주문 상세를 반환합니다.

### `PATCH /orders/{order_id}/status`

관리자 전용 주문 상태 변경 API입니다. 서비스 계층의 허용된 상태 전이만 처리합니다.

## Payments

### `POST /payments/dummy/approve`

더미 결제를 승인합니다.

```json
{
  "order_id": 1,
  "idempotency_key": "kiosk-payment-1"
}
```

응답은 `PaymentRead`입니다. 승인 성공 시 포인트와 영수증이 함께 생성됩니다.

### `GET /payments/{payment_id}`

현재 사용자가 접근할 수 있는 결제 상세를 반환합니다.

## Points

### `GET /points/me`

현재 포인트 잔액을 반환합니다.

### `GET /points/ledger`

현재 사용자의 포인트 적립/사용 내역을 반환합니다.

## Receipts

### `GET /receipts/{receipt_id}`

현재 사용자가 접근할 수 있는 영수증을 반환합니다.

### `GET /orders/{order_id}/receipt`

주문 기준 영수증을 반환합니다.

영수증 생성 공개 API는 없습니다. 영수증은 더미 결제 승인 서비스 내부에서만 생성됩니다.

## Admin

모든 `/admin/*` API는 관리자 토큰이 필요합니다.

- `GET /admin/overview`
- `GET /admin/orders?limit=50`
- `GET /admin/orders/{order_id}`
- `GET /admin/payments?limit=100`
- `GET /admin/points?limit=100`
- `GET /admin/receipts?limit=100`

관리자 응답에는 주문 출처, 결제 상태, 포인트 적립 내역, 영수증 발급 상태가 포함됩니다.

## Agent/Internal

Agent API는 Agent가 백엔드 파이프라인을 재사용하기 위한 경계입니다.

- `GET /agent/menu`
- `GET /agent/user-context`
- `POST /agent/orders/draft`
- `POST /agent/orders/confirm`
- `POST /agent/payments/dummy/approve`

`POST /agent/orders/draft`는 가격 계산과 검증만 수행하며 주문을 저장하지 않습니다. `POST /agent/orders/confirm`은 일반 주문 생성 서비스와 같은 파이프라인으로 `source=ai_agent` 주문을 생성합니다.

## 미구현 API

- `POST /auth/logout`은 현재 구현되어 있지 않습니다. MVP에서는 클라이언트가 저장한 access token을 삭제하는 방식으로 로그아웃합니다.
- 실제 결제 PG 승인/취소/환불 API는 구현하지 않았습니다.
