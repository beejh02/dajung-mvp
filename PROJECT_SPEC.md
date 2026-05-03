# 다정(多情) MVP 프로젝트 명세

## 1. 제품 개요

다정 MVP는 햄버거 주문 키오스크, 로그인 기반 사용자 계정, 텍스트 채팅형 AI 주문 Agent, 관리자 대시보드를 하나의 주문 백엔드로 연결하는 실험용 플랫폼입니다.

핵심 검증 대상은 다음입니다.

- 서로 다른 키오스크 UI 3종 중 어떤 주문 경험이 적합한가
- 고완성도 UI 1종이 실제 주문 백엔드와 안정적으로 연동되는가
- 사용자가 한 번 로그인한 뒤 AI 채팅에서도 주문할 수 있는가
- 주문, 결제, 포인트, 영수증, 관리자 반영까지 하나의 일관된 도메인 흐름으로 처리되는가

## 2. MVP 범위

### 포함

- React 키오스크 UI 3종
- 고완성도 키오스크 UI `Dajung Premium` 1종과 FastAPI 백엔드 연동
- 회원가입/로그인용 더미 사용자 DB
- 메뉴 조회
- 장바구니/주문 생성
- 더미 결제 처리
- 포인트 적립/조회
- 영수증 생성/조회
- 관리자 대시보드 반영
- 기업 MCP 서버
- Streamlit 텍스트 채팅형 AI Agent
- `models/gemma-4-26b-a4b-it` 목표 모델을 향한 `LLMProvider` 기반 Agent 응답 구조
- API Key 없이 실행 가능한 `StubLLMProvider` 기반 demo mode
- RAG 확장을 고려한 폴더/인터페이스 구조
- SQLite + SQLModel 기반 로컬 DB
- JWT + 일회성 handoff token 기반 인증 흐름
- 더미 DB 조회 기반 개인화 시나리오

### 제외

- 실제 결제 PG 연동
- 실사용 개인정보/민감정보 처리
- 음성 입력
- STT
- TTS
- 실제 RAG 파이프라인
- 프로덕션 수준의 권한/감사/보안 체계

## 3. 시스템 구성

```text
React Kiosk App
  ├─ Login / Signup
  ├─ Kiosk UI A: Classic Grid
  ├─ Kiosk UI B: Guided Order
  ├─ Kiosk UI C: Dajung Premium
  └─ AI Chat Entry

React Admin App
  └─ Admin Dashboard

FastAPI Backend
  ├─ Auth API
  ├─ Menu API
  ├─ Order API
  ├─ Dummy Payment API
  ├─ Points API
  ├─ Receipt API
  ├─ Admin API
  └─ Agent/Internal API

Streamlit Agent
  ├─ Text Chat UI
  ├─ Dajung Session Handoff
  ├─ Tool Calling Layer
  ├─ LLMProvider Interface
  └─ StubLLMProvider Demo Mode

Enterprise MCP Server
  ├─ FastAPI Fake MCP HTTP API
  ├─ MCP-like Tool Schemas
  ├─ Tool Adapter Layer
  └─ Business Tools

SQLite Dummy DB
  ├─ users
  ├─ agent_handoff_tokens
  ├─ menu_items
  ├─ orders
  ├─ order_items
  ├─ payments
  ├─ point_ledger
  └─ receipts
```

## 4. 현재 폴더 구조

Phase 11 기준 실제 구현 구조는 다음과 같습니다. 일부 초기 계획의 폴더명은 구현 과정에서 단순화되었습니다.

```text
dajung-mvp/
  README.md
  PROJECT_SPEC.md
  TODO.md

  frontend/
    kiosk/
      src/
        pages/
          auth/
          kiosk/
        components/
          common/
        lib/
          api/
          auth/
          formatting/
        styles/

    admin/
      src/
        pages/
          dashboard/
          orders/
        components/
          orders/
          common/
        lib/
          api/
          auth/
          formatting/
        styles/

  shared/
    frontend-client/
      src/
        api/
        auth/
        types/
        formatting/

    dummy-data/
      users.json
      menus.json
      order_history.json
      preferences.json
      rag_contexts.json

    docs/
      API_SPEC.md
      AGENT_TOOLS.md
      MVP_DEMO.md

  backend/
    app/
      app/
        main.py
        core/
        db/
        models/
        schemas/
        routers/
        services/
      tests/

  scripts/
    phase10_integration_check.py
```

MCP tool 상세 문서는 `mcp-server/app/docs/mcp_tools.md`에 둡니다.

