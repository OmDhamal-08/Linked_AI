/**
 * Session token storage. The token is a user session credential (not a server secret).
 * For production hardening, move it to an httpOnly cookie set by a server route handler.
 */
const TOKEN_KEY = "linkdine.token";

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Storage can be blocked (private mode); the user will simply need to log in again.
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Nothing else to do.
  }
}

export const AUTH_EXPIRED_EVENT = "auth:expired";
