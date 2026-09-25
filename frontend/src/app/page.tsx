import { redirect } from "next/navigation";
import AnalyzeForm from "@/components/AnalyzeForm";
import UserMenu from "@/components/UserMenu";
import { getAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

async function getHealth() {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${base}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as { status: string; app: string };
  } catch {
    return null;
  }
}

export default async function Home() {
  let user: { name?: string | null; email?: string | null; image?: string | null } | null = null;
  try {
    const { data: session } = await getAuth().getSession();
    user = session?.user ?? null;
  } catch {
    user = null;
  }
  if (!user) redirect("/login");

  const health = await getHealth();
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-2xl flex-col gap-6 rounded-2xl bg-white p-10 shadow-sm dark:bg-zinc-900">
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm font-medium uppercase tracking-widest text-zinc-500">
            FactoryMark · Setup
          </p>
          <UserMenu user={user} />
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
          Agente de Inteligencia Competitiva
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Pipeline: Researcher → Analyst → Strategist → Creator → Publisher.
          Backend FastAPI + frontend Next.js listos para la Fase 1.
        </p>
        <div className="rounded-xl border border-zinc-200 p-4 text-sm dark:border-zinc-800">
          <p className="font-medium">          Backend: {health ? `✅ ${health.app}` : "⚠️ no conectado (modo mock)"}</p>
          <p className="mt-1 text-zinc-500">
            {health
              ? "GET /health responde. Abajo podés probar el flujo con datos mock."
              : "Levantá el backend con `cd backend && uv run uvicorn factorymark.main:app --reload`, o usá el modo mock."}
          </p>
        </div>
        <AnalyzeForm />
      </main>
    </div>
  );
}
