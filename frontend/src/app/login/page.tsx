import { redirect } from "next/navigation";
import { getAuth } from "@/lib/auth/server";
import { LoginCard } from "./components/LoginCard";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  let configured = true;
  let authError = false;
  let user: unknown = null;
  try {
    const { data: session } = await getAuth().getSession();
    user = session?.user ?? null;
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[login] getSession failed", {
      hasBaseUrl: !!process.env.NEON_AUTH_BASE_URL,
      hasCookieSecret: !!process.env.NEON_AUTH_COOKIE_SECRET,
      baseUrlLen: process.env.NEON_AUTH_BASE_URL?.length ?? 0,
      error: msg,
    });
    authError = !msg.includes("Falta configuración");
    configured = false;
  }

  // Fuera del try: redirect() interrumpe con NEXT_REDIRECT y el catch no debe tragarlo.
  // Con negocio guardado va al dashboard (el BusinessGate devuelve a /onboarding si falta).
  if (user) redirect("/dashboard");

  return <LoginCard configured={configured} authError={authError} />;
}
