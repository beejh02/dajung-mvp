# 다정(多情) MVP TODO

이 TODO는 코드가 없는 상태에서 시작하는 개발 순서입니다. 현재 단계에서는 문서만 작성하고, 실제 폴더와 코드는 다음 단계부터 생성합니다.

## Phase 0. 문서 및 범위 확정

- [x] `README.md` 작성
- [x] `PROJECT_SPEC.md` 작성
- [x] `TODO.md` 작성
- [x] React UI 3종의 이름과 목적 확정: `Classic Grid`, `Guided Order`, `Dajung Premium`
- [x] 고완성도 UI 대상 확정: `Dajung Premium`
- [x] 백엔드 DB 방식 확정: SQLite + SQLModel
- [x] 인증 방식 확정: JWT + 3분 만료 일회성 handoff token
- [x] 주문/결제/출처/포인트 enum 정책 확정
- [x] 결제 승인 idempotency와 단일 트랜잭션 처리 정책 확정
- [x] MCP 서버 역할 확정: FastAPI 백엔드 API를 호출하는 얇은 어댑터
- [x] MVP MCP tool 범위 확정: 메뉴 조회, 주문 제출, 더미 결제 승인, 영수증 조회, 최근 주문 조회
- [x] AI 모델 클라이언트 전략 확정: `LLMProvider` 추상화 + `StubLLMProvider`로 E2E 선구현
- [x] `models/gemma-4-26b-a4b-it`는 목표 모델로 두고, 초기 MVP는 실제 API 연결 없이 Stub provider로 개발
- [x] 추후 Google Gemini API 또는 Cloudflare Workers AI Provider로 교체 가능한 구조 확정
- [x] MCP 서버 SDK/런타임 전략 확정: 공식 SDK 미사용, FastAPI 기반 fake MCP HTTP 서버로 시작

## Phase 1. 프로젝트 스캐폴딩

- [x] 루트 폴더 구조 생성
- [x] `frontend/kiosk` React + TypeScript + Vite 초기화
- [x] `frontend/admin` React + TypeScript + Vite 초기화
- [x] `backend/app` FastAPI 앱 초기화
- [x] `ai-agent/app` Streamlit 앱 초기화
- [x] `mcp-server/app` MCP 서버 초기화
- [x] `shared/frontend-client` 공통 프론트 API 클라이언트 영역 생성
- [x] `shared/dummy-data` 더미 데이터 영역 생성
- [x] `shared/docs` 설계 문서 영역 생성
- [x] 공통 환경 변수 예시 파일 작성
- [x] 로컬 실행 방법 문서화

## Phase 2. 백엔드 기반 구현

- [x] FastAPI 앱 엔트리포인트 작성
- [x] 설정 모듈 작성
- [x] SQLite 연결 구성
- [x] DB 모델 정의
- [x] `OrderStatus`, `PaymentStatus`, `OrderSource`, `PointLedgerType` enum 정의
- [x] 사용자 `role` 필드와 관리자 권한 모델 정의
- [x] handoff token 저장 모델 정의: token hash, 만료, 사용 시각
- [x] 결제/영수증/포인트 중복 방지 유니크 제약 정의
- [x] Pydantic 요청/응답 스키마 정의
- [x] 메뉴 옵션 그룹 스키마 정의: required, min_select, max_select, price_delta, is_available
- [x] 더미 seed 데이터 구조 작성
- [x] 메뉴 seed 데이터 작성
- [x] 더미 사용자 seed 데이터 작성
- [x] 관리자 seed 사용자 작성
- [x] 기본 헬스체크 API 작성

## Phase 3. 인증 및 사용자

