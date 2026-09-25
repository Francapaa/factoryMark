"use client";

import { authClient } from "@/lib/auth/client";

export class AuthRequiredError extends Error {
  constructor() {
    super("Sesión requerida");
    this.name = "AuthRequiredError";
  }
}

/** JWT corto de Neon Auth (EdDSA, 15 min). Siempre fresco: pedirlo antes de cada llamada. */
export async function getAccessToken(): Promise<string> {
  const { data, error } = await authClient.token();
  const token = (data as { token?: string } | null)?.token;
  if (error || !token) throw new AuthRequiredError();
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
