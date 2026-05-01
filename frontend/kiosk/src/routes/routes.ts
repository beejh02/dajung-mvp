export type KioskRoute = "/" | "/login" | "/signup";

const kioskRoutes = new Set<string>(["/", "/login", "/signup"]);

export function getKioskRouteFromPathname(pathname: string): KioskRoute {
  return kioskRoutes.has(pathname) ? (pathname as KioskRoute) : "/";
}
