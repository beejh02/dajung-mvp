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
      console.error(submitError);
      setError("회원가입에 실패했습니다. 입력한 정보를 다시 확인해 주세요.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="auth-layout">
      <div>
        <p className="eyebrow">새 계정</p>
        <h1>회원가입</h1>
        <p className="lead">다정 키오스크 주문과 포인트 적립에 사용할 계정을 만듭니다.</p>
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
          <span>휴대폰 번호</span>
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
          {isSubmitting ? "계정 생성 중" : "회원가입"}
        </button>
        <button className="text-action" type="button" onClick={() => onNavigate("/login")}>
          로그인
        </button>
      </form>
    </section>
  );
}
