import { createNeonAuth } from "@neondatabase/auth/next/server";
import type { NeonAuth } from "@neondatabase/auth/next/server";

let instance: NeonAuth | null = null;

/** Singleton lazy: no revienta el build si falta el .env, falla con mensaje claro en runtime. */
export function getAuth(): NeonAuth {
  if (instance) return instance;
  const baseUrl = process.env.NEON_AUTH_BASE_URL;
  const secret = process.env.NEON_AUTH_COOKIE_SECRET;
  if (!baseUrl || !secret) {
    throw new Error(
      "Falta configuración de Neon Auth: definí NEON_AUTH_BASE_URL y " +
        "NEON_AUTH_COOKIE_SECRET en frontend/.env.local (ver .env.local.example)."
    );
  }
  instance = createNeonAuth({ baseUrl, cookies: { secret } });
  return instance;
}
