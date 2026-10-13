"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthRequiredError } from "@/lib/api";
import { getMyBusiness } from "@/lib/businesses";

/** Gate del lado cliente: con negocio guardado redirige a /dashboard (1 perfil = 1 local). */
export default function OnboardingGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    getMyBusiness()
      .then((b) => {
        if (!alive) return;
        if (b !== null) {
          router.replace("/dashboard");
          return;
        }
        setChecked(true);
      })
      .catch((err) => {
        if (!alive) return;
        if (err instanceof AuthRequiredError) {
          router.push("/login");
          return;
        }
        setError(err instanceof Error ? err.message : "No pudimos verificar tu negocio");
      });
    return () => {
      alive = false;
    };
  }, [router, attempt]);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-3 py-6 text-center">
        <p className="text-sm text-zinc-500">{error}</p>
        <button
          type="button"
          onClick={() => {
            setChecked(false);
            setError("");
            setAttempt((n) => n + 1);
          }}
          className="rounded-lg bg-black px-5 py-2 font-medium text-white dark:bg-white dark:text-black"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!checked) {
    return <p className="py-6 text-center text-sm text-zinc-500">Verificando tu negocio…</p>;
  }
  return <>{children}</>;
}
