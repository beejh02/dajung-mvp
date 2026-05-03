# 다정 MVP 데모와 최종 점검

## Phase 10 통합 검증 결과

검증일 기준 Phase 10에서 다음 항목을 통과했습니다.

- 회원가입부터 `Dajung Premium` 키오스크 주문 완료까지 확인
- 로그인부터 AI Agent handoff token 교환과 채팅 주문 완료까지 확인
- 더미 결제 후 포인트 적립 확인
- 더미 결제 후 영수증 생성 확인
- 관리자 대시보드 반영 확인
- 키오스크 주문과 AI Agent 주문의 백엔드 파이프라인 공유 확인
- 비로그인 사용자의 주문 제한 확인
- handoff token 만료와 재사용 방지 확인
- 관리자 API 일반 사용자 접근 거부 확인
- 더미 결제 승인 API 재시도 시 중복 포인트/영수증 미생성 확인
- MCP tool 입력/출력 스키마와 실패 응답 확인

반복 검증 명령:

```powershell
$env:BACKEND_API_BASE_URL = "http://127.0.0.1:8000"
$env:MCP_API_BASE_URL = "http://127.0.0.1:8010"
.\backend\app\.venv\Scripts\python.exe scripts\phase10_integration_check.py
```

## 데모 시나리오

### 1. 키오스크 주문

1. 백엔드와 `frontend/kiosk`를 실행합니다.
2. 새 사용자로 회원가입하거나 seed demo 사용자를 사용합니다.
3. 홈에서 `다정 프리미엄`을 엽니다.
4. 메뉴를 장바구니에 담습니다.
5. 주문 생성 후 서버 확정 금액을 확인합니다.
6. 더미 결제를 승인합니다.
7. 포인트 적립과 영수증 번호를 확인합니다.

### 2. AI Agent 주문

1. 백엔드와 Streamlit Agent를 실행합니다.
2. 로그인 사용자 access token으로 `POST /auth/agent-handoff`를 호출해 handoff token을 발급합니다.
3. Streamlit 사이드바에 handoff token을 입력하거나 URL query로 전달합니다.
4. 예: `데리버거 세트 1개 주문해줘`
5. Agent가 주문 초안과 총액을 안내하면 `확정` 또는 `결제`라고 입력합니다.
6. 더미 결제 완료, 포인트, 영수증 안내를 확인합니다.

### 3. 관리자 대시보드

1. `frontend/admin`을 실행합니다.
2. seed 관리자 계정 또는 `role=admin` 사용자로 로그인합니다.
3. 개요 화면에서 주문 수, 더미 매출, 포인트, 영수증, 주문 출처 통계를 확인합니다.
4. 최근 주문 목록에서 `kiosk_premium`, `ai_agent`, `mcp` 출처 주문이 함께 표시되는지 확인합니다.
5. 주문 상세에서 결제 상태, 포인트 적립 내역, 영수증 발급 상태를 확인합니다.

### 4. Fake MCP HTTP tool 호출

1. 백엔드와 MCP 서버를 실행합니다.
2. `GET /mcp/tools`로 tool 목록과 스키마를 확인합니다.
3. 사용자 token으로 `dajung.submit_order`, `dajung.approve_dummy_payment`, `dajung.get_receipt`를 호출합니다.
4. 관리자 token으로 `dajung.list_recent_orders`를 호출합니다.
5. 일반 사용자 token으로 관리자 tool을 호출해 실패 응답이 `backend_api_error`와 `backend_status=403`으로 변환되는지 확인합니다.

## 시연 전 체크리스트

- 백엔드 `.env` 또는 환경 변수에 운영 secret을 넣지 않았는지 확인
- 백엔드, 키오스크, 관리자, Agent, MCP 서버 포트가 서로 충돌하지 않는지 확인
- SQLite 개발 DB에 보여주기 곤란한 로컬 테스트 데이터가 없는지 확인
- `pnpm.cmd typecheck`와 `pnpm.cmd build`가 kiosk/admin에서 통과하는지 확인
- `backend/app` pytest가 통과하는지 확인
- Agent가 `StubLLMProvider` demo mode로 표시되는지 확인
- Fake MCP HTTP 서버가 `GET /mcp/tools`에 5개 필수 tool을 반환하는지 확인

## 미구현/제한사항

- 실제 결제 PG는 없습니다.
- 실제 LLM API 호출은 없습니다.
- 실제 RAG 검색은 없습니다.
- 음성 입력, STT, TTS는 없습니다.
- React 키오스크의 AI 채팅 자동 진입 UI는 없습니다.
- Fake MCP HTTP 서버는 공식 MCP SDK 서버가 아닙니다.
