import type { OrderItemRead, OrderSource, OrderStatus } from "./order";
import type { PaymentMethod, PaymentStatus } from "./payment";
import type { PointLedgerType } from "./points";

export interface AdminPaymentStatusRead {
  id: number;
  order_id: number;
  status: PaymentStatus;
  method: PaymentMethod;
  approved_amount: number;
  dummy_approval_code: string | null;
  approved_at: string | null;
  created_at: string;
}

export interface AdminPointLedgerEntryRead {
  id: number;
  user_id: string;
  order_id: number | null;
  type: PointLedgerType;
  amount: number;
  balance_after: number;
  created_at: string;
}

export interface AdminReceiptStatusRead {
  id: number;
  order_id: number;
  receipt_number: string;
  issued_at: string;
}

export interface AdminOrderSummaryRead {
  id: number;
  user_id: string;
  user_name: string;
  user_email: string;
  source: OrderSource;
  status: OrderStatus;
  subtotal_amount: number;
  discount_amount: number;
  total_amount: number;
  created_at: string;
  updated_at: string;
  payment: AdminPaymentStatusRead | null;
  earned_points: number;
  receipt: AdminReceiptStatusRead | null;
}

export interface AdminOrderDetailRead extends AdminOrderSummaryRead {
  items: OrderItemRead[];
  point_ledger: AdminPointLedgerEntryRead[];
}

export interface AdminOrderSourceStatRead {
  source: OrderSource;
  order_count: number;
  paid_order_count: number;
  sales_amount: number;
}

export interface AdminOverviewRead {
  today_order_count: number;
  today_dummy_sales_amount: number;
  total_order_count: number;
  total_dummy_sales_amount: number;
  pending_payment_count: number;
  paid_order_count: number;
  failed_order_count: number;
  receipt_issued_count: number;
  earned_points_total: number;
  source_stats: AdminOrderSourceStatRead[];
  recent_orders: AdminOrderSummaryRead[];
}
