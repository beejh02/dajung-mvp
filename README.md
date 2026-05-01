# 다정(多情) MVP

다정 MVP는 햄버거 키오스크 주문 경험을 여러 UI 방향으로 검증하고, 하나의 고완성도 UI를 실제 백엔드와 연결한 뒤, 로그인된 사용자가 텍스트 채팅형 AI Agent로도 주문할 수 있게 만드는 프로토타입입니다.

Phase 1부터는 최소 실행 가능한 프로젝트 스캐폴딩을 시작합니다. 이 문서는 전체 구조, 확정된 기술 선택, 개발 순서를 합의하기 위한 기준 문서입니다.

## MVP 목표

- React 기반 햄버거 키오스크 UI 3종 구현
- 3종 중 1종은 고완성도 UI로 제작하고 FastAPI 백엔드와 실제 연동
- 다정 회원가입/로그인을 위한 더미 사용자 DB 구현
- 주문 생성, 더미 결제, 포인트 적립, 영수증 생성, 관리자 대시보드 반영
- 기업 내부 도구 역할의 MCP 서버 구현
- Streamlit 기반 텍스트 채팅형 AI Agent 구현
- AI Agent는 `models/gemma-4-26b-a4b-it` 모델 사용
- 사용자는 다정 플랫폼에 한 번 로그인하면 AI 채팅에서도 주문 가능
- MVP에서는 음성, STT, TTS 제외
- RAG는 구현하지 않고, 추후 확장 가능한 구조만 고려

## 핵심 사용자 흐름

1. 사용자가 다정 플랫폼에서 회원가입 또는 로그인합니다.
2. 사용자는 React 키오스크 UI 또는 Streamlit AI 채팅 중 하나를 통해 메뉴를 탐색합니다.
3. 주문 항목, 옵션, 수량을 선택합니다.
4. 백엔드는 주문을 생성하고 더미 결제를 처리합니다.
5. 결제 완료 후 포인트를 적립하고 영수증을 생성합니다.
6. 관리자 대시보드에는 주문, 결제, 포인트, 영수증 상태가 반영됩니다.
7. AI Agent 주문도 동일한 백엔드 주문 파이프라인을 사용합니다.

## 확정 기술 스택

- Frontend: React, TypeScript, Vite
- Frontend Package Manager: pnpm
- Backend: FastAPI, Pydantic, SQLModel
- Python Package Manager: uv
- Local DB: SQLite
- Auth: JWT + AI 채팅 진입용 일회성 handoff token
- Agent UI: Streamlit
- AI Model: `models/gemma-4-26b-a4b-it`
- MCP Server: Python 기반 MCP 서버

## 로컬 실행 방법

Phase 1은 최소 실행 가능한 스캐폴딩만 포함합니다. 주문, 결제, 포인트, MCP tool, AI 채팅 로직은 아직 구현하지 않습니다.

### 키오스크 프론트엔드

```powershell
cd frontend/kiosk
pnpm install
pnpm dev --host 127.0.0.1 --port 5173
```

### 관리자 프론트엔드

```powershell
cd frontend/admin
pnpm install
pnpm dev --host 127.0.0.1 --port 5174
```

### 백엔드 API

```powershell
cd backend/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

헬스체크: `GET http://127.0.0.1:8000/health`

### AI Agent

```powershell
cd ai-agent/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\streamlit run app.py
```

### Fake MCP HTTP 서버

```powershell
cd mcp-server/app
uv venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

헬스체크: `GET http://127.0.0.1:8010/health`

## 계획된 프로젝트 구조

아래 구조는 Phase 1에서 생성한 초기 구조이며, 세부 기능 코드는 이후 단계에서 추가합니다.

