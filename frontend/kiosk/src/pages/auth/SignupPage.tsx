import type { FormEvent } from "react";
import { useState } from "react";

import { authApi } from "../../lib/api/auth";
import { createAuthSession, type AuthSession } from "../../lib/auth/session";
import type { KioskRoute } from "../../routes/routes";

interface SignupPageProps {
  onAuthenticated(session: AuthSession): void;
  onNavigate(route: KioskRoute): void;
}

export function SignupPage({ onAuthenticated, onNavigate }: SignupPageProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await authApi.signup({
        email,
        password,
        name,
        phone: phone || null,
      });
      onAuthenticated(createAuthSession(response));
    } catch (submitError: unknown) {
      setError(submitError instanceof Error ? submitError.message : "Account creation failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-layout">
      <div>
        <p className="eyebrow">New account</p>
        <h1>Create account</h1>
        <p className="lead">Create a backend-backed user session before opening order screens.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input
            autoComplete="name"
            name="name"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
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
          <span>Phone</span>
          <input
            autoComplete="tel"
            name="phone"
            type="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
        <label>
          <span>Password</span>
          <input
            autoComplete="new-password"
            minLength={8}
            name="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error && <p className="error-text">{error}</p>}
        <button className="primary-action full-width" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating account" : "Create account"}
        </button>
        <button className="text-action" type="button" onClick={() => onNavigate("/login")}>
          Sign in
        </button>
      </form>
    </section>
  );
}
