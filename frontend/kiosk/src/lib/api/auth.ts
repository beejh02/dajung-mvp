import { createAuthApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const authApi = createAuthApi(apiClient);
