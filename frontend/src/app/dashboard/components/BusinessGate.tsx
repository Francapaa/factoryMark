"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthRequiredError } from "@/lib/api";
import { getMyBusiness, type MyBusiness } from "@/lib/businesses";

/** Gate del lado cliente: sin negocio guardado redirige a /onboarding. */
export default function BusinessGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [business, setBusiness] = useState<MyBusiness | null | undefined>(undefined);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    getMyBusiness()
      .then((b) => {
        if (!alive) return;
        if (b === null) {
          router.push("/onboarding");
          return;
        }
        setBusiness(b);
      })
      .catch((err) => {
        if (!alive) return;
        if (err instanceof AuthRequiredError) {
          router.push("/login");
          return;
        }
        setError(err instanceof Error ? err.message : "No pudimos cargar tu negocio");
      });
    return () => {
      alive = false;
    };
  }, [router, attempt]);

  if (error) {
    return (
      <div className="rounded-2xl border border-white/10 bg-black/50 p-5 text-center">
        <p className="text-sm text-zinc-400">{error}</p>
        <button
          type="button"
          onClick={() => {
            setBusiness(undefined);
            setError("");
            setAttempt((n) => n + 1);
          }}
          className="font-display mt-3 inline-flex h-9 items-center rounded-full bg-[#FF5C00] px-4 text-sm font-semibold text-[#0A0A0B]"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (business === undefined) {
    return <p className="text-sm text-zinc-500">Cargando tu negocio…</p>;
  }
  return <>{children}</>;
}
