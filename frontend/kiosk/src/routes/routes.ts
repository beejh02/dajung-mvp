export type KioskRoute =
  | "/"
  | "/login"
  | "/signup"
  | "/kiosk/classic-grid"
  | "/kiosk/guided-order"
  | "/kiosk/dajung-premium";

const kioskRoutes = new Set<string>([
  "/",
  "/login",
  "/signup",
  "/kiosk/classic-grid",
  "/kiosk/guided-order",
  "/kiosk/dajung-premium",
]);

export function getKioskRouteFromPathname(pathname: string): KioskRoute {
  return kioskRoutes.has(pathname) ? (pathname as KioskRoute) : "/";
}
