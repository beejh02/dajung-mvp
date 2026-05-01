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
            <span className="brand-context">Admin</span>
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
