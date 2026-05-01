export type OrderSource = "kiosk_classic" | "kiosk_guided" | "kiosk_premium" | "ai_agent" | "mcp";

export type OrderStatus = "draft" | "pending_payment" | "paid" | "completed" | "cancelled" | "failed";

export interface SelectedOptionInput {
  group_id: string;
  choice_ids: string[];
}

export interface OrderCreateItem {
  menu_item_id: string;
  quantity: number;
  selected_options: SelectedOptionInput[];
}

export interface OrderCreateRequest {
  source: OrderSource;
  items: OrderCreateItem[];
  simulate_failure?: boolean;
}

export interface OrderSelectedChoiceRead {
  id: string;
  name: string;
  price_delta: number;
}

export interface OrderSelectedOptionRead {
  group_id: string;
  group_name: string;
  choices: OrderSelectedChoiceRead[];
}

export interface OrderItemRead {
  id: number;
  menu_item_id: string;
  name_snapshot: string;
  unit_price: number;
  quantity: number;
  selected_options: OrderSelectedOptionRead[];
  line_total: number;
}

export interface OrderRead {
  id: number;
  user_id: string;
  source: OrderSource;
  status: OrderStatus;
  subtotal_amount: number;
  discount_amount: number;
  total_amount: number;
  created_at: string;
  updated_at: string;
  items: OrderItemRead[];
}
