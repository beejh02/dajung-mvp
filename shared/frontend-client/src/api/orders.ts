import type { ApiClient } from "./client";
import type { OrderCreateRequest, OrderRead } from "../types/order";

export interface OrdersApi {
  createOrder(payload: OrderCreateRequest): Promise<OrderRead>;
  getOrder(orderId: number): Promise<OrderRead>;
  listMyOrders(): Promise<OrderRead[]>;
}

export function createOrdersApi(client: ApiClient): OrdersApi {
  return {
    createOrder: (payload) => client.post<OrderRead, OrderCreateRequest>("/orders", payload),
    getOrder: (orderId) => client.get<OrderRead>(`/orders/${orderId}`),
    listMyOrders: () => client.get<OrderRead[]>("/orders/my"),
  };
}
