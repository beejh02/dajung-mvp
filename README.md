# 다정(多情) MVP

다정 MVP는 햄버거 키오스크 주문, 로그인 기반 사용자 계정, 텍스트 채팅형 AI Agent, 관리자 대시보드, Fake MCP HTTP 서버를 하나의 FastAPI 백엔드 주문 파이프라인으로 연결하는 로컬 프로토타입입니다.

## MVP 상태

- `Dajung Premium` 키오스크는 실제 백엔드 메뉴, 주문, 더미 결제, 포인트, 영수증 API와 연결되어 있습니다.
- `Classic Grid`와 `Guided Order`는 비교용 mock UI입니다.
- 관리자 대시보드는 `role=admin` 사용자만 접근할 수 있고 주문, 결제, 포인트, 영수증, 주문 출처 통계를 표시합니다.
- Streamlit AI Agent는 handoff token으로 Agent 세션을 교환하고 백엔드 Agent API만 호출합니다.
- AI Agent는 API Key 없이 `StubLLMProvider` demo mode로 동작합니다.
- Fake MCP HTTP 서버는 공식 MCP SDK 없이 tool 호출 HTTP API를 제공하며, 비즈니스 로직을 직접 구현하지 않고 백엔드 API를 호출합니다.
- 실제 결제 PG, 실제 RAG, 음성 입력, STT, TTS는 MVP 범위에서 제외되어 있습니다.

## 기술 스택

- Frontend: React, TypeScript, Vite, pnpm
- Backend: FastAPI, Pydantic, SQLModel, SQLite
- Python runtime: uv 기반 가상환경
- Auth: JWT + 3분 만료 일회성 handoff token
- Agent UI: Streamlit
- Agent model boundary: `LLMProvider`, `StubLLMProvider`, 목표 모델 식별자 `models/gemma-4-26b-a4b-it`
- MCP Server: FastAPI 기반 Fake MCP HTTP 서버

## 로컬 실행 방법

Windows PowerShell 기준입니다. `pnpm.ps1` 실행 정책 문제가 있으면 `pnpm.cmd`를 사용합니다.

### 1. 백엔드 API

```powershell
cd backend/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

확인:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 2. 키오스크 프론트엔드

```powershell
cd frontend/kiosk
pnpm.cmd install
pnpm.cmd dev --host 127.0.0.1 --port 5173
```

기본 API 주소는 `http://127.0.0.1:8000`입니다. 다른 백엔드 포트를 쓰면 Vite 환경 변수로 `VITE_API_BASE_URL`을 지정합니다.

### 3. 관리자 프론트엔드

```powershell
cd frontend/admin
pnpm.cmd install
pnpm.cmd dev --host 127.0.0.1 --port 5174
```

관리자 화면은 seed 데이터의 관리자 계정 또는 직접 생성한 `role=admin` 사용자로 로그인해야 사용할 수 있습니다.

### 4. Streamlit AI Agent

```powershell
cd ai-agent/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
$env:BACKEND_API_BASE_URL = "http://127.0.0.1:8000"
.venv\Scripts\streamlit.exe run app.py --server.address 127.0.0.1 --server.port 8502
```

AI Agent는 다음 방식으로 세션을 연결합니다.

- 백엔드 `POST /auth/agent-handoff`로 handoff token 발급
- Streamlit 사이드바에 handoff token 입력
- 또는 `http://127.0.0.1:8502/?handoff_token=<token>` 형태로 전달

현재 React 키오스크에서 Streamlit으로 자동 이동하는 버튼은 별도 구현하지 않았습니다. 시연에서는 handoff token을 API로 발급해 Streamlit에 전달합니다.

### 5. Fake MCP HTTP 서버

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

## 주요 API

상세 명세는 [shared/docs/API_SPEC.md](shared/docs/API_SPEC.md)를 기준으로 합니다.

