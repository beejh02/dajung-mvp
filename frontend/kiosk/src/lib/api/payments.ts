import { createPaymentsApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const paymentsApi = createPaymentsApi(apiClient);
