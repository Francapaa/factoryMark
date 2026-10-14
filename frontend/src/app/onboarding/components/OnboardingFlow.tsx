"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  Check,
  ExternalLink,
  Globe,
  Loader2,
  MapPin,
  Search,
  Star,
  Store,
} from "lucide-react";
import { AuthRequiredError } from "@/lib/api";
import {
  getPhotoObjectUrl,
  resolveBusiness,
  saveBusiness,
  type ResolvedBusiness,
} from "@/lib/businesses";
import type { SalesChannel } from "@/types/analysis";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ease = [0.22, 1, 0.36, 1] as const;

const inputClassName =
  "w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-[15px] text-white placeholder:text-zinc-500 outline-none transition focus:border-[#FF5C00]/60 focus:bg-white/[0.05] focus:ring-2 focus:ring-[#FF5C00]/20";

const labelClassName =
  "font-display text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500";

type Step = "form" | "confirm";

const STEPS = ["Buscá tu local", "Confirmá"];

function Stepper({ step }: { step: Step }) {
  const activeIndex = step === "form" ? 0 : 1;
  return (
    <div className="flex items-center gap-2" aria-label="Progreso del onboarding">
      {STEPS.map((label, i) => {
        const done = activeIndex > i;
        const active = activeIndex === i;
        return (
          <div key={label} className="flex flex-1 items-center gap-2 last:flex-none">
            <span
              className={cn(
                "font-display grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-bold transition-all",
                done && "bg-emerald-500/20 text-emerald-400",
                active && !done && "bg-[#FF5C00] text-[#0A0A0B] shadow-[0_0_16px_rgba(255,92,0,0.5)]",
                !done && !active && "bg-white/5 text-zinc-500"
              )}
            >
              {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </span>
            <span
              className={cn(
                "font-display hidden text-xs font-medium sm:block",
                active ? "text-white" : "text-zinc-500"
              )}
            >
              {label}
            </span>
            {i < STEPS.length - 1 && <span className="h-px flex-1 bg-white/10" aria-hidden />}
          </div>
        );
      })}
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <p className="rounded-2xl border border-[#FF5C00]/30 bg-[#FF5C00]/10 p-4 text-sm leading-relaxed text-[#FFD9A3]">
      {message}
    </p>
  );
}

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

  return (
    <div className="flex flex-col gap-6">
      <Stepper step={step} />
      <AnimatePresence mode="wait" initial={false}>
        {step === "confirm" && resolved ? (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.35, ease }}
            className="flex flex-col gap-4"
          >
            <div>
              <h3 className="font-display text-xl font-semibold text-white">
                ¿Este es tu local?
              </h3>
              <p className="mt-1 text-sm text-zinc-500">
                Confirmalo y arrancamos con el análisis de tu zona.
              </p>
            </div>
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/50">
              {photoUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={photoUrl}
                  alt={resolved.name}
                  className="max-h-56 w-full object-cover"
                />
              )}
              <div className="flex flex-col gap-1.5 p-5">
                <p className="font-display text-lg font-semibold text-white">
                  {resolved.name}
                </p>
                <p className="flex items-start gap-1.5 text-sm text-zinc-400">
                  <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-[#FF5C00]" />
                  {resolved.address}
                </p>
                {resolved.rating != null && (
                  <p className="flex items-center gap-1.5 text-sm text-zinc-400">
                    <Star className="h-4 w-4 fill-[#FF5C00] text-[#FF5C00]" />
                    {resolved.rating}
                  </p>
                )}
                {resolved.hours_summary.length > 0 && (
                  <p className="text-sm text-zinc-500">{resolved.hours_summary[0]}</p>
                )}
                <a
                  href={resolved.maps_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 flex items-center gap-1.5 text-sm font-medium text-[#FFB25C] underline-offset-4 transition-colors hover:text-[#FFD9A3] hover:underline"
                >
                  Ver en Google Maps <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
            {status === "error" && <ErrorBox message={error} />}
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                type="button"
                variant="primary"
                size="md"
                onClick={onConfirm}
                disabled={status === "saving"}
                className="flex-1"
              >
                {status === "saving" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Guardando…
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" /> Confirmar, es mi local
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="dark"
                size="md"
                onClick={onReject}
                disabled={status === "saving"}
                className="flex-1"
              >
                No es este
              </Button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="form"
            initial={{ opacity: 0, x: -24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 24 }}
            transition={{ duration: 0.35, ease }}
            className="flex flex-col gap-4"
          >
            <div>
              <h3 className="font-display text-xl font-semibold text-white">
                ¿Cuál es tu local?
              </h3>
              <p className="mt-1 text-sm leading-relaxed text-zinc-500">
                Lo buscamos en Google Maps una sola vez y lo guardamos para todos tus
                análisis.
              </p>
            </div>
            <form onSubmit={onResolve} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="onboarding-name" className={labelClassName}>
                  <span className="flex items-center gap-1.5">
                    <Store className="h-3.5 w-3.5 text-[#FF5C00]" /> Nombre de tu comercio
                  </span>
                </label>
                <input
                  id="onboarding-name"
                  className={inputClassName}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej: Café Martínez"
                  aria-label="Nombre de tu comercio"
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="onboarding-zone" className={labelClassName}>
                  <span className="flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-[#FF5C00]" /> Zona
                  </span>
                </label>
                <input
                  id="onboarding-zone"
                  className={inputClassName}
                  value={zone}
                  onChange={(e) => setZone(e.target.value)}
                  placeholder="Ej: Palermo Soho, Buenos Aires"
                  aria-label="Zona"
                  required
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="onboarding-type" className={labelClassName}>
                    Tipo de negocio
                  </label>
                  <input
                    id="onboarding-type"
                    className={inputClassName}
                    value={businessType}
                    onChange={(e) => setBusinessType(e.target.value)}
                    placeholder="Tipo de negocio"
                    aria-label="Tipo de negocio"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="onboarding-channel" className={labelClassName}>
                    <span className="flex items-center gap-1.5">
                      <Globe className="h-3.5 w-3.5 text-[#FF5C00]" /> Canal de venta
                    </span>
                  </label>
                  <select
                    id="onboarding-channel"
                    className={cn(inputClassName, "[&>option]:bg-[#1A1A1E] [&>option]:text-white")}
                    value={salesChannel}
                    onChange={(e) => setSalesChannel(e.target.value as SalesChannel)}
                    aria-label="Canal de venta"
                  >
                    <option value="local">Local (compite por cercanía)</option>
                    <option value="online">Online (compite en web)</option>
                    <option value="mixto">Mixto (ambos)</option>
                  </select>
                </div>
              </div>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={status === "loading"}
                className="w-full"
              >
                {status === "loading" ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" /> Buscando…
                  </>
                ) : (
                  <>
                    <Search className="h-5 w-5" /> Buscar mi local{" "}
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </Button>
            </form>
            {status === "error" && <ErrorBox message={error} />}
            <p className="text-xs text-zinc-500">
              ¿Ya tenés tu local guardado?{" "}
              <Link
                href="/dashboard"
                className="font-medium text-[#FFB25C] underline-offset-4 transition-colors hover:text-[#FFD9A3] hover:underline"
              >
                Ir a la app
              </Link>
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
