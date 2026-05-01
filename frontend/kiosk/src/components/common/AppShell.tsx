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
  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand-button" type="button" onClick={() => onNavigate("/")}>
          <span className="brand-mark">D</span>
          <span>
            <span className="brand-name">Dajung</span>
            <span className="brand-context">Kiosk</span>
          </span>
        </button>
        <nav className="nav-actions" aria-label="Primary">
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/" ? "page" : undefined}
            onClick={() => onNavigate("/")}
          >
            Home
          </button>
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/kiosk/classic-grid" ? "page" : undefined}
            onClick={() => onNavigate("/kiosk/classic-grid")}
          >
            Classic
          </button>
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/kiosk/guided-order" ? "page" : undefined}
            onClick={() => onNavigate("/kiosk/guided-order")}
          >
            Guided
          </button>
          <button
            className="nav-link"
            type="button"
            aria-current={currentRoute === "/kiosk/dajung-premium" ? "page" : undefined}
            onClick={() => onNavigate("/kiosk/dajung-premium")}
          >
            Premium
          </button>
          {session ? (
            <button className="nav-link" type="button" onClick={onSignOut}>
              Sign out
            </button>
          ) : (
            <>
              <button
                className="nav-link"
                type="button"
                aria-current={currentRoute === "/login" ? "page" : undefined}
                onClick={() => onNavigate("/login")}
              >
                Sign in
              </button>
              <button
                className="primary-action"
                type="button"
                aria-current={currentRoute === "/signup" ? "page" : undefined}
                onClick={() => onNavigate("/signup")}
              >
                Create account
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
