import { API_BASE_URL, REQUEST_TIMEOUT_MS } from "./config";
import { AUTH_EXPIRED_EVENT, clearToken, getToken } from "./auth";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly requestId: string | null;

  constructor(message: string, status: number, code: string, details: unknown = null, requestId: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  json?: unknown;
  body?: BodyInit | null;
  /** Send the stored bearer token. Defaults to true. */
  auth?: boolean;
  /** Abort after this many ms (defaults to REQUEST_TIMEOUT_MS). */
  timeoutMs?: number;
}

const FRIENDLY_BY_STATUS: Record<number, string> = {
  400: "Please check your input and try again.",
  401: "Your session has ended. Please log in again.",
  403: "You do not have access to this.",
  404: "We could not find what you were looking for.",
  413: "That file is too large.",
  422: "Please check the highlighted fields and try again.",
  429: "You have reached a limit. Please wait a moment or try again tomorrow.",
  502: "We could not produce a clean result this time. Please try again.",
  503: "The service is busy right now. Please try again in a moment.",
  504: "The request took too long. Please try again.",
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { json, auth = true, timeoutMs = REQUEST_TIMEOUT_MS, headers: extraHeaders, signal, ...rest } = options;
  const headers = new Headers(extraHeaders);
  let body: BodyInit | null | undefined = rest.body;

  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(json);
  }
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  // Let callers cancel (for example when the user presses Cancel while a post is generating).
  signal?.addEventListener("abort", () => controller.abort());

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...rest, headers, body, signal: controller.signal });
  } catch (error) {
    if (signal?.aborted) throw new ApiError("Request cancelled.", 0, "cancelled");
    const timedOut = controller.signal.aborted;
    throw new ApiError(
      timedOut ? FRIENDLY_BY_STATUS[504] : "We could not reach the server. Check your connection and try again.",
      0,
      timedOut ? "timeout" : "network_error",
    );
  } finally {
    clearTimeout(timer);
  }

  if (response.status === 401 && auth) {
    clearToken();
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }

  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = "http_error";
  let message = FRIENDLY_BY_STATUS[response.status] ?? "Something went wrong. Please try again.";
  let details: unknown = null;
  let requestId: string | null = response.headers.get("X-Request-ID");
  try {
    const data = (await response.json()) as { error?: { code?: string; message?: string; details?: unknown; request_id?: string } };
    if (data.error) {
      code = data.error.code ?? code;
      message = data.error.message ?? message;
      details = data.error.details ?? null;
      requestId = data.error.request_id ?? requestId;
    }
  } catch {
    // Non-JSON body (for example a proxy error page): keep the friendly default.
  }
  return new ApiError(message, response.status, code, details, requestId);
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return "Something went wrong. Please try again.";
  return "Something went wrong. Please try again.";
}
