import { createAdminApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const adminApi = createAdminApi(apiClient);
