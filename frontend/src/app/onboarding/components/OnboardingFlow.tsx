"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AuthRequiredError } from "@/lib/api";
import {
  getPhotoObjectUrl,
  resolveBusiness,
  saveBusiness,
  type ResolvedBusiness,
} from "@/lib/businesses";
import type { SalesChannel } from "@/types/analysis";

const inputClassName =
  "flex-1 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800";

type Step = "form" | "confirm";

export default function OnboardingFlow() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [zone, setZone] = useState("");
  const [businessType, setBusinessType] = useState("café de especialidad");
  const [salesChannel, setSalesChannel] = useState<SalesChannel>("local");
  const [step, setStep] = useState<Step>("form");
  const [resolved, setResolved] = useState<ResolvedBusiness | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "saving" | "error">("idle");
  const [error, setError] = useState("");

  // Foto vía proxy autenticado (object URL, se revoca al cambiar de candidato).
  // photoUrl se resetea en onResolve/onReject; el efecto solo descarga.
  useEffect(() => {
    const ref = resolved?.photo_ref;
    if (!ref) return;
    let alive = true;
    let url: string | null = null;
    getPhotoObjectUrl(ref)
      .then((u) => {
        if (alive) {
          url = u;
          setPhotoUrl(u);
        } else {
          URL.revokeObjectURL(u);
        }
      })
      .catch(() => {
        if (alive) setPhotoUrl(null);
      });
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [resolved]);

  async function onResolve(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setError("");
    try {
      const found = await resolveBusiness(name, zone);
      setPhotoUrl(null);
      setResolved(found);
      setStep("confirm");
      setStatus("idle");
    } catch (err) {
      if (err instanceof AuthRequiredError) {
        router.push("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Error desconocido");
      setStatus("error");
    }
  }

  async function onConfirm() {
    if (!resolved) return;
    setStatus("saving");
    setError("");
    try {
      await saveBusiness({
        name: resolved.name,
        business_type: businessType,
        sales_channel: salesChannel,
        zone,
        anchor_place_id: resolved.place_id,
        anchor_snapshot: {
          address: resolved.address,
          latitude: resolved.latitude,
          longitude: resolved.longitude,
          rating: resolved.rating,
          photo_ref: resolved.photo_ref,
        },
      });
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof AuthRequiredError) {
        router.push("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Error desconocido");
      setStatus("error");
    }
  }

  function onReject() {
    // "No es este": no se guarda nada, el form conserva lo tipeado.
    setResolved(null);
    setPhotoUrl(null);
    setStep("form");
    setStatus("idle");
    setError("");
  }

  if (step === "confirm" && resolved) {
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold">¿Este es tu local?</h2>
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          {photoUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={photoUrl} alt={resolved.name} className="max-h-64 w-full object-cover" />
          )}
          <div className="flex flex-col gap-1 p-4">
            <p className="text-lg font-medium">{resolved.name}</p>
            <p className="text-sm text-zinc-500">{resolved.address}</p>
            {resolved.rating != null && (
              <p className="text-sm text-zinc-500">⭐ {resolved.rating}</p>
            )}
            {resolved.hours_summary.length > 0 && (
              <p className="text-sm text-zinc-500">{resolved.hours_summary[0]}</p>
            )}
            <a
              href={resolved.maps_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-medium text-blue-600 underline dark:text-blue-400"
            >
              Ver en Google Maps
            </a>
          </div>
        </div>
        {status === "error" && (
          <p className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onConfirm}
            disabled={status === "saving"}
            className="flex-1 rounded-lg bg-black px-5 py-2 font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
          >
            {status === "saving" ? "Guardando…" : "Confirmar, es mi local"}
          </button>
          <button
            type="button"
            onClick={onReject}
            disabled={status === "saving"}
            className="flex-1 rounded-lg border border-zinc-300 px-5 py-2 font-medium dark:border-zinc-700"
          >
            No es este
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold">¿Cuál es tu local?</h2>
      <p className="text-sm text-zinc-500">
        Lo buscamos en Google Maps una sola vez y lo guardamos para todos tus análisis.
      </p>
      <form onSubmit={onResolve} className="flex flex-col gap-3">
        <input
          className={inputClassName}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nombre de tu comercio (ej: Café Martínez)"
          aria-label="Nombre de tu comercio"
          required
        />
        <input
          className={inputClassName}
          value={zone}
          onChange={(e) => setZone(e.target.value)}
          placeholder="Zona (ej: Palermo Soho, Buenos Aires)"
          aria-label="Zona"
          required
        />
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className={inputClassName}
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            placeholder="Tipo de negocio"
            aria-label="Tipo de negocio"
            required
          />
          <select
            className="rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800"
            value={salesChannel}
            onChange={(e) => setSalesChannel(e.target.value as SalesChannel)}
            aria-label="Canal de venta"
          >
            <option value="local">Local (compite por cercanía)</option>
            <option value="online">Online (compite en web)</option>
            <option value="mixto">Mixto (ambos)</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-lg bg-black px-5 py-2 font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
        >
          {status === "loading" ? "Buscando…" : "Buscar mi local"}
        </button>
      </form>
      {status === "error" && (
        <p className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}
      <p className="text-xs text-zinc-400">
        ¿Ya tenés tu local guardado?{" "}
        <Link href="/dashboard" className="underline">
          Ir a la app
        </Link>
      </p>
    </div>
  );
}
