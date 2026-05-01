import type { ReactNode } from "react";

import type { AuthSession } from "../../lib/auth/session";
import type { KioskRoute } from "../../routes/routes";

interface AppShellProps {
  children: ReactNode;
  currentRoute: KioskRoute;
  isRestoringSession: boolean;
  session: AuthSession | null;
  onNavigate(route: KioskRoute): void;
  onSignOut(): void;
}

export function AppShell({
  children,
  currentRoute,
  isRestoringSession,
  session,
  onNavigate,
  onSignOut,
}: AppShellProps) {
  const isPremiumRoute = currentRoute === "/kiosk/dajung-premium";

  return (
    <div className={`app-shell${isPremiumRoute ? " premium-app-shell" : ""}`}>
      <header className="topbar">
        <button className="brand-button" type="button" onClick={() => onNavigate("/")}>
          <span className="brand-mark">D</span>
          <span>
            <span className="brand-name">다정</span>
            <span className="brand-context">키오스크</span>
          </span>
        </button>
        <nav className="nav-actions" aria-label="주요 화면">
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/" ? "page" : undefined}
            onClick={() => onNavigate("/")}
          >
            홈
          </button>
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/kiosk/classic-grid" ? "page" : undefined}
            onClick={() => onNavigate("/kiosk/classic-grid")}
          >
            클래식
          </button>
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/kiosk/guided-order" ? "page" : undefined}
            onClick={() => onNavigate("/kiosk/guided-order")}
          >
            가이드
          </button>
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/kiosk/dajung-premium" ? "page" : undefined}
            onClick={() => onNavigate("/kiosk/dajung-premium")}
          >
            프리미엄
          </button>
          {session ? (
            <button className="nav-link" type="button" onClick={onSignOut}>
              로그아웃
            </button>
          ) : (
            <>
              <button
                className="nav-link"
                type="button"
                aria-current={currentRoute === "/login" ? "page" : undefined}
                onClick={() => onNavigate("/login")}
              >
                로그인
              </button>
              <button
                className="primary-action"
                type="button"
                aria-current={currentRoute === "/signup" ? "page" : undefined}
                onClick={() => onNavigate("/signup")}
              >
                회원가입
              </button>
            </>
          )}
        </nav>
      </header>
      <main className="main-surface" aria-busy={isRestoringSession}>
        {children}
      </main>
    </div>
  );
}
