import type {
  AdminOrderSummaryRead,
  OrderStatus,
  PaymentStatus,
} from "../../../../../shared/frontend-client/src";
import { formatKrw, formatPoints } from "../../lib/formatting/money";
import {
  formatDateTime,
  orderSourceLabels,
  orderStatusLabels,
  paymentStatusLabels,
} from "../../lib/formatting/adminLabels";

interface AdminOrderTableProps {
  emptyMessage: string;
  orders: AdminOrderSummaryRead[];
  onOpenOrder(orderId: number): void;
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

export function AdminOrderTable({ emptyMessage, orders, onOpenOrder }: AdminOrderTableProps) {
  if (orders.length === 0) {
    return <p className="empty-state">{emptyMessage}</p>;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">주문</th>
            <th scope="col">고객</th>
            <th scope="col">출처</th>
            <th scope="col">주문 상태</th>
            <th scope="col">결제</th>
            <th scope="col">포인트</th>
            <th scope="col">영수증</th>
            <th scope="col">금액</th>
            <th scope="col">생성 시각</th>
            <th scope="col">상세</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td>#{order.id}</td>
              <td>
                <span className="table-strong">{order.user_name}</span>
                <span className="table-muted">{order.user_email || order.user_id}</span>
              </td>
              <td>{orderSourceLabels[order.source]}</td>
              <td>
                <span className={`status-badge ${orderStatusClass(order.status)}`}>
                  {orderStatusLabels[order.status]}
                </span>
              </td>
              <td>
                {order.payment ? (
                  <span className={`status-badge ${paymentStatusClass(order.payment.status)}`}>
                    {paymentStatusLabels[order.payment.status]}
                  </span>
                ) : (
                  <span className="status-badge status-waiting">미결제</span>
                )}
              </td>
              <td>{formatPoints(order.earned_points)}</td>
              <td>
                {order.receipt ? (
                  <span className="status-badge status-good">발급</span>
                ) : (
                  <span className="status-badge status-waiting">미발급</span>
                )}
              </td>
              <td>{formatKrw(order.total_amount)}</td>
              <td>{formatDateTime(order.created_at)}</td>
              <td>
                <button className="text-action compact-action" type="button" onClick={() => onOpenOrder(order.id)}>
                  보기
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