초기 계획에서 `auth-flow.md`, `order-flow.md`, `rag-extension-plan.md`처럼 분리하려던 문서는 Phase 11에서 `API_SPEC.md`, `AGENT_TOOLS.md`, `MVP_DEMO.md`로 통합 정리했습니다.

```text
mcp-server/
  app/
    app/
      main.py
      adapter.py
      backend_client.py
      schemas.py
      tools/
    docs/
      mcp_tools.md

ai-agent/
  app/
    app.py
    config.py
    model_client.py
    session_handoff.py
    backend_client.py
    tools/
    prompts/
```

`frontend/kiosk`와 `frontend/admin`의 `lib/api`와 `lib/auth`는 앱별 래퍼만 두고, 실제 HTTP 클라이언트, 인증 토큰 처리, 공통 타입은 `shared/frontend-client`에서 공유합니다.

## 5. 인증 및 세션 설계

### 기본 방침

- 다정 플랫폼의 로그인은 FastAPI 백엔드가 담당합니다.
- MVP에서는 더미 사용자 DB를 사용합니다.
- 비밀번호는 평문 저장을 피하고 해시 저장을 기본으로 합니다.
- 로그인 성공 시 백엔드는 JWT 액세스 토큰을 발급합니다.
- 관리자 API는 `role=admin` 사용자만 접근할 수 있습니다.

### AI 채팅 단일 로그인 흐름

Streamlit 앱은 React 앱과 실행 포트가 다를 수 있으므로, 단순히 브라우저 로컬 스토리지를 공유하는 방식에 의존하지 않습니다.

권장 흐름:

1. 사용자가 React 다정 플랫폼에서 로그인합니다.
2. React 앱이 백엔드에 AI 채팅 진입용 일회성 handoff token을 요청합니다.
3. 사용자는 AI 채팅 화면으로 이동합니다.
4. Streamlit 앱은 URL 또는 초기 요청으로 전달된 handoff token을 백엔드에 교환 요청합니다.
5. 백엔드는 유효한 handoff token을 확인한 뒤 Agent용 사용자 세션을 발급합니다.
6. Agent는 해당 세션으로 메뉴 조회, 주문 생성, 결제, 영수증 조회 API를 호출합니다.

이 방식은 "한 번 로그인하면 AI 채팅으로 주문 가능"이라는 요구사항을 만족하면서, Streamlit과 React가 느슨하게 결합되도록 합니다.

Phase 11 기준으로 handoff token API와 Streamlit token 수신은 구현되어 있습니다. React 키오스크에서 Streamlit으로 자동 이동하는 별도 버튼은 구현되어 있지 않으므로, 시연에서는 API로 발급한 handoff token을 Streamlit 사이드바 또는 URL query로 전달합니다.

### handoff token 정책

- `POST /auth/agent-handoff`는 로그인된 사용자에게 3분 동안 유효한 일회성 token을 발급합니다.
- handoff token은 서버에 원문이 아닌 해시로 저장합니다.
- `POST /auth/agent-session`은 token이 유효하고, 만료되지 않았고, 아직 사용되지 않은 경우에만 Agent용 JWT를 발급합니다.
- handoff token은 성공적으로 교환되는 즉시 사용 처리되어 재사용할 수 없습니다.
- 만료, 재사용, 사용자 불일치, 위조 token은 모두 인증 실패로 처리합니다.

## 6. 주요 도메인 모델

### User

- `id`
- `email`
- `password_hash`
- `name`
- `phone`
- `role`: `user` 또는 `admin`
- `points_balance`
- `created_at`

### AgentHandoffToken

- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `used_at`
- `created_at`

### MenuItem

- `id`
- `name`
- `category`
- `description`
- `price`
- `image_url`
- `is_available`
- `options`

`options`는 다음 구조를 따릅니다.

- `id`
- `name`
- `required`
- `min_select`
- `max_select`
- `choices`

각 `choice`는 다음 필드를 가집니다.

- `id`
- `name`
- `price_delta`
- `is_available`

### Order

- `id`
- `user_id`
- `source`
- `status`
- `subtotal_amount`
- `discount_amount`
- `total_amount`
- `created_at`
- `updated_at`

`source` 예시:

- `kiosk_classic`
- `kiosk_guided`
- `kiosk_premium`
- `ai_agent`

`status` 예시:

- `draft`
- `pending_payment`
- `paid`
- `completed`
- `cancelled`
- `failed`

### OrderItem

