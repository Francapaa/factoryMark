"use client";

import { authClient } from "@/lib/auth/client";

export class AuthRequiredError extends Error {
  constructor() {
    super("Sesión requerida");
    this.name = "AuthRequiredError";
  }
}

/** El JWT vive en la sesión (Neon lo inyecta vía header set-auth-jwt).
 * Un JWT real tiene 3 segmentos base64; los tokens opacos de sesión no.
 * Si viaja un opaco, el backend jamás podría validarlo: fallar acá con
 * mensaje claro en vez de cosechar un 401 mudo. */
export function isJwtShape(token: string): boolean {
  return token.split(".").length === 3 && token.length > 100;
}

/** JWT de la sesión de Neon Auth. Siempre fresco: pedirlo antes de cada llamada. */
export async function getAccessToken(): Promise<string> {
  const { data, error } = await authClient.getSession();
  const token = (data?.session as { token?: unknown } | undefined)?.token;
  if (error || typeof token !== "string" || !isJwtShape(token)) {
    throw new AuthRequiredError();
  }
  return token;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** fetch al backend FastAPI con Bearer JWT. Lanza AuthRequiredError si hay 401. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await getAccessToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...(init.headers ?? {}), Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) throw new AuthRequiredError();
  return res;
}