- [x] 회원가입 API 구현
- [x] 로그인 API 구현
- [x] 현재 사용자 조회 API 구현
- [x] 비밀번호 해시 처리
- [x] JWT 액세스 토큰 발급
- [x] 관리자 API 보호용 `role=admin` dependency 구현
- [x] React/Agent 공통 인증 정책 정리
- [x] AI 채팅 진입용 3분 만료 handoff token API 구현
- [x] handoff token 해시 저장 구현
- [x] handoff token 1회 사용 처리 구현
- [x] Agent 세션 교환 API 구현: 유효 token을 Agent용 JWT로 교환

## Phase 4. 메뉴, 주문, 결제, 포인트, 영수증

- [x] 메뉴 목록 API 구현
- [x] 메뉴 상세 API 구현
- [x] 주문 생성 시 메뉴/옵션 기준 서버 가격 재계산 구현
- [x] 필수 옵션/선택 개수/비활성 메뉴 옵션 검증 구현
- [x] 주문 생성 API 구현
- [x] 주문 상세 API 구현
- [x] 내 주문 목록 API 구현
- [x] 주문 상태 전이 검증 구현
- [x] `PATCH /orders/{order_id}/status` 관리자/내부 전용 처리
- [x] 더미 결제 승인 API 구현
- [x] 결제 승인 후 주문 상태 변경/포인트 적립/영수증 생성을 단일 트랜잭션으로 처리
- [x] 결제 승인 API idempotency 구현
- [x] 포인트 적립 중복 방지 구현
- [x] 영수증 중복 생성 방지 구현
- [x] 주문 실패/결제 실패 더미 케이스 정의
- [x] 백엔드 서비스 단위 테스트 작성: 가격 재계산, 옵션 검증, 상태 전이, idempotency

## Phase 5. React 웹 앱

- [x] React 라우팅 구조 작성
- [x] `shared/frontend-client` 기반 API 클라이언트 작성
- [x] `frontend/kiosk`와 `frontend/admin`의 앱별 API 래퍼 작성
- [x] 로그인 화면 구현
- [x] 회원가입 화면 구현
- [x] 로그인 세션 저장/복원 처리
- [x] 공통 레이아웃 작성
- [x] 메뉴/가격 포맷 유틸 작성

## Phase 6. 키오스크 UI 3종

- [x] `Classic Grid` 키오스크 UI 구현
- [x] `Guided Order` 키오스크 UI 구현
- [x] `Dajung Premium` 키오스크 UI 구현
- [x] 3종 UI 전환 화면 또는 라우트 구현
- [x] 비연동 UI용 mock 데이터 연결
- [x] `Dajung Premium`에 실제 메뉴 API 연결
- [x] `Dajung Premium`에서 서버 계산 금액을 기준으로 주문 확인 UI 표시
- [x] `Dajung Premium` 주문 생성 연동
- [x] `Dajung Premium` 더미 결제 연동
- [x] `Dajung Premium` 포인트/영수증 결과 화면 구현
- [x] 모바일/태블릿/키오스크 크기 반응형 확인

## Phase 7. 관리자 대시보드

- [x] 관리자 라우트 작성
- [x] 관리자 개요 API 구현
- [x] 관리자 API 일반 사용자 접근 거부 처리
- [x] 최근 주문 목록 UI 구현
- [x] 주문 상세 확인 UI 구현
- [x] 결제 상태 표시
- [x] 포인트 적립 내역 표시
- [x] 영수증 발급 상태 표시
- [x] 주문 출처별 통계 표시
- [x] 키오스크 주문과 AI Agent 주문이 함께 반영되는지 확인

## Phase 8. Streamlit AI Agent