- `id`
- `order_id`
- `menu_item_id`
- `name_snapshot`
- `unit_price`
- `quantity`
- `selected_options`
- `line_total`

### Payment

- `id`
- `order_id`
- `status`
- `method`
- `approved_amount`
- `dummy_approval_code`
- `approved_at`

`order_id`는 주문당 하나의 승인 결제만 존재하도록 유니크 제약을 둡니다.

### PointLedger

- `id`
- `user_id`
- `order_id`
- `type`
- `amount`
- `balance_after`
- `created_at`

주문 결제 적립 ledger는 `order_id + type=earn` 기준으로 중복 생성되지 않게 합니다.

### Receipt

- `id`
- `order_id`
- `receipt_number`
- `content`
- `issued_at`

`order_id`는 주문당 하나의 영수증만 존재하도록 유니크 제약을 둡니다.

### 명시적 enum

- `OrderStatus`: `draft`, `pending_payment`, `paid`, `completed`, `cancelled`, `failed`
- `PaymentStatus`: `pending`, `approved`, `failed`, `refunded`
- `OrderSource`: `kiosk_classic`, `kiosk_guided`, `kiosk_premium`, `ai_agent`, `mcp`
- `PointLedgerType`: `earn`, `spend`, `adjust`

상태 전이는 서비스 계층에서만 처리합니다. `PATCH /orders/{order_id}/status`는 관리자/내부 전용이며 허용된 상태 전이만 통과시킵니다.

## 7. 주요 API 설계

