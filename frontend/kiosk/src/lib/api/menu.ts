import { createMenuApi } from "../../../../../shared/frontend-client/src";

import { apiClient } from "./client";

export const menuApi = createMenuApi(apiClient);
