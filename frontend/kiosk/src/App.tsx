import { useEffect, useState } from "react";

import { AppShell } from "./components/common/AppShell";
import { LoginPage } from "./pages/auth/LoginPage";
import { SignupPage } from "./pages/auth/SignupPage";
import { HomePage } from "./pages/HomePage";
import { ClassicGridPage } from "./pages/kiosk/ClassicGridPage";
import { DajungPremiumPage } from "./pages/kiosk/DajungPremiumPage";
import { GuidedOrderPage } from "./pages/kiosk/GuidedOrderPage";
import { authApi } from "./lib/api/auth";
import {
  clearAuthSession,
  getStoredAuthSession,
  replaceAuthSessionUser,
  saveAuthSession,
  type AuthSession,
} from "./lib/auth/session";
import { getKioskRouteFromPathname, type KioskRoute } from "./routes/routes";
import type { UserRead } from "../../../shared/frontend-client/src";

export default function App() {
  const [route, setRoute] = useState<KioskRoute>(() => getKioskRouteFromPathname(window.location.pathname));
  const [session, setSession] = useState<AuthSession | null>(() => getStoredAuthSession());
  const [isRestoringSession, setIsRestoringSession] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(getKioskRouteFromPathname(window.location.pathname));
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    const storedSession = getStoredAuthSession();
    if (!storedSession) {
      setSession(null);
      return;
    }

    let isActive = true;
    setIsRestoringSession(true);
    setSessionError(null);

    authApi
      .getCurrentUser()
      .then((user) => {
        if (!isActive) {
          return;
        }
        const refreshedSession = replaceAuthSessionUser(storedSession, user);
        saveAuthSession(refreshedSession);
        setSession(refreshedSession);
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        clearAuthSession();
        setSession(null);
        setSessionError(error instanceof Error ? error.message : "Session restore failed");
      })
      .finally(() => {
        if (isActive) {
          setIsRestoringSession(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const navigate = (nextRoute: KioskRoute) => {
    window.history.pushState(null, "", nextRoute);
    setRoute(nextRoute);
  };

  const handleAuthenticated = (nextSession: AuthSession) => {
    saveAuthSession(nextSession);
    setSession(nextSession);
    setSessionError(null);
    navigate("/");
  };

  const handleSignOut = () => {
    clearAuthSession();
    setSession(null);
    navigate("/login");
  };

  const handleUserRefreshed = (user: UserRead) => {
    setSession((currentSession) => {
      if (!currentSession) {
        return null;
      }
      const refreshedSession = replaceAuthSessionUser(currentSession, user);
      saveAuthSession(refreshedSession);
      return refreshedSession;
    });
  };

  return (
    <AppShell
      currentRoute={route}
      isRestoringSession={isRestoringSession}
      session={session}
      onNavigate={navigate}
      onSignOut={handleSignOut}
    >
      {route === "/" && (
        <HomePage
          session={session}
          sessionError={sessionError}
          onNavigate={navigate}
        />
      )}
      {route === "/login" && (
        <LoginPage
          onAuthenticated={handleAuthenticated}
          onNavigate={navigate}
        />
      )}
      {route === "/signup" && (
        <SignupPage
          onAuthenticated={handleAuthenticated}
          onNavigate={navigate}
        />
      )}
      {route === "/kiosk/classic-grid" && <ClassicGridPage />}
      {route === "/kiosk/guided-order" && <GuidedOrderPage />}
      {route === "/kiosk/dajung-premium" && (
        <DajungPremiumPage
          session={session}
          onNavigate={navigate}
          onUserRefreshed={handleUserRefreshed}
        />
      )}
    </AppShell>
  );
}
