export type PaymentStatus = "pending" | "approved" | "failed" | "refunded";

export type PaymentMethod = "dummy_card" | "point";

export interface DummyPaymentApproveRequest {
  order_id: number;
  idempotency_key?: string | null;
  simulate_failure?: boolean;
}

export interface PaymentRead {
  id: number;
  order_id: number;
  status: PaymentStatus;
  method: PaymentMethod;
  approved_amount: number;
  dummy_approval_code: string | null;
  approved_at: string | null;
}
