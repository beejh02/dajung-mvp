import { useEffect, useState } from "react";

import type { AdminOrderSummaryRead } from "../../../../../shared/frontend-client/src";
import { AdminOrderTable } from "../../components/orders/AdminOrderTable";
import { adminApi } from "../../lib/api/admin";
import { toKoreanApiError } from "../../lib/api/errors";
import type { AuthSession } from "../../lib/auth/session";
import type { AdminRoute } from "../../routes/routes";
import { getOrderDetailRoute } from "../../routes/routes";

interface OrdersPageProps {
  session: AuthSession | null;
  onNavigate(route: AdminRoute): void;
}

export function OrdersPage({ session, onNavigate }: OrdersPageProps) {
  const [orders, setOrders] = useState<AdminOrderSummaryRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isAdmin = session?.user.role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      setOrders([]);
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    adminApi
      .listOrders(100)
      .then((data) => {
        if (isActive) {
          setOrders(data);
        }
      })
      .catch((loadError: unknown) => {
        if (isActive) {
          setError(toKoreanApiError(loadError, "주문 목록을 불러오지 못했습니다."));
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [isAdmin, session?.accessToken]);

  if (!session) {
    return (
      <section className="page-stack">
        <div className="page-heading">
          <p className="eyebrow">로그인 필요</p>
          <h1>주문 목록을 보려면 로그인해 주세요</h1>
        </div>
        <button className="primary-action fit-action" type="button" onClick={() => onNavigate("/login")}>
          로그인
        </button>
      </section>
    );
  }

  if (!isAdmin) {
    return (
      <section className="page-stack">
        <div className="page-heading">
          <p className="eyebrow">접근 거부</p>
          <h1>관리자 권한이 없습니다</h1>
        </div>
        <p className="warning-text">현재 계정은 주문 운영 목록에 접근할 수 없습니다.</p>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <p className="eyebrow">주문 운영</p>
        <h1>최근 주문 목록</h1>
      </div>
      {isLoading && <p className="loading-state">주문 목록을 불러오는 중입니다.</p>}
      {error && <p className="error-text">{error}</p>}
      {!isLoading && !error && (
        <AdminOrderTable
          emptyMessage="아직 주문 데이터가 없습니다."
          orders={orders}
          onOpenOrder={(orderId) => onNavigate(getOrderDetailRoute(orderId))}
        />
      )}
    </section>
  );
}
