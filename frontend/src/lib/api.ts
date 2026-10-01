"use client";

import { authClient } from "@/lib/auth/client";

export class AuthRequiredError extends Error {
  constructor() {
    super("Sesión requerida");
    this.name = "AuthRequiredError";
  }
}

export class SessionTimeoutError extends Error {
  constructor() {
    super("La sesión tardó demasiado en responder. Recargá la página e intentá de nuevo.");
    this.name = "SessionTimeoutError";
  }
}

/** El JWT vive en la sesión (Neon lo inyecta vía header set-auth-jwt).
 * Un JWT real tiene 3 segmentos base64; los tokens opacos de sesión no.
 * Si viaja un opaco, el backend jamás podría validarlo: fallar acá con
 * mensaje claro en vez de cosechar un 401 mudo. */
export function isJwtShape(token: string): boolean {
  return token.split(".").length === 3 && token.length > 100;
}

const SESSION_TIMEOUT_MS = 8000;

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new SessionTimeoutError()), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

/** JWT de la sesión de Neon Auth. Siempre fresco: pedirlo antes de cada llamada.
 * Nunca cuelga en silencio: si la sesión no resuelve en 8s, lanza SessionTimeoutError. */
export async function getAccessToken(): Promise<string> {
  let session: Awaited<ReturnType<typeof authClient.getSession>> | null = null;
  let sessionError: unknown = null;
  try {
    const res = await withTimeout(authClient.getSession(), SESSION_TIMEOUT_MS);
    session = res.data;
    sessionError = res.error;
  } catch (err) {
    if (err instanceof SessionTimeoutError) throw err;
    throw new AuthRequiredError();
  }
  const token = (session?.session as { token?: unknown } | undefined)?.token;
  if (sessionError || typeof token !== "string" || !isJwtShape(token)) {
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
