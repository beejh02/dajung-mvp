import type { FormEvent } from "react";
import { useState } from "react";

import { authApi } from "../../lib/api/auth";
import { createAuthSession, type AuthSession } from "../../lib/auth/session";
import type { KioskRoute } from "../../routes/routes";

interface LoginPageProps {
  onAuthenticated(session: AuthSession): void;
  onNavigate(route: KioskRoute): void;
}

export function LoginPage({ onAuthenticated, onNavigate }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await authApi.login({ email, password });
      onAuthenticated(createAuthSession(response));
    } catch (submitError: unknown) {
      setError(submitError instanceof Error ? submitError.message : "Sign in failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-layout">
      <div>
        <p className="eyebrow">Dajung account</p>
        <h1>Sign in</h1>
        <p className="lead">Use the same backend account that will own kiosk and agent orders.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          <span>Email</span>
          <input
            autoComplete="email"
            name="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label>
          <span>Password</span>
          <input
            autoComplete="current-password"
            name="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button className="primary-action full-width" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in" : "Sign in"}
        </button>
        <button className="text-action" type="button" onClick={() => onNavigate("/signup")}>
          Create account
        </button>
      </form>
    </section>
  );
}
