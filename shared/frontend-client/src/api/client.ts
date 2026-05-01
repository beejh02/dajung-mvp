export type AccessTokenProvider = () => string | null;

export interface ApiClientOptions {
  baseUrl: string;
  getAccessToken?: AccessTokenProvider;
  fetchImpl?: typeof fetch;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export interface ApiClient {
  get<TResponse>(path: string): Promise<TResponse>;
  post<TResponse, TBody = unknown>(path: string, body?: TBody): Promise<TResponse>;
  patch<TResponse, TBody = unknown>(path: string, body: TBody): Promise<TResponse>;
}

function joinUrl(baseUrl: string, path: string): string {
  const cleanBase = baseUrl.replace(/\/+$/, "");
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function detailToMessage(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((entry) => {
        if (isRecord(entry) && typeof entry.msg === "string") {
          return entry.msg;
        }
        return null;
      })
      .filter((entry): entry is string => entry !== null);

    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  if (isRecord(detail) && typeof detail.message === "string") {
    return detail.message;
  }

  return "Request failed";
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export function createApiClient(options: ApiClientOptions): ApiClient {
  const request = async <TResponse>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<TResponse> => {
    const headers = new Headers();
    const accessToken = options.getAccessToken?.();

    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }

    const init: RequestInit = {
      method,
      headers,
    };

    if (body !== undefined) {
      headers.set("Content-Type", "application/json");
      init.body = JSON.stringify(body);
    }

    const response = await (options.fetchImpl ?? fetch)(joinUrl(options.baseUrl, path), init);

    if (!response.ok) {
      const problem = await readResponseBody(response);
      const detail = isRecord(problem) && "detail" in problem ? problem.detail : problem;
      throw new ApiError(response.status, detail, detailToMessage(detail));
    }

    if (response.status === 204) {
      return undefined as TResponse;
    }

    return response.json() as Promise<TResponse>;
  };

  return {
    get: (path) => request("GET", path),
    post: (path, body) => request("POST", path, body),
    patch: (path, body) => request("PATCH", path, body),
  };
}
