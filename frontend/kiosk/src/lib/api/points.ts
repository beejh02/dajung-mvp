import { createPointsApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const pointsApi = createPointsApi(apiClient);
