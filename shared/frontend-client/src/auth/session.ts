import type { TokenResponse, UserRead } from "../types/auth";

const STORAGE_KEY = "dajung.auth.session";

export interface AuthSession {
  accessToken: string;
  tokenType: string;
  tokenUse: string;
  expiresAt: number;
  user: UserRead;
}

export function createAuthSession(response: TokenResponse, now = Date.now()): AuthSession {
  return {
    accessToken: response.access_token,
    tokenType: response.token_type,
    tokenUse: response.token_use,
    expiresAt: now + response.expires_in * 1000,
    user: response.user,
  };
}

export function isAuthSessionExpired(session: AuthSession, now = Date.now()): boolean {
  return session.expiresAt <= now;
}

function isStorageAvailable(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function saveAuthSession(session: AuthSession): void {
  if (!isStorageAvailable()) {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearAuthSession(): void {
  if (!isStorageAvailable()) {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
}

export function getStoredAuthSession(): AuthSession | null {
  if (!isStorageAvailable()) {
    return null;
  }

  const rawSession = window.localStorage.getItem(STORAGE_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    const session = JSON.parse(rawSession) as AuthSession;
    if (!session.accessToken || !session.user || isAuthSessionExpired(session)) {
      clearAuthSession();
      return null;
    }
    return session;
  } catch {
    clearAuthSession();
    return null;
  }
}

export function replaceAuthSessionUser(session: AuthSession, user: UserRead): AuthSession {
  return {
    ...session,
    user,
  };
}
