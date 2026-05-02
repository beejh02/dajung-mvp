import { useEffect, useState } from "react";

import type { AdminOverviewRead } from "../../../../../shared/frontend-client/src";
import { AdminOrderTable } from "../../components/orders/AdminOrderTable";
import { adminApi } from "../../lib/api/admin";
import { toKoreanApiError } from "../../lib/api/errors";
import type { AuthSession } from "../../lib/auth/session";
import { formatKrw, formatPoints } from "../../lib/formatting/money";
import { orderSourceLabels } from "../../lib/formatting/adminLabels";
import type { AdminRoute } from "../../routes/routes";
import { getOrderDetailRoute } from "../../routes/routes";

interface DashboardPageProps {
  session: AuthSession | null;
  sessionError: string | null;
  onNavigate(route: AdminRoute): void;
}

function AccessNotice({
  session,
  sessionError,
  onNavigate,
}: DashboardPageProps) {
  if (!session) {
    return (
      <section className="content-grid">
        <div className="intro-panel">
          <p className="eyebrow">관리자 접근</p>
          <h1>로그인이 필요합니다</h1>
          <p className="lead">관리자 계정으로 로그인해야 운영 데이터를 볼 수 있습니다.</p>
          <div className="button-row">
            <button className="primary-action" type="button" onClick={() => onNavigate("/login")}>
              로그인
            </button>
            <button className="secondary-action" type="button" onClick={() => onNavigate("/signup")}>
              계정 만들기
            </button>
          </div>
          {sessionError && <p className="error-text">{sessionError}</p>}
        </div>
      </section>
    );
  }

  return (
    <section className="content-grid">
      <div className="intro-panel">
        <p className="eyebrow">접근 거부</p>
        <h1>관리자 권한이 없습니다</h1>
        <p className="warning-text">현재 계정은 관리자 화면에 접근할 수 없습니다.</p>
      </div>
      <aside className="status-panel" aria-label="계정 상태">
        <p className="panel-title">현재 계정</p>
        <dl className="detail-list">
          <div>
            <dt>이름</dt>
            <dd>{session.user.name}</dd>
          </div>
          <div>
            <dt>이메일</dt>
            <dd>{session.user.email}</dd>
          </div>
          <div>
            <dt>권한</dt>
            <dd>{session.user.role}</dd>
          </div>
          <div>
            <dt>포인트</dt>
            <dd>{formatPoints(session.user.points_balance)}</dd>
          </div>
        </dl>
      </aside>
    </section>
  );
}

export function DashboardPage({ session, sessionError, onNavigate }: DashboardPageProps) {
  const [overview, setOverview] = useState<AdminOverviewRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isAdmin = session?.user.role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      setOverview(null);
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    adminApi
      .getOverview()
      .then((data) => {
        if (isActive) {
          setOverview(data);
        }
      })
      .catch((loadError: unknown) => {
        if (isActive) {
          setError(toKoreanApiError(loadError, "관리자 개요를 불러오지 못했습니다."));
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

  if (!isAdmin) {
    return <AccessNotice session={session} sessionError={sessionError} onNavigate={onNavigate} />;
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <p className="eyebrow">운영 개요</p>
        <h1>관리자 대시보드</h1>
      </div>

      {isLoading && <p className="loading-state">관리자 데이터를 불러오는 중입니다.</p>}
      {error && <p className="error-text">{error}</p>}

      {overview && (
        <>
          <section className="metric-grid" aria-label="주요 지표">
            <article className="metric-card">
              <span>오늘 주문</span>
              <strong>{overview.today_order_count.toLocaleString("ko-KR")}건</strong>
            </article>
            <article className="metric-card">
              <span>오늘 더미 매출</span>
              <strong>{formatKrw(overview.today_dummy_sales_amount)}</strong>
            </article>
            <article className="metric-card">
              <span>전체 주문</span>
              <strong>{overview.total_order_count.toLocaleString("ko-KR")}건</strong>
            </article>
            <article className="metric-card">
              <span>전체 더미 매출</span>
              <strong>{formatKrw(overview.total_dummy_sales_amount)}</strong>
            </article>
            <article className="metric-card">
              <span>결제 대기</span>
              <strong>{overview.pending_payment_count.toLocaleString("ko-KR")}건</strong>
            </article>
            <article className="metric-card">
              <span>결제 완료</span>
              <strong>{overview.paid_order_count.toLocaleString("ko-KR")}건</strong>
            </article>
            <article className="metric-card">
              <span>영수증 발급</span>
              <strong>{overview.receipt_issued_count.toLocaleString("ko-KR")}건</strong>
            </article>
            <article className="metric-card">
              <span>포인트 적립</span>
              <strong>{formatPoints(overview.earned_points_total)}</strong>
            </article>
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <div>
                <p className="eyebrow">출처 통계</p>
                <h2>주문 출처별 현황</h2>
              </div>
            </div>
            <div className="source-stat-list">
              {overview.source_stats.map((stat) => {
                const width = overview.total_order_count > 0
                  ? Math.round((stat.order_count / overview.total_order_count) * 100)
                  : 0;
                return (
                  <article className="source-stat" key={stat.source}>
                    <div>
                      <strong>{orderSourceLabels[stat.source]}</strong>
                      <span>
                        {stat.order_count.toLocaleString("ko-KR")}건 · 결제 완료 {stat.paid_order_count.toLocaleString("ko-KR")}건
                      </span>
                    </div>
                    <div className="source-bar-track" aria-hidden="true">
                      <span className="source-bar-fill" style={{ width: `${width}%` }} />
                    </div>
                    <strong>{formatKrw(stat.sales_amount)}</strong>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <div>
                <p className="eyebrow">최근 주문</p>
                <h2>최근 주문 목록</h2>
              </div>
              <button className="secondary-action" type="button" onClick={() => onNavigate("/orders")}>
                전체 보기
              </button>
            </div>
            <AdminOrderTable
              emptyMessage="아직 주문 데이터가 없습니다."
              orders={overview.recent_orders}
              onOpenOrder={(orderId) => onNavigate(getOrderDetailRoute(orderId))}
            />
          </section>
        </>
      )}
    </section>
  );
}
