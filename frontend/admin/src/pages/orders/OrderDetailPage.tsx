import { useEffect, useState } from "react";

import type {
  AdminOrderDetailRead,
  OrderStatus,
  PaymentStatus,
} from "../../../../../shared/frontend-client/src";
import { adminApi } from "../../lib/api/admin";
import { toKoreanApiError } from "../../lib/api/errors";
import type { AuthSession } from "../../lib/auth/session";
import {
  formatDateTime,
  orderSourceLabels,
  orderStatusLabels,
  paymentStatusLabels,
  pointLedgerTypeLabels,
} from "../../lib/formatting/adminLabels";
import { formatKrw, formatPoints } from "../../lib/formatting/money";
import type { AdminRoute } from "../../routes/routes";

interface OrderDetailPageProps {
  orderId: number;
  session: AuthSession | null;
  onNavigate(route: AdminRoute): void;
}

function orderStatusClass(status: OrderStatus): string {
  if (status === "paid" || status === "completed") {
    return "status-good";
  }
  if (status === "failed" || status === "cancelled") {
    return "status-bad";
  }
  return "status-waiting";
}

function paymentStatusClass(status: PaymentStatus): string {
  if (status === "approved") {
    return "status-good";
  }
  if (status === "failed" || status === "refunded") {
    return "status-bad";
  }
  return "status-waiting";
}

export function OrderDetailPage({ orderId, session, onNavigate }: OrderDetailPageProps) {
  const [order, setOrder] = useState<AdminOrderDetailRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isAdmin = session?.user.role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      setOrder(null);
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    adminApi
      .getOrder(orderId)
      .then((data) => {
        if (isActive) {
          setOrder(data);
        }
      })
      .catch((loadError: unknown) => {
        if (isActive) {
          setError(toKoreanApiError(loadError, "주문 상세를 불러오지 못했습니다."));
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
  }, [isAdmin, orderId, session?.accessToken]);

  if (!session) {
    return (
      <section className="page-stack">
        <div className="page-heading">
          <p className="eyebrow">로그인 필요</p>
          <h1>주문 상세를 보려면 로그인해 주세요</h1>
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
        <p className="warning-text">현재 계정은 주문 상세에 접근할 수 없습니다.</p>
      </section>
    );
  }

  return (
    <section className="page-stack">
      <div className="section-header">
        <div className="page-heading">
          <p className="eyebrow">주문 상세</p>
          <h1>주문 #{orderId}</h1>
        </div>
        <button className="secondary-action" type="button" onClick={() => onNavigate("/orders")}>
          목록으로
        </button>
      </div>

      {isLoading && <p className="loading-state">주문 상세를 불러오는 중입니다.</p>}
      {error && <p className="error-text">{error}</p>}

      {order && (
        <>
          <section className="detail-grid">
            <article className="detail-section">
              <h2>주문 정보</h2>
              <dl className="detail-list">
                <div>
                  <dt>고객</dt>
                  <dd>{order.user_name}</dd>
                </div>
                <div>
                  <dt>이메일</dt>
                  <dd>{order.user_email || order.user_id}</dd>
                </div>
                <div>
                  <dt>출처</dt>
                  <dd>{orderSourceLabels[order.source]}</dd>
                </div>
                <div>
                  <dt>주문 상태</dt>
                  <dd>
                    <span className={`status-badge ${orderStatusClass(order.status)}`}>
                      {orderStatusLabels[order.status]}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>생성 시각</dt>
                  <dd>{formatDateTime(order.created_at)}</dd>
                </div>
              </dl>
            </article>

            <article className="detail-section">
              <h2>금액</h2>
              <dl className="detail-list">
                <div>
                  <dt>상품 합계</dt>
                  <dd>{formatKrw(order.subtotal_amount)}</dd>
                </div>
                <div>
                  <dt>할인</dt>
                  <dd>{formatKrw(order.discount_amount)}</dd>
                </div>
                <div>
                  <dt>결제 금액</dt>
                  <dd>{formatKrw(order.total_amount)}</dd>
                </div>
                <div>
                  <dt>적립 포인트</dt>
                  <dd>{formatPoints(order.earned_points)}</dd>
                </div>
              </dl>
            </article>

            <article className="detail-section">
              <h2>결제 상태</h2>
              {order.payment ? (
                <dl className="detail-list">
                  <div>
                    <dt>상태</dt>
                    <dd>
                      <span className={`status-badge ${paymentStatusClass(order.payment.status)}`}>
                        {paymentStatusLabels[order.payment.status]}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>승인 금액</dt>
                    <dd>{formatKrw(order.payment.approved_amount)}</dd>
                  </div>
                  <div>
                    <dt>승인 코드</dt>
                    <dd>{order.payment.dummy_approval_code ?? "없음"}</dd>
                  </div>
                  <div>
                    <dt>승인 시각</dt>
                    <dd>{order.payment.approved_at ? formatDateTime(order.payment.approved_at) : "미승인"}</dd>
                  </div>
                </dl>
              ) : (
                <p className="empty-state">결제 정보가 없습니다.</p>
              )}
            </article>

            <article className="detail-section">
              <h2>영수증 발급 상태</h2>
              {order.receipt ? (
                <dl className="detail-list">
                  <div>
                    <dt>상태</dt>
                    <dd>
                      <span className="status-badge status-good">발급</span>
                    </dd>
                  </div>
                  <div>
                    <dt>영수증 번호</dt>
                    <dd>{order.receipt.receipt_number}</dd>
                  </div>
                  <div>
                    <dt>발급 시각</dt>
                    <dd>{formatDateTime(order.receipt.issued_at)}</dd>
                  </div>
                </dl>
              ) : (
                <p className="empty-state">영수증이 아직 발급되지 않았습니다.</p>
              )}
            </article>
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <div>
                <p className="eyebrow">주문 구성</p>
                <h2>상품 내역</h2>
              </div>
            </div>
            {order.items.length === 0 ? (
              <p className="empty-state">주문 상품이 없습니다.</p>
            ) : (
              <div className="item-list">
                {order.items.map((item) => (
                  <article className="line-item" key={item.id}>
                    <div>
                      <strong>{item.name_snapshot}</strong>
                      <span>
                        {item.quantity.toLocaleString("ko-KR")}개 · 단가 {formatKrw(item.unit_price)}
                      </span>
                      {item.selected_options.length > 0 ? (
                        <ul>
                          {item.selected_options.map((option) => (
                            <li key={option.group_id}>
                              {option.group_name}: {option.choices.map((choice) => choice.name).join(", ")}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span>선택 옵션 없음</span>
                      )}
                    </div>
                    <strong>{formatKrw(item.line_total)}</strong>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <div>
                <p className="eyebrow">포인트</p>
                <h2>적립 내역</h2>
              </div>
            </div>
            {order.point_ledger.length === 0 ? (
              <p className="empty-state">포인트 적립 내역이 없습니다.</p>
            ) : (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">구분</th>
                      <th scope="col">금액</th>
                      <th scope="col">잔액</th>
                      <th scope="col">처리 시각</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.point_ledger.map((entry) => (
                      <tr key={entry.id}>
                        <td>{pointLedgerTypeLabels[entry.type]}</td>
                        <td>{formatPoints(entry.amount)}</td>
                        <td>{formatPoints(entry.balance_after)}</td>
                        <td>{formatDateTime(entry.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </section>
  );
}
