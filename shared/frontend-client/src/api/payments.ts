import type { ApiClient } from "./client";
import type { DummyPaymentApproveRequest, PaymentRead } from "../types/payment";

export interface PaymentsApi {
  approveDummyPayment(payload: DummyPaymentApproveRequest): Promise<PaymentRead>;
  getPayment(paymentId: number): Promise<PaymentRead>;
}

export function createPaymentsApi(client: ApiClient): PaymentsApi {
  return {
    approveDummyPayment: (payload) =>
      client.post<PaymentRead, DummyPaymentApproveRequest>("/payments/dummy/approve", payload),
    getPayment: (paymentId) => client.get<PaymentRead>(`/payments/${paymentId}`),
  };
}