### Auth

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/agent-handoff`
- `POST /auth/agent-session`

`POST /auth/logout`은 구현되어 있지 않습니다. MVP에서는 클라이언트가 저장한 token을 삭제하는 방식으로 로그아웃합니다.

### Menu

- `GET /menu`
- `GET /menu/{menu_item_id}`

### Orders

- `POST /orders`
- `GET /orders/{order_id}`
- `GET /orders/my`
- `PATCH /orders/{order_id}/status`

`POST /orders`는 클라이언트가 보낸 가격을 신뢰하지 않습니다. 백엔드는 메뉴와 옵션 seed 데이터를 기준으로 가격, 할인, 총액을 다시 계산합니다.

`PATCH /orders/{order_id}/status`는 관리자 또는 내부 호출만 사용할 수 있으며, 허용된 상태 전이만 처리합니다.

### Payments

- `POST /payments/dummy/approve`
- `GET /payments/{payment_id}`

`POST /payments/dummy/approve`는 idempotent하게 동작합니다. 같은 주문에 대해 재시도해도 승인 결제, 포인트 적립, 영수증이 중복 생성되지 않아야 합니다.

### Points

- `GET /points/me`
- `GET /points/ledger`

### Receipts

- `GET /receipts/{receipt_id}`
- `GET /orders/{order_id}/receipt`

영수증 생성은 결제 승인 서비스 내부에서만 수행합니다. 외부 클라이언트가 영수증을 임의로 생성하는 공개 API는 두지 않습니다.

### Admin

- `GET /admin/overview`
- `GET /admin/orders`
- `GET /admin/orders/{order_id}`
- `GET /admin/payments`
- `GET /admin/points`
- `GET /admin/receipts`

모든 `/admin/*` API는 `role=admin` 사용자만 접근할 수 있습니다.

### Agent/Internal

- `POST /agent/orders/draft`
- `POST /agent/orders/confirm`
- `POST /agent/payments/dummy/approve`
- `GET /agent/menu`
- `GET /agent/user-context`

Agent/Internal API는 Agent가 DB를 직접 읽거나 쓰지 않도록 하는 백엔드 경계입니다. `POST /agent/orders/draft`는 검증과 가격 계산만 수행하고, `POST /agent/orders/confirm`은 일반 주문 생성 서비스와 같은 파이프라인을 호출합니다.

## 8. 주문 처리 흐름

### 키오스크 주문

1. React 키오스크가 메뉴를 조회합니다.
2. 사용자가 메뉴와 옵션을 선택합니다.
3. React 앱이 `POST /orders`로 주문을 생성합니다.
4. React 앱이 `POST /payments/dummy/approve`로 더미 결제를 요청합니다.
5. 백엔드는 결제 승인, 주문 상태 변경, 포인트 적립, 영수증 생성을 단일 트랜잭션으로 처리합니다.
6. 관리자 대시보드 API가 최신 주문/매출/포인트 데이터를 반환합니다.

### AI Agent 주문

1. 사용자는 로그인된 상태에서 AI 채팅으로 진입합니다.
2. Agent가 사용자 요청을 해석합니다.
3. Agent가 메뉴 조회 도구를 호출합니다.
4. Agent가 주문 초안을 만들고 사용자에게 확인을 요청합니다.
5. 사용자가 확인하면 Agent가 주문 확정 API를 호출합니다.
6. Agent가 더미 결제를 진행합니다.
7. Agent가 영수증과 적립 포인트를 사용자에게 안내합니다.
8. 관리자 대시보드에는 키오스크 주문과 같은 방식으로 반영됩니다.

AI Agent는 자체 DB 접근 없이 백엔드 API만 호출합니다. Agent 주문도 일반 주문 서비스와 같은 가격 계산, 결제 승인, 포인트 적립, 영수증 생성 파이프라인을 사용합니다.

## 9. AI Agent 설계

### 모델

- 목표 모델 식별자: `models/gemma-4-26b-a4b-it`
- 초기 MVP에서는 실제 모델 API를 바로 연결하지 않고 `LLMProvider` 추상 인터페이스로 모델 호출 경계를 분리합니다.
- 초기 구현은 `StubLLMProvider`로 시작합니다.
- `StubLLMProvider`는 사용자 입력에 따라 미리 정의된 intent JSON을 반환해 주문 E2E 흐름을 검증합니다.
- API Key가 없어도 Streamlit Agent는 demo mode로 실행 가능해야 합니다.
- 추후 실제 provider는 Google Gemini API 또는 Cloudflare Workers AI Provider로 교체할 수 있게 합니다.
- 모델 클라이언트는 provider 교체가 가능하도록 `generate_response`, intent/tool 호출 요청 파싱, 오류 변환을 인터페이스로 분리합니다.

### Agent 도구

- `get_menu`
- `get_user_context`
- `create_order_draft`
- `confirm_order`
- `approve_dummy_payment`
- `get_receipt`
- `get_points_balance`

### 대화 정책

- 주문 전에는 메뉴명, 수량, 필수 옵션을 확인합니다.
- 결제 전에는 총액과 주문 구성을 사용자에게 재확인합니다.
- 재고가 없거나 메뉴가 비활성화된 경우 대체 메뉴를 제안합니다.
- 모델 출력이 주문 JSON으로 검증되지 않으면 주문을 진행하지 않고 필요한 정보를 다시 묻습니다.
- 실제 결제가 아닌 더미 결제임을 UI 또는 응답에서 명확히 표시합니다.
- RAG를 사용하지 않으며 메뉴/주문 정보는 백엔드 API를 신뢰합니다.
- 개인화 시나리오는 현재 더미 DB에서 조회한 사용자 컨텍스트를 기반으로 구현합니다.

## 10. MCP 서버 설계

기업 MCP 서버는 다정의 내부 비즈니스 도구를 표준화된 MCP 도구 형태로 노출합니다. 초기 MVP에서는 공식 MCP SDK를 바로 사용하지 않고 FastAPI 기반 fake MCP HTTP 서버로 시작합니다.

MVP fake MCP 서버는 비즈니스 로직을 직접 구현하지 않고 FastAPI 백엔드 API를 호출하는 얇은 어댑터로 둡니다. Tool 이름과 입출력 구조는 실제 MCP Tool처럼 설계하고, tool 로직은 `mcp-server/app/app/tools/` 아래에 분리합니다. HTTP 엔드포인트와 tool 실행 계층은 나중에 공식 Python MCP SDK로 교체할 수 있도록 어댑터 경계를 유지합니다.

### MVP 필수 MCP Tools

- `dajung.get_menu`
- `dajung.submit_order`
- `dajung.approve_dummy_payment`
- `dajung.get_receipt`
- `dajung.list_recent_orders`

### 확장 후보 MCP Tools

- `dajung.get_user_profile`
- `dajung.create_order_draft`
- `dajung.get_admin_overview`

### MCP Resources 초안

- `dajung://menu`
- `dajung://admin/overview`
- `dajung://orders/recent`

각 MCP tool은 입력/출력 스키마를 명시하고, 백엔드 API 오류를 MCP 오류 응답으로 변환합니다.

## 11. 관리자 대시보드

관리자 대시보드는 MVP에서 운영 상태를 확인하는 용도입니다. 모든 관리자 화면과 API는 `role=admin` 사용자만 접근할 수 있습니다.

필수 화면:

- 오늘 주문 수
- 오늘 더미 매출
- 최근 주문 목록
- 결제 상태
- 포인트 적립 내역
- 영수증 발급 상태
- 주문 출처별 비중: 키오스크 UI, AI Agent

## 12. RAG 확장 계획

MVP에서는 RAG를 구현하지 않습니다. 다만 다음 확장을 고려해 인터페이스와 폴더를 분리합니다.

- `retrieval/` 또는 `knowledge/` 모듈을 Agent 내부에 나중에 추가 가능하게 유지
- Agent 도구 호출과 지식 검색 호출을 분리
- 메뉴, 프로모션, 정책 문서는 추후 벡터 DB로 이전 가능하도록 문서 원천을 구분
- 현재 Agent는 백엔드 API, 더미 DB 기반 사용자 컨텍스트, 정적 시스템 프롬프트만 사용

## 13. 테스트 계획

### 백엔드 단위 테스트

- 메뉴/옵션 기반 가격 재계산
- 필수 옵션, 선택 개수, 비활성 메뉴/옵션 검증
- 주문 상태 전이 허용/거부
- 더미 결제 승인 idempotency
- 포인트 적립과 영수증 중복 생성 방지

### 인증 테스트

- 회원가입, 로그인, 현재 사용자 조회
- handoff token 3분 만료, 1회 사용, 재사용 방지
- 잘못된 handoff token 거부
- 관리자 API의 일반 사용자 접근 거부

### 통합 테스트

- 회원가입부터 `Dajung Premium` 키오스크 주문 완료까지
- 로그인부터 AI 채팅 주문 완료까지
- 더미 결제 후 포인트 적립과 영수증 생성 확인
- 관리자 대시보드에 키오스크와 AI Agent 주문이 함께 반영되는지 확인

### Agent/MCP 테스트

- Agent가 결제 전 사용자 재확인을 수행하는지 확인
- 품절/비활성 메뉴 요청 시 대체 메뉴를 제안하는지 확인
- 모델 출력 JSON 검증 실패 시 재질문하는지 확인
- MCP tool별 입력/출력 스키마와 백엔드 API 실패 변환을 확인

### Phase 10 통합 검증 결과

Phase 10에서 다음 검증을 완료했습니다.

- 회원가입부터 `Dajung Premium` 키오스크 주문 완료까지 통과
- 로그인부터 AI Agent handoff token 교환과 채팅 주문 완료까지 통과
- 더미 결제 후 포인트 적립과 영수증 생성 확인
- 관리자 대시보드에 키오스크 주문과 AI Agent 주문이 함께 반영되는지 확인
- 비로그인 주문 제한, handoff token 만료/재사용 방지, 관리자 API 일반 사용자 접근 거부 확인
- 더미 결제 재시도 시 결제/포인트/영수증 중복 미생성 확인
- MCP tool 입력/출력 스키마와 백엔드 실패 응답 변환 확인

반복 실행용 검증 스크립트는 `scripts/phase10_integration_check.py`입니다.

## 14. 성공 기준

- React 앱에서 키오스크 UI 3종을 전환해 볼 수 있습니다.
- 고완성도 키오스크 UI에서 실제 백엔드 메뉴를 조회하고 주문할 수 있습니다.
- 회원가입/로그인 후 주문이 사용자 계정에 연결됩니다.
- 더미 결제 후 포인트와 영수증이 생성됩니다.
- 관리자 대시보드에서 주문/결제/포인트/영수증 상태가 확인됩니다.
- Streamlit AI Agent가 로그인 세션을 기반으로 주문을 생성할 수 있습니다.
- Streamlit AI Agent가 API Key 없이 `StubLLMProvider` demo mode로 주문 흐름을 시연할 수 있습니다.
- MCP 서버가 최소한 메뉴 조회와 주문 관련 도구를 제공합니다.
- RAG, 음성, STT, TTS는 MVP 범위에서 제외되어 있습니다.

## 15. MVP 제한사항

- 실제 결제 PG 연동은 없습니다.
- 실제 LLM API 호출은 없습니다. Google Gemini API와 Cloudflare Workers AI provider는 교체 지점만 준비되어 있습니다.
- 실제 RAG 검색은 없습니다. `shared/dummy-data/rag_contexts.json`은 추후 확장용 원천 텍스트입니다.
- 음성 입력, STT, TTS는 없습니다.
- React 키오스크에서 AI 채팅으로 자동 이동하는 UI는 없습니다.
- Fake MCP HTTP 서버는 공식 MCP SDK 서버가 아닙니다.
