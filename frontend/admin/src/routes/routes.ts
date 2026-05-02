export type AdminRoute = "/" | "/login" | "/signup" | "/orders" | `/orders/${number}`;

const adminRoutes = new Set<string>(["/", "/login", "/signup", "/orders"]);

export function getAdminRouteFromPathname(pathname: string): AdminRoute {
  if (/^\/orders\/\d+$/.test(pathname)) {
    return pathname as AdminRoute;
  }

  return adminRoutes.has(pathname) ? (pathname as AdminRoute) : "/";
}

export function getOrderDetailRoute(orderId: number): AdminRoute {
  return `/orders/${orderId}` as AdminRoute;
}

export function getOrderIdFromRoute(route: AdminRoute): number | null {
  const match = route.match(/^\/orders\/(\d+)$/);
  return match ? Number(match[1]) : null;
}
