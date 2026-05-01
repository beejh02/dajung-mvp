import type { PaymentStatus } from "./payment";

export interface ReceiptPaymentContent {
  id: number;
  method: string;
  status: PaymentStatus;
  approved_amount: number;
  dummy_approval_code: string | null;
}

export interface ReceiptItemContent {
  menu_item_id: string;
  name: string;
  unit_price: number;
  quantity: number;
  selected_options: unknown[];
  line_total: number;
}

export interface ReceiptContent {
  order_id: number;
  user_id: string;
  source: string;
  status: string;
  subtotal_amount: number;
  discount_amount: number;
  total_amount: number;
  payment: ReceiptPaymentContent;
  earned_points: number;
  items: ReceiptItemContent[];
}

export interface ReceiptRead {
  id: number;
  order_id: number;
  receipt_number: string;
  content: ReceiptContent;
  issued_at: string;
}