```text
dajung-mvp/
  README.md
  PROJECT_SPEC.md
  TODO.md

  frontend/
    kiosk/
      # React 키오스크 앱
      # 로그인/회원가입, 키오스크 UI 3종, AI 채팅 진입 포함

    admin/
      # React 관리자 대시보드 앱
      # 주문, 결제, 포인트, 영수증 운영 현황 표시

  backend/
    app/
      # FastAPI 백엔드
      # 인증, 메뉴, 주문, 결제, 포인트, 영수증, 관리자 API

  mcp-server/
    app/
      # 기업 MCP 서버
      # Agent 또는 외부 MCP 클라이언트가 사용할 비즈니스 도구 제공

  ai-agent/
    app/
      # Streamlit 텍스트 채팅형 AI Agent
      # 다정 로그인 세션과 연결된 주문 채팅 UI

  shared/
    frontend-client/
      # kiosk/admin이 공유하는 API 클라이언트, 인증 유틸, 공통 타입

    dummy-data/
      # 더미 사용자, 메뉴, 주문 샘플 데이터

    docs/
      # 아키텍처, 인증 흐름, Agent 도구, MCP 도구 설계
```

## React 키오스크 UI 3종 방향

1. `Kiosk A - Classic Grid`
   - 일반적인 패스트푸드 키오스크 구조
   - 카테고리 탭, 메뉴 그리드, 장바구니, 결제 버튼 중심
   - 빠른 구현과 비교 기준 역할

2. `Kiosk B - Guided Order`
   - 단계형 주문 경험
   - 버거 선택, 옵션 선택, 사이드/음료 추천, 확인 순서
   - 초보 사용자에게 친절한 UX 검증

3. `Kiosk C - Dajung Premium`
   - 고완성도 UI 대상
   - 실제 FastAPI 백엔드와 연동
   - 주문 생성, 더미 결제, 포인트, 영수증, 관리자 반영까지 연결

`Classic Grid`와 `Guided Order`는 비교용 mock UI로 유지하고, 실제 백엔드 연동은 `Dajung Premium`에 집중합니다.

## 백엔드 책임

- 사용자 회원가입/로그인
- 더미 사용자 DB 관리
- 메뉴 데이터 제공
- 주문 생성 및 상태 관리
- 더미 결제 승인 처리
- 포인트 적립 및 조회
- 영수증 생성 및 조회
- 관리자 대시보드용 집계 API 제공
- AI Agent와 MCP 서버가 사용할 내부 API 제공
- 주문 생성 시 클라이언트 금액을 신뢰하지 않고 메뉴/옵션 기준으로 서버에서 가격 재계산
- 더미 결제 승인, 주문 상태 변경, 포인트 적립, 영수증 생성을 단일 트랜잭션으로 처리
- 결제 승인 API 재시도 시 포인트와 영수증이 중복 생성되지 않도록 idempotent하게 처리

## AI Agent 책임

- Streamlit 텍스트 채팅 UI 제공
- 로그인된 다정 사용자 세션과 연결
- 사용자의 자연어 주문 요청을 구조화된 주문으로 변환
- 메뉴 조회, 주문 생성, 더미 결제, 영수증 조회 도구 호출
- DB를 직접 읽거나 쓰지 않고 백엔드 API만 호출
- RAG 없이 동작하되, 추후 지식 검색 도구를 추가할 수 있는 구조 유지

## MCP 서버 책임

- 다정 내부 비즈니스 기능을 MCP 도구로 노출
- 비즈니스 로직을 직접 구현하지 않고 FastAPI 백엔드 API를 호출하는 얇은 어댑터로 동작
- MVP 필수 도구는 메뉴 조회, 주문 제출, 더미 결제 승인, 영수증 조회, 최근 주문 조회로 제한

## 개발 원칙

- UI 3종은 비교 가능해야 하지만, 실제 백엔드 연동은 `Dajung Premium` 1종에 집중합니다.
- 주문, 결제, 포인트, 영수증은 React와 AI Agent가 같은 백엔드 파이프라인을 사용합니다.
- 결제는 실제 PG 연동 없이 더미 승인으로 구현합니다.
- DB는 MVP 단계에서 SQLite + SQLModel로 시작하고, 교체 가능한 레이어를 둡니다.
- 주문, 결제, 주문 출처, 포인트 적립 유형은 명시적 enum으로 관리합니다.
- 관리자 API는 `role=admin` 사용자만 접근할 수 있게 합니다.
- RAG, 음성, STT, TTS는 MVP 범위에서 제외합니다.

## 관련 문서

- `PROJECT_SPEC.md`: 상세 제품/기술 명세
- `TODO.md`: 단계별 개발 체크리스트
