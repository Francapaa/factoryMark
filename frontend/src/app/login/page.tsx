import { redirect } from "next/navigation";
import Link from "next/link";
import GoogleSignInButton from "@/components/GoogleSignInButton";
import { getAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function LoginPage() {
  let configured = true;
  try {
    const { data: session } = await getAuth().getSession();
    if (session?.user) redirect("/app");
  } catch {
    configured = false;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-md flex-col gap-6 rounded-2xl bg-white p-10 shadow-sm dark:bg-zinc-900">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-500">
          FactoryMark · Ingreso
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
          Tu espía legal de la competencia
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Ingresá con tu cuenta de Google para analizar tu zona y generar tu marketing.
          Si es tu primera vez, la cuenta se crea sola: no hay formularios ni contraseñas.
        </p>
        {!configured ? (
          <div className="flex flex-col gap-3">
            <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-600 dark:border-zinc-800 dark:bg-zinc-800/50 dark:text-zinc-400">
              El login con Google aún no está configurado en este entorno (faltan{" "}
              <code>NEON_AUTH_BASE_URL</code> y <code>NEON_AUTH_COOKIE_SECRET</code>).
              Mientras tanto podés explorar la landing y la demo.
            </div>
            <Link
              href="/#demo"
              className="rounded-lg bg-black px-5 py-3 text-center font-medium text-white dark:bg-white dark:text-black"
            >
              Ver la demo
            </Link>
          </div>
        ) : (
          <GoogleSignInButton />
        )}
        <p className="text-xs text-zinc-400">
          Solo pedimos tu nombre y email de Google para identificar tu cuenta. Nada se publica sin tu
          aprobación.
        </p>
      </main>
    </div>
  );
}
