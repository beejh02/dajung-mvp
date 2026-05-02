import type { ApiClient } from "./client";
import type {
  AdminOrderDetailRead,
  AdminOrderSummaryRead,
  AdminOverviewRead,
  AdminPaymentStatusRead,
  AdminPointLedgerEntryRead,
  AdminReceiptStatusRead,
} from "../types/admin";

export interface AdminApi {
  getOverview(): Promise<AdminOverviewRead>;
  listOrders(limit?: number): Promise<AdminOrderSummaryRead[]>;
  getOrder(orderId: number): Promise<AdminOrderDetailRead>;
  listPayments(limit?: number): Promise<AdminPaymentStatusRead[]>;
  listPoints(limit?: number): Promise<AdminPointLedgerEntryRead[]>;
  listReceipts(limit?: number): Promise<AdminReceiptStatusRead[]>;
}

function withLimit(path: string, limit?: number): string {
  if (limit === undefined) {
    return path;
  }

  const params = new URLSearchParams({ limit: String(limit) });
  return `${path}?${params.toString()}`;
}

export function createAdminApi(client: ApiClient): AdminApi {
  return {
    getOverview: () => client.get<AdminOverviewRead>("/admin/overview"),
    listOrders: (limit) => client.get<AdminOrderSummaryRead[]>(withLimit("/admin/orders", limit)),
    getOrder: (orderId) => client.get<AdminOrderDetailRead>(`/admin/orders/${orderId}`),
    listPayments: (limit) => client.get<AdminPaymentStatusRead[]>(withLimit("/admin/payments", limit)),
    listPoints: (limit) => client.get<AdminPointLedgerEntryRead[]>(withLimit("/admin/points", limit)),
    listReceipts: (limit) => client.get<AdminReceiptStatusRead[]>(withLimit("/admin/receipts", limit)),
  };
}
