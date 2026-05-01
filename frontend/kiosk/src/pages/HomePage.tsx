import type { AuthSession } from "../lib/auth/session";
import { formatPoints } from "../lib/formatting/money";
import type { KioskRoute } from "../routes/routes";

interface HomePageProps {
  session: AuthSession | null;
  sessionError: string | null;
  onNavigate(route: KioskRoute): void;
}

export function HomePage({ session, sessionError, onNavigate }: HomePageProps) {
  return (
    <section className="content-grid">
      <div className="intro-panel">
        <p className="eyebrow">Account entry</p>
        <h1>Dajung Kiosk</h1>
        <p className="lead">
          Sign in once and keep the same account context for the kiosk order flow.
        </p>
        <div className="button-row">
          {session ? (
            <p className="success-text">Signed in as {session.user.name}</p>
          ) : (
            <>
              <button className="primary-action" type="button" onClick={() => onNavigate("/login")}>
                Sign in
              </button>
              <button className="secondary-action" type="button" onClick={() => onNavigate("/signup")}>
                Create account
              </button>
            </>
          )}
        </div>
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
