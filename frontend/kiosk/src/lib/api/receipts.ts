import { createReceiptsApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const receiptsApi = createReceiptsApi(apiClient);
