import type { FormEvent } from "react";
import { useState } from "react";

import { authApi } from "../../lib/api/auth";
import { toKoreanApiError } from "../../lib/api/errors";
import { createAuthSession, type AuthSession } from "../../lib/auth/session";
import type { AdminRoute } from "../../routes/routes";

interface SignupPageProps {
  onAuthenticated(session: AuthSession): void;
  onNavigate(route: AdminRoute): void;
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
      setError(toKoreanApiError(submitError, "계정을 만들지 못했습니다."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-layout">
      <div>
        <p className="eyebrow">새 계정</p>
        <h1>계정 만들기</h1>
        <p className="lead">새 계정은 일반 사용자 권한으로 생성됩니다.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          <span>이름</span>
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
          <span>전화번호</span>
          <input
            autoComplete="tel"
            name="phone"
            type="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
        <label>
          <span>비밀번호</span>
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
          {isSubmitting ? "가입 중" : "계정 만들기"}
        </button>
        <button className="text-action" type="button" onClick={() => onNavigate("/login")}>
          로그인으로 돌아가기
        </button>
      </form>
    </section>
  );
}
