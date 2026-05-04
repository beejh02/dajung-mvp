# 다정 AI Agent 도구 명세

Streamlit AI Agent는 `ai-agent/app`에서 실행됩니다. Agent는 DB를 직접 읽거나 쓰지 않고 FastAPI 백엔드 API만 호출합니다.

## 실행 방식

```powershell
cd ai-agent/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
$env:BACKEND_API_BASE_URL = "http://127.0.0.1:8000"
.venv\Scripts\streamlit.exe run app.py --server.address 127.0.0.1 --server.port 8502
```

세션 연결 방식:

- 백엔드 `POST /auth/agent-handoff`로 handoff token 발급
- Streamlit 사이드바에 token 입력
- 또는 `http://127.0.0.1:8502/?handoff_token=<token>`으로 진입
- handoff token이 없으면 사이드바에서 seed 데모 사용자 로그인, 이메일 로그인, 또는 JWT 직접 입력으로 Agent 세션 연결

## 모델 설정

기본 설정은 API Key 없이 실행 가능한 demo mode입니다.

```text
LLM_PROVIDER=stub
AGENT_DEMO_MODE=true
LLM_MODEL=models/gemma-4-26b-a4b-it
GEMINI_API_KEY=
```

구현된 provider 경계:

- `LLMProvider`: 모델 호출 추상 인터페이스
- `StubLLMProvider`: 사용자 입력을 규칙 기반 intent JSON으로 변환하는 demo provider
- `GoogleGeminiProvider`: `GEMINI_API_KEY`가 있을 때 Gemini REST API로 intent JSON 생성을 호출
- `CloudflareWorkersAIProvider`: 교체 지점만 준비되어 있으며 실제 API 호출은 미구현

`LLM_PROVIDER`가 실제 provider로 설정되어도 필요한 API Key가 없고 `AGENT_DEMO_MODE=true`이면 `StubLLMProvider`로 fallback합니다.

## Intent action

`StubLLMProvider`는 다음 action을 반환할 수 있습니다.

- `get_menu`
- `get_user_context`
- `create_order_draft`
- `confirm_order`
- `get_receipt`
- `get_points_balance`
- `ask_clarification`
- `unavailable_menu`

검증되지 않은 intent JSON은 주문을 진행하지 않고 재질문 메시지로 처리합니다.

## Agent 도구

### `get_menu`

- 백엔드 호출: `GET /agent/menu`
- 용도: 주문 가능한 메뉴 목록 조회

### `get_user_context`

- 백엔드 호출: `GET /agent/user-context`
- 용도: 사용자 정보, 포인트, 최근 주문 조회

### `create_order_draft`

- 백엔드 호출: `POST /agent/orders/draft`
- 용도: 주문 저장 전 가격 계산과 옵션 검증
- 결과: 주문 초안과 총액을 사용자에게 보여주고 결제 전 확인을 요구

### `confirm_order`

- 백엔드 호출: `POST /agent/orders/confirm`
- 용도: 사용자가 확인한 주문을 `source=ai_agent` 주문으로 저장

### `approve_dummy_payment`

- 백엔드 호출: `POST /agent/payments/dummy/approve`
- 용도: Agent 주문의 더미 결제 승인
- 결과: 결제, 포인트 잔액, 영수증을 함께 안내

### `get_receipt`

- 백엔드 호출: `GET /orders/{order_id}/receipt`
- 용도: 주문 영수증 조회

### `get_points_balance`

- 백엔드 호출: `GET /points/me`
- 용도: 현재 포인트 잔액 조회

## 대화 정책

- 결제 전에는 주문 구성과 총액을 확인합니다.
- 비활성 메뉴나 옵션이 요청되면 대체 메뉴를 제안합니다.
- 메뉴명, 수량, 필수 옵션이 부족하면 주문을 진행하지 않고 다시 묻습니다.
- 실제 결제가 아닌 더미 결제임을 안내합니다.
- RAG, 음성 입력, STT, TTS는 사용하지 않습니다.

## 제한사항

- 자연어 파싱은 `StubLLMProvider`의 규칙 기반 demo 수준입니다.
- React 키오스크에서 Streamlit으로 자동 이동하는 UI는 현재 구현되어 있지 않습니다. 시연 시 handoff token을 수동 또는 URL query로 전달합니다.
