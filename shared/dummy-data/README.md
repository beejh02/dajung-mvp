# Dummy Data

Phase 1.5에서 작성한 발표용 더미 기준 데이터입니다. 아직 백엔드 DB 모델이나 API는 구현하지 않았으며, Phase 2에서 DB seed 데이터로 변환될 예정입니다.

모든 개인정보성 값은 실제 사용자를 나타내지 않는 데모 데이터입니다. `password` 필드는 MVP seed와 로그인 흐름 검증을 위한 평문 예시이며, 실제 구현에서는 해시 저장으로 교체해야 합니다.

## 파일 목록

- `users.json`: 일반 사용자와 관리자 계정의 기준 데이터입니다. 키오스크, 관리자 대시보드, AI Agent 세션 교환 시 같은 사용자 ID를 공유하는 전제로 사용합니다.
- `payment_profiles.json`: 사용자별 등록 카드 더미 데이터입니다. 주문/결제 Phase에서 기본 결제수단 선택에 사용합니다.
- `point_memberships.json`: 사용자별 브랜드 포인트 멤버십 데이터입니다. 결제 후 포인트 적립과 관리자 확인 화면의 seed 후보입니다.
- `preferences.json`: 사용자별 선호 메뉴, 기피 식품, 알레르기/확인 메모, 기본 음료/사이드입니다. AI Agent가 개인화 주문 초안을 만들 때 참조할 수 있습니다.
- `brands.json`: 키오스크 UI 3종과 대응되는 햄버거 브랜드입니다. `brand_dajung`은 `Dajung Premium` 백엔드 연동 대상입니다.
- `stores.json`: 브랜드별 매장 데이터입니다. `store_dajung_001`은 `Dajung Premium` 대표 매장입니다.
- `menus.json`: 메뉴, 가격, 재료, 선택 옵션 그룹 데이터입니다. `menu_dajung_teriyaki_set`은 "데리버거 세트, 토마토 제외, 콜라, 감자튀김" 시나리오를 지원합니다.
- `order_history.json`: 사용자별 과거 주문 기록입니다. AI Agent가 "전에 먹던 거" 같은 요청을 해석할 때 사용할 수 있는 구조입니다.
- `rag_contexts.json`: 추후 RAG 확장을 위한 텍스트 조각입니다. 현재는 vector embedding 없이 `type`, `content`, `source`만 분리해 둡니다.

## 컴포넌트별 사용 범위

- 백엔드: Phase 2에서 `users`, `brands`, `stores`, `menus`, `payment_profiles`, `point_memberships`, `order_history`를 seed 데이터로 변환합니다.
- 키오스크: 브랜드, 매장, 메뉴, 옵션 그룹을 화면 구성과 주문 초안 생성에 사용합니다.
- 관리자 대시보드: 사용자, 주문 이력, 결제수단 존재 여부, 포인트 상태를 운영 현황 표시용으로 사용합니다.
- AI Agent: 사용자 취향, 과거 주문, RAG 후보 컨텍스트를 바탕으로 재주문과 개인화 추천 흐름을 구성합니다.
- MCP 서버: Phase 9에서 백엔드 API를 호출하는 fake MCP HTTP tool의 응답 예시 기준으로 사용합니다.
