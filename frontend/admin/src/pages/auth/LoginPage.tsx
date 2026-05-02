import type { FormEvent } from "react";
import { useState } from "react";

import { authApi } from "../../lib/api/auth";
import { toKoreanApiError } from "../../lib/api/errors";
import { createAuthSession, type AuthSession } from "../../lib/auth/session";
import type { AdminRoute } from "../../routes/routes";

interface LoginPageProps {
  onAuthenticated(session: AuthSession): void;
  onNavigate(route: AdminRoute): void;
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
      setError(toKoreanApiError(submitError, "로그인에 실패했습니다."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-layout">
      <div>
        <p className="eyebrow">관리자 계정</p>
        <h1>로그인</h1>
        <p className="lead">관리자 권한이 있는 계정으로 접속하세요.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          <span>이메일</span>
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
          <span>비밀번호</span>
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
          {isSubmitting ? "로그인 중" : "로그인"}
        </button>
        <button className="text-action" type="button" onClick={() => onNavigate("/signup")}>
          계정 만들기
        </button>
      </form>
    </section>
  );
}
