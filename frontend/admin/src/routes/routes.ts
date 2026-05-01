export type AdminRoute = "/" | "/login" | "/signup";

const adminRoutes = new Set<string>(["/", "/login", "/signup"]);

export function getAdminRouteFromPathname(pathname: string): AdminRoute {
  return adminRoutes.has(pathname) ? (pathname as AdminRoute) : "/";
}
