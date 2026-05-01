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
      label: "Mock",
      description: "Category tabs, menu grid, and a cart-first checkout layout.",
    },
    {
      route: "/kiosk/guided-order" as const,
      title: "Guided Order",
      label: "Mock",
      description: "Step-by-step selection for first-time or slower decision flows.",
    },
    {
      route: "/kiosk/dajung-premium" as const,
      title: "Dajung Premium",
      label: "Live API",
      description: "Backend menu, server order, dummy payment, points, and receipt.",
    },
  ];

  return (
    <section className="home-stack">
      <div className="intro-panel">
        <p className="eyebrow">Account entry</p>
        <h1>Dajung Kiosk</h1>
        <p className="lead">
          Compare three kiosk directions. The Premium flow uses the live backend order pipeline.
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

      <div className="mode-grid" aria-label="Kiosk modes">
        {kioskModes.map((mode) => (
          <article className="mode-card" key={mode.route}>
            <div>
              <span>{mode.label}</span>
              <h2>{mode.title}</h2>
              <p>{mode.description}</p>
            </div>
            <button className="secondary-action" type="button" onClick={() => onNavigate(mode.route)}>
              Open
            </button>
          </article>
        ))}
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
