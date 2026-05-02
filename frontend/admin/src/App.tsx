import { useEffect, useState } from "react";

import { AppShell } from "./components/common/AppShell";
import { authApi } from "./lib/api/auth";
import {
  clearAuthSession,
  getStoredAuthSession,
  replaceAuthSessionUser,
  saveAuthSession,
  type AuthSession,
} from "./lib/auth/session";
import { LoginPage } from "./pages/auth/LoginPage";
import { SignupPage } from "./pages/auth/SignupPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { OrderDetailPage } from "./pages/orders/OrderDetailPage";
import { OrdersPage } from "./pages/orders/OrdersPage";
import { getAdminRouteFromPathname, getOrderIdFromRoute, type AdminRoute } from "./routes/routes";

export default function App() {
  const [route, setRoute] = useState<AdminRoute>(() => getAdminRouteFromPathname(window.location.pathname));
  const [session, setSession] = useState<AuthSession | null>(() => getStoredAuthSession());
  const [isRestoringSession, setIsRestoringSession] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(getAdminRouteFromPathname(window.location.pathname));
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
        setSessionError("세션을 다시 확인하지 못했습니다.");
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

  const navigate = (nextRoute: AdminRoute) => {
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

  const orderDetailId = getOrderIdFromRoute(route);

  return (
    <AppShell
      currentRoute={route}
      isRestoringSession={isRestoringSession}
      session={session}
      onNavigate={navigate}
      onSignOut={handleSignOut}
    >
      {route === "/" && (
        <DashboardPage
          session={session}
          sessionError={sessionError}
          onNavigate={navigate}
        />
      )}
      {route === "/orders" && (
        <OrdersPage
          session={session}
          onNavigate={navigate}
        />
      )}
      {orderDetailId !== null && (
        <OrderDetailPage
          orderId={orderDetailId}
          session={session}
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
    </AppShell>
  );
}
