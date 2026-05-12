/**
 * Wrapper sobre fetch.
 * - Inyecta `Authorization: Bearer <token>` desde el auth store.
 * - Parsea errores de FastAPI (string o array de ValidationError).
 * - En 401, limpia sesión y redirige a /login.
 */

import { useAuthStore } from "@/lib/auth/store";

const BASE_URL = import.meta.env.PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public payload?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isUnauthorized() {
    return this.status === 401;
  }

  get isForbidden() {
    return this.status === 403;
  }
}

interface ApiOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Si true, no manda Authorization header (útil para /auth/login). */
  skipAuth?: boolean;
}

function detailToMessage(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts: string[] = [];
    for (const item of detail) {
      if (item && typeof item === "object") {
        const i = item as { loc?: unknown[]; msg?: string };
        const field = (i.loc ?? [])
          .filter((x) => x !== "body" && x !== "query" && x !== "path")
          .join(".");
        const msg = i.msg ?? "valor inválido";
        parts.push(field ? `${field}: ${msg}` : msg);
      }
    }
    if (parts.length) return parts.join("; ");
  }
  return "Error de validación";
}

export async function apiFetch<T = unknown>(
  path: string,
  { body, skipAuth, headers, ...rest }: ApiOptions = {},
): Promise<T> {
  const token = skipAuth ? null : useAuthStore.getState().token;
  const init: RequestInit = {
    ...rest,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers ?? {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  };

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch (err) {
    throw new ApiError(0, `No se pudo conectar al servidor: ${(err as Error).message}`);
  }

  if (response.status === 401) {
    useAuthStore.getState().logout();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Sesión expirada");
  }

  if (!response.ok) {
    let payload: unknown = null;
    let detail: unknown = null;
    try {
      payload = await response.json();
      detail = (payload as { detail?: unknown })?.detail ?? payload;
    } catch {
      try {
        payload = await response.text();
        detail = payload;
      } catch {
        detail = "Error desconocido";
      }
    }
    throw new ApiError(response.status, detailToMessage(detail), payload);
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const api = {
  get: <T>(path: string, opts?: Omit<ApiOptions, "body" | "method">) =>
    apiFetch<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: Omit<ApiOptions, "body" | "method">) =>
    apiFetch<T>(path, { ...opts, method: "POST", body }),
  put: <T>(path: string, body?: unknown, opts?: Omit<ApiOptions, "body" | "method">) =>
    apiFetch<T>(path, { ...opts, method: "PUT", body }),
  patch: <T>(path: string, body?: unknown, opts?: Omit<ApiOptions, "body" | "method">) =>
    apiFetch<T>(path, { ...opts, method: "PATCH", body }),
  delete: <T>(path: string, opts?: Omit<ApiOptions, "body" | "method">) =>
    apiFetch<T>(path, { ...opts, method: "DELETE" }),
};
