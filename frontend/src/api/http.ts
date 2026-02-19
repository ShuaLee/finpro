import { API_ENDPOINTS } from "./config";

let csrfToken: string | null = null;

type RequestMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

function isStateChangingMethod(method: RequestMethod): boolean {
  return method !== "GET";
}

export async function ensureCsrfToken(force = false): Promise<string> {
  if (csrfToken && !force) {
    return csrfToken;
  }

  const response = await fetch(API_ENDPOINTS.auth.csrf, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  const data = (await parseJsonSafely(response)) as { csrfToken?: string } | null;
  if (!response.ok || !data?.csrfToken) {
    throw new ApiError("Unable to initialize CSRF protection.", response.status);
  }

  csrfToken = data.csrfToken;
  return csrfToken;
}

export async function apiRequest<TResponse>(
  url: string,
  method: RequestMethod,
  body?: Record<string, unknown>,
): Promise<TResponse> {
  const headers: HeadersInit = {
    Accept: "application/json",
  };

  if (body) {
    headers["Content-Type"] = "application/json";
  }

  if (isStateChangingMethod(method)) {
    const token = await ensureCsrfToken();
    headers["X-CSRFToken"] = token;
  }

  const response = await fetch(url, {
    method,
    credentials: "include",
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = (await parseJsonSafely(response)) as { detail?: string } | TResponse | null;

  if (!response.ok) {
    const detail = typeof data === "object" && data && "detail" in data
      ? (data.detail ?? "Request failed.")
      : "Request failed.";
    throw new ApiError(String(detail), response.status);
  }

  return (data as TResponse) ?? ({} as TResponse);
}

export function clearCachedCsrfToken(): void {
  csrfToken = null;
}
