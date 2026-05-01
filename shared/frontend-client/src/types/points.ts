export type PointLedgerType = "earn" | "spend" | "adjust";

export interface PointBalanceRead {
  user_id: string;
  points_balance: number;
}

export interface PointLedgerRead {
  id: number;
  user_id: string;
  order_id: number | null;
  type: PointLedgerType;
  amount: number;
  balance_after: number;
  created_at: string;
}
