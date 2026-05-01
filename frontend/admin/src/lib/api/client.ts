import { createApiClient, getStoredAuthSession } from "../../../../../shared/frontend-client/src";

const apiBaseUrl = import.meta.env.VITE_DAJUNG_API_BASE_URL ?? "/api";

export const apiClient = createApiClient({
  baseUrl: apiBaseUrl,
  getAccessToken: () => getStoredAuthSession()?.accessToken ?? null,
});
