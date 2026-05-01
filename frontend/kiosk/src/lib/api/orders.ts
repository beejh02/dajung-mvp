import { createOrdersApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const ordersApi = createOrdersApi(apiClient);
