import type { AuthSession } from "../lib/auth/session";
import { formatPoints } from "../lib/formatting/money";
import type { AdminRoute } from "../routes/routes";

interface HomePageProps {
  session: AuthSession | null;
  sessionError: string | null;
  onNavigate(route: AdminRoute): void;
}

export function HomePage({ session, sessionError, onNavigate }: HomePageProps) {
  const isAdmin = session?.user.role === "admin";

  return (
    <section className="content-grid">
      <div className="intro-panel">
        <p className="eyebrow">Operator access</p>
        <h1>Dajung Admin</h1>
        <p className="lead">
          Sign in with an administrator account before opening operations screens.
        </p>
        {!session && (
          <div className="button-row">
            <button className="primary-action" type="button" onClick={() => onNavigate("/login")}>
              Sign in
            </button>
            <button className="secondary-action" type="button" onClick={() => onNavigate("/signup")}>
              Create account
            </button>
          </div>
        )}
        {session && !isAdmin && (
          <p className="warning-text">This account does not have administrator access.</p>
        )}
        {session && isAdmin && (
          <p className="success-text">Administrator session active.</p>
        )}
      </div>

      <aside className="status-panel" aria-label="Account status">
        <p className="panel-title">Session</p>
        {session ? (
          <dl className="detail-list">
            <div>
              <dt>Name</dt>
              <dd>{session.user.name}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{session.user.email}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{session.user.role}</dd>
            </div>
            <div>
              <dt>Points</dt>
              <dd>{formatPoints(session.user.points_balance)}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted-text">No active session</p>
        )}
        {sessionError && <p className="error-text">{sessionError}</p>}
      </aside>
    </section>
  );
}
