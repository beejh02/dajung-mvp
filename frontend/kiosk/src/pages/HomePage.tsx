import type { AuthSession } from "../lib/auth/session";
import { formatPoints } from "../lib/formatting/money";
import type { KioskRoute } from "../routes/routes";

interface HomePageProps {
  session: AuthSession | null;
  sessionError: string | null;
  onNavigate(route: KioskRoute): void;
}

export function HomePage({ session, sessionError, onNavigate }: HomePageProps) {
  const kioskModes = [
    {
      route: "/kiosk/classic-grid" as const,
      title: "Classic Grid",
      label: "비교용 Mock",
      description: "카테고리 탭, 메뉴 그리드, 장바구니 중심의 기본 키오스크 흐름입니다.",
    },
    {
      route: "/kiosk/guided-order" as const,
      title: "Guided Order",
      label: "비교용 Mock",
      description: "처음 방문한 사용자가 단계별로 메뉴와 옵션을 고를 수 있는 흐름입니다.",
    },
    {
      route: "/kiosk/dajung-premium" as const,
      title: "다정 프리미엄",
      label: "실제 API",
      description: "실제 메뉴, 서버 주문, 더미 결제, 포인트, 영수증까지 연결된 주문 화면입니다.",
    },
  ];

  return (
    <section className="home-stack">
      <div className="intro-panel">
        <p className="eyebrow">다정 주문 시작</p>
        <h1>다정 키오스크</h1>
        <p className="lead">
          세 가지 키오스크 방향을 비교해 보고, 프리미엄 화면에서 실제 백엔드 주문 흐름을 확인할 수 있습니다.
        </p>
        <div className="button-row">
          {session ? (
            <p className="success-text">{session.user.name}님으로 로그인되었습니다.</p>
          ) : (
            <>
              <button className="primary-action" type="button" onClick={() => onNavigate("/login")}>
                로그인
              </button>
              <button className="secondary-action" type="button" onClick={() => onNavigate("/signup")}>
                회원가입
              </button>
            </>
          )}
        </div>
      </div>

      <div className="mode-grid" aria-label="키오스크 화면 선택">
        {kioskModes.map((mode) => (
          <article className="mode-card" key={mode.route}>
            <div>
              <span>{mode.label}</span>
              <h2>{mode.title}</h2>
              <p>{mode.description}</p>
            </div>
            <button className="secondary-action" type="button" onClick={() => onNavigate(mode.route)}>
              열기
            </button>
          </article>
        ))}
      </div>

      <aside className="status-panel" aria-label="계정 상태">
        <p className="panel-title">로그인 상태</p>
        {session ? (
          <dl className="detail-list">
            <div>
              <dt>이름</dt>
              <dd>{session.user.name}</dd>
            </div>
            <div>
              <dt>이메일</dt>
              <dd>{session.user.email}</dd>
            </div>
            <div>
              <dt>포인트</dt>
              <dd>{formatPoints(session.user.points_balance)}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted-text">로그인된 세션이 없습니다.</p>
        )}
        {sessionError && <p className="error-text">{sessionError}</p>}
      </aside>
    </section>
  );
}
