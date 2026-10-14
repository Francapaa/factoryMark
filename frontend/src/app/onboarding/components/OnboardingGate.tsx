"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { AuthRequiredError } from "@/lib/api";
import { getMyBusiness } from "@/lib/businesses";
import { Button } from "@/components/ui/button";

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
      <div className="flex flex-col items-center gap-4 py-8 text-center">
        <p className="rounded-2xl border border-[#FF5C00]/25 bg-[#FF5C00]/5 p-4 text-sm leading-relaxed text-zinc-300">
          {error}
        </p>
        <Button
          type="button"
          variant="primary"
          size="md"
          onClick={() => {
            setChecked(false);
            setError("");
            setAttempt((n) => n + 1);
          }}
        >
          <RotateCcw className="h-4 w-4" /> Reintentar
        </Button>
      </div>
    );
  }

  if (!checked) {
    return (
      <div className="flex flex-col items-center gap-4 py-10 text-center" aria-live="polite">
        <span className="h-11 w-11 animate-pulse rounded-2xl bg-[#FF5C00]/20 shadow-[0_0_24px_rgba(255,92,0,0.35)]" />
        <p className="text-sm text-zinc-500">Verificando tu negocio…</p>
      </div>
    );
  }
  return <>{children}</>;
}
