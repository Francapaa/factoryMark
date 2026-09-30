"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthRequiredError } from "@/lib/api";
import { getMyBusiness, type MyBusiness } from "@/lib/businesses";

/** Gate del lado cliente: sin negocio guardado redirige a /onboarding. */
export default function BusinessGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [business, setBusiness] = useState<MyBusiness | null | undefined>(undefined);

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
        if (err instanceof AuthRequiredError) router.push("/login");
      });
    return () => {
      alive = false;
    };
  }, [router]);

  if (business === undefined) {
    return <p className="text-sm text-zinc-500">Cargando tu negocio…</p>;
  }
  return <>{children}</>;
}
