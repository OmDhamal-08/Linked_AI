import { describe, expect, it, vi, beforeEach } from "vitest";
import { apiFetch, ApiError, errorMessage } from "@/lib/api";
import { setToken, clearToken, AUTH_EXPIRED_EVENT } from "@/lib/auth";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
}

describe("apiFetch", () => {
  beforeEach(() => {
    clearToken();
  });

  it("sends the bearer token when one is stored", async () => {
    setToken("abc.def.ghi");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/users/me");
    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer abc.def.ghi");
  });

  it("does not send a token when auth is disabled", async () => {
    setToken("abc.def.ghi");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, {}));
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/meta/taxonomy", { auth: false });
    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("Authorization")).toBeNull();
  });

  it("maps backend error envelopes to friendly ApiErrors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(429, { error: { code: "usage_limit_reached", message: "You have reached today's limit.", request_id: "r1" } }),
      ),
    );
    const error = (await apiFetch("/posts/generate", { method: "POST", json: {} }).catch((e: unknown) => e)) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(429);
    expect(error.code).toBe("usage_limit_reached");
    expect(error.message).toBe("You have reached today's limit.");
    expect(error.requestId).toBe("r1");
  });

  it("falls back to a friendly message when the body is not JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>502</html>", { status: 502 })));
    const error = (await apiFetch("/posts").catch((e: unknown) => e)) as ApiError;
    expect(error.message).toContain("could not produce");
  });

  it("reports network failures without leaking technical details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = (await apiFetch("/health").catch((e: unknown) => e)) as ApiError;
    expect(error.code).toBe("network_error");
    expect(error.message).not.toContain("Failed to fetch");
  });

  it("clears the session and notifies the app on 401 for authenticated calls", async () => {
    setToken("expired");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(401, { error: { code: "unauthorized", message: "expired" } })));
    const listener = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, listener);
    await apiFetch("/users/me").catch(() => undefined);
    window.removeEventListener(AUTH_EXPIRED_EVENT, listener);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(window.localStorage.getItem("linkdine.token")).toBeNull();
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    await expect(apiFetch("/posts/1", { method: "DELETE" })).resolves.toBeUndefined();
  });
});

describe("errorMessage", () => {
  it("returns the message of ApiError and a generic one otherwise", () => {
    expect(errorMessage(new ApiError("Nice message", 400, "x"))).toBe("Nice message");
    expect(errorMessage(new Error("stack details"))).not.toContain("stack");
  });
});
