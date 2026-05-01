import type { ApiClient } from "./client";
import type { ReceiptRead } from "../types/receipt";

export interface ReceiptsApi {
  getReceipt(receiptId: number): Promise<ReceiptRead>;
  getOrderReceipt(orderId: number): Promise<ReceiptRead>;
}

export function createReceiptsApi(client: ApiClient): ReceiptsApi {
  return {
    getReceipt: (receiptId) => client.get<ReceiptRead>(`/receipts/${receiptId}`),
    getOrderReceipt: (orderId) => client.get<ReceiptRead>(`/orders/${orderId}/receipt`),
  };
}