- Auth: `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`, `POST /auth/agent-handoff`, `POST /auth/agent-session`
- Menu: `GET /menu`, `GET /menu/{menu_item_id}`
- Orders: `POST /orders`, `GET /orders/my`, `GET /orders/{order_id}`, `PATCH /orders/{order_id}/status`
- Payments: `POST /payments/dummy/approve`, `GET /payments/{payment_id}`
- Points: `GET /points/me`, `GET /points/ledger`
- Receipts: `GET /receipts/{receipt_id}`, `GET /orders/{order_id}/receipt`
- Admin: `GET /admin/overview`, `GET /admin/orders`, `GET /admin/orders/{order_id}`, `GET /admin/payments`, `GET /admin/points`, `GET /admin/receipts`
- Agent/Internal: `GET /agent/menu`, `GET /agent/user-context`, `POST /agent/orders/draft`, `POST /agent/orders/confirm`, `POST /agent/payments/dummy/approve`

## AI Agent와 MCP 문서

- Agent 도구와 demo mode 제한사항: [shared/docs/AGENT_TOOLS.md](shared/docs/AGENT_TOOLS.md)
- MCP HTTP tool 사용법: [mcp-server/app/docs/mcp_tools.md](mcp-server/app/docs/mcp_tools.md)
- MVP 데모 시나리오와 통합 검증 결과: [shared/docs/MVP_DEMO.md](shared/docs/MVP_DEMO.md)

## 프로젝트 구조

```text
dajung-mvp/
  frontend/
    kiosk/          # React 키오스크 앱
    admin/          # React 관리자 대시보드 앱
  backend/
    app/            # FastAPI 백엔드, DB 모델, 라우터, 서비스, 테스트
  ai-agent/
    app/            # Streamlit AI Agent, LLMProvider, tool wrapper
  mcp-server/
    app/            # Fake MCP HTTP 서버와 tool adapter
  shared/
    frontend-client/# kiosk/admin 공통 API client, type, auth utility
    dummy-data/     # 더미 사용자, 메뉴, 선호도, 주문 히스토리, RAG용 원천 텍스트
    docs/           # API, Agent, 데모, 제한사항 문서
  scripts/
    phase10_integration_check.py
```

## 검증 명령

```powershell
cd backend/app
.venv\Scripts\python.exe -m pytest
```

```powershell
cd frontend/kiosk
pnpm.cmd typecheck
pnpm.cmd build
```

```powershell
cd frontend/admin
pnpm.cmd typecheck
pnpm.cmd build
```

```powershell
cd mcp-server/app
.venv\Scripts\python.exe -m compileall app
```

```powershell
cd ai-agent/app
.venv\Scripts\python.exe -m compileall app.py backend_client.py config.py model_client.py session_handoff.py tools
```

백엔드와 MCP 서버를 실행한 뒤 전체 HTTP 통합 검증:

```powershell
$env:BACKEND_API_BASE_URL = "http://127.0.0.1:8000"
$env:MCP_API_BASE_URL = "http://127.0.0.1:8010"
.\backend\app\.venv\Scripts\python.exe scripts\phase10_integration_check.py
```

## MVP 제한사항

- 실제 결제 PG는 연결하지 않았고 더미 결제 승인만 제공합니다.
- 실제 Google Gemini API 또는 Cloudflare Workers AI 호출은 구현하지 않았습니다. provider 교체 지점만 준비되어 있으며 API Key가 없으면 `StubLLMProvider`를 사용합니다.
- 실제 RAG 검색은 구현하지 않았습니다. `shared/dummy-data/rag_contexts.json`은 추후 확장을 위한 원천 텍스트입니다.
- 음성 입력, STT, TTS는 구현하지 않았습니다.
- Fake MCP HTTP 서버는 공식 MCP SDK 서버가 아닙니다. 추후 `mcp-server/app/app/adapter.py` 경계를 공식 Python MCP SDK adapter로 교체하는 구조입니다.
- 로컬 SQLite 개발 DB와 seed 데이터는 시연용이며 실사용 개인정보를 담지 않습니다.