- [x] Streamlit 채팅 UI 작성
- [x] 다정 handoff token 수신 처리
- [x] Agent 세션 교환 처리
- [x] `LLMProvider` 인터페이스 작성
- [x] `StubLLMProvider` 구현: 사용자 입력 기반 predefined intent JSON 반환
- [x] API Key 없이 실행 가능한 demo mode 처리
- [x] `models/gemma-4-26b-a4b-it` 목표 모델 식별자 설정값 정의
- [x] Google Gemini API Provider 교체 가능 구조 준비
- [x] Cloudflare Workers AI Provider 교체 가능 구조 준비
- [x] 시스템 프롬프트 작성
- [x] 메뉴 조회 도구 구현
- [x] 사용자 컨텍스트 조회 도구 구현
- [x] 주문 초안 생성 도구 구현
- [x] 주문 확정 도구 구현
- [x] 더미 결제 도구 구현
- [x] 영수증 조회 도구 구현
- [x] 포인트 조회 도구 구현
- [x] 결제 전 사용자 확인 흐름 구현
- [x] intent JSON 검증 실패 시 재질문 흐름 구현
- [x] 비활성 메뉴/옵션 요청 시 대체 메뉴 제안 흐름 구현

## Phase 9. 기업 MCP 서버

- [x] FastAPI fake MCP HTTP 서버 엔트리포인트 작성
- [x] 공식 MCP SDK 없이 동작하는 tool 호출 HTTP API 작성
- [x] FastAPI 백엔드 클라이언트 작성
- [x] tool adapter 경계 작성: HTTP 요청/응답과 tool 실행 로직 분리
- [x] `mcp-server/app/tools/` 아래에 tool 로직 분리
- [x] `dajung.get_menu` tool 구현
- [x] `dajung.submit_order` tool 구현
- [x] `dajung.approve_dummy_payment` tool 구현
- [x] `dajung.get_receipt` tool 구현
- [x] `dajung.list_recent_orders` tool 구현
- [x] 실제 MCP Tool형 입력/출력 스키마 문서화
- [x] MCP tool 백엔드 API 오류 변환 처리
- [x] 추후 공식 Python MCP SDK adapter 전환 지점 문서화
- [ ] 확장 후보 tool 보류: `dajung.get_user_profile`, `dajung.create_order_draft`, `dajung.get_admin_overview`

## Phase 10. 통합 검증

- [ ] 회원가입부터 키오스크 주문까지 E2E 확인
- [ ] 로그인부터 AI 채팅 주문까지 E2E 확인
- [ ] 더미 결제 후 포인트 적립 확인
- [ ] 더미 결제 후 영수증 생성 확인
- [ ] 관리자 대시보드 반영 확인
- [ ] 키오스크 주문과 AI Agent 주문의 백엔드 파이프라인 공유 확인
- [ ] 비로그인 사용자의 주문 제한 확인
- [ ] handoff token 만료/재사용 방지 확인
- [ ] 관리자 API 일반 사용자 접근 거부 확인
- [ ] 더미 결제 승인 API 재시도 시 중복 포인트/영수증 미생성 확인
- [ ] MCP tool 입력/출력 스키마와 실패 응답 확인

## Phase 11. 정리 및 MVP 마감

- [ ] README 실행 방법 업데이트
- [ ] API 명세 업데이트
- [ ] Agent 도구 명세 업데이트
- [ ] MCP 서버 사용 방법 업데이트
- [ ] demo mode, Stub LLM, fake MCP HTTP 서버 제한사항 정리
- [ ] 추후 RAG 확장 계획 정리
- [ ] 음성/STT/TTS 제외 범위 재명시
- [ ] 데모 시나리오 작성

## MVP 완료 기준

- [ ] 로그인한 사용자가 `Dajung Premium` 키오스크에서 주문을 완료할 수 있습니다.
- [ ] 로그인한 사용자가 AI 채팅에서 주문을 완료할 수 있습니다.
- [ ] 주문 완료 시 더미 결제, 포인트 적립, 영수증 생성이 자동 처리됩니다.
- [ ] 관리자 대시보드에서 모든 주문 출처가 확인됩니다.
- [ ] MCP 서버가 핵심 비즈니스 도구를 노출합니다.
- [ ] RAG, 음성, STT, TTS가 MVP 범위에서 제외되어 있습니다.
