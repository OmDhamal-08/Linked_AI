export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "Linkdine AI";

export const MOCK_PAYMENTS_ENABLED = process.env.NEXT_PUBLIC_ENABLE_MOCK_PAYMENTS === "true";

export const REQUEST_TIMEOUT_MS = 60_000;
