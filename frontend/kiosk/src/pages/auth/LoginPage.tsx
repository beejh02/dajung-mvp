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
      console.error(submitError);
      setError("로그인에 실패했습니다. 이메일과 비밀번호를 확인해 주세요.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-layout">
      <div>
        <p className="eyebrow">다정 계정</p>
        <h1>로그인</h1>
        <p className="lead">키오스크 주문과 포인트 적립에 사용할 다정 계정으로 로그인하세요.</p>
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
          회원가입
        </button>
      </form>
    </section>
  );
}
