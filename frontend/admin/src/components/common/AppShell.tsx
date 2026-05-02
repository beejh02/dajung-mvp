import type { ReactNode } from "react";

import type { AuthSession } from "../../lib/auth/session";
import type { AdminRoute } from "../../routes/routes";

interface AppShellProps {
  children: ReactNode;
  currentRoute: AdminRoute;
  isRestoringSession: boolean;
  session: AuthSession | null;
  onNavigate(route: AdminRoute): void;
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
  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand-button" type="button" onClick={() => onNavigate("/")}>
          <span className="brand-mark">D</span>
          <span>
            <span className="brand-name">Dajung</span>
            <span className="brand-context">관리자</span>
          </span>
        </button>
        <nav className="nav-actions" aria-label="주요 메뉴">
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/" ? "page" : undefined}
            onClick={() => onNavigate("/")}
          >
            개요
          </button>
          {session?.user.role === "admin" && (
            <button
              className="nav-link"
              type="button"
              aria-current={currentRoute.startsWith("/orders") ? "page" : undefined}
              onClick={() => onNavigate("/orders")}
            >
              주문
            </button>
          )}
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
                계정 만들기
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
