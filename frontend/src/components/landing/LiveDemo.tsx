"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Search, Loader2, TrendingUp, FileCheck, ArrowRight } from "lucide-react";
import mock from "@/mocks/analyze.json";
import { Reveal } from "./Reveal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import CompetitorsTable from "@/components/CompetitorsTable";
import DraftPreview from "@/components/DraftPreview";

type Status = "idle" | "scanning" | "done";

const STEPS = ["Buscando locales de tu cuadra…", "Leyendo 400 opiniones…", "Buscando huecos…", "Armando tu post…"];

export function LiveDemo() {
  const [rubro, setRubro] = useState("café de especialidad");
  const [zona, setZona] = useState("Palermo Soho, Buenos Aires");
  const [status, setStatus] = useState<Status>("idle");
  const [stepIdx, setStepIdx] = useState(0);

  function run(e: React.FormEvent) {
    e.preventDefault();
    if (status === "scanning") return;
    setStatus("scanning");
    setStepIdx(0);
    STEPS.forEach((_, i) => {
      setTimeout(() => setStepIdx(i), 550 * (i + 1));
    });
    setTimeout(() => setStatus("done"), 550 * STEPS.length + 500);
  }

  return (
    <section id="demo" className="relative scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge variant="solid">Demo interactiva · datos de ejemplo</Badge>
          <h2 className="font-display mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Probá el flujo ahora mismo
          </h2>
          <p className="mt-4 text-zinc-400">
            Escribí tu rubro y tu zona. Vas a ver el mismo recorrido del producto: locales
            → oportunidades → post listo para aprobar.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="glass-dark noise relative mx-auto mt-10 max-w-4xl overflow-hidden rounded-3xl p-6 sm:p-9">
            <form onSubmit={run} className="flex flex-col gap-3 sm:flex-row">
              <label className="relative flex-1">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
                <input
                  value={rubro}
                  onChange={(e) => setRubro(e.target.value)}
                  placeholder="Rubro (ej: barbería)"
                  aria-label="Rubro"
                  className="w-full rounded-xl border border-white/10 bg-black/60 py-3 pl-10 pr-4 text-[15px] text-white placeholder:text-zinc-600 focus:border-[#FF5C00] focus:outline-none"
                />
              </label>
              <label className="relative flex-1">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
                <input
                  value={zona}
                  onChange={(e) => setZona(e.target.value)}
                  placeholder="Zona (ej: Villa Crespo)"
                  aria-label="Zona"
                  className="w-full rounded-xl border border-white/10 bg-black/60 py-3 pl-10 pr-4 text-[15px] text-white placeholder:text-zinc-600 focus:border-[#FF5C00] focus:outline-none"
                />
              </label>
              <Button type="submit" variant="primary" size="lg" disabled={status === "scanning"}>
                {status === "scanning" ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" /> Analizando…
                  </>
                ) : (
                  <>Analizar mi zona <ArrowRight className="h-5 w-5" /></>
                )}
              </Button>
            </form>

            <AnimatePresence mode="wait">
              {status === "scanning" && (
                <motion.div
                  key="scan"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="mt-6 rounded-2xl border border-[#FF5C00]/25 bg-black/50 p-5"
                >
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin text-[#FF5C00]" />
                    <p className="font-display font-semibold text-white">{STEPS[stepIdx]}</p>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/8">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-[#FF5C00] to-[#FFD9A3]"
                      animate={{ width: `${((stepIdx + 1) / STEPS.length) * 100}%` }}
                      transition={{ duration: 0.4 }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-zinc-500">
                    Analizando “{rubro}” en “{zona}” · mapas + opiniones públicas de tu zona
                  </p>
                </motion.div>
              )}

              {status === "done" && (
                <motion.div
                  key="done"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="mt-6 grid gap-4"
                >
                  <div className="rounded-2xl border border-white/10 bg-black/50 p-5">
                    <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
                      <TrendingUp className="h-3.5 w-3.5" /> Competidores detectados
                    </p>
                    <div className="mt-3 overflow-x-auto text-zinc-200 [&_th]:text-zinc-500 [&_td]:text-zinc-200 [&_tr]:border-white/10">
                      <CompetitorsTable competitors={mock.competitors} />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-2xl border border-[#FF5C00]/25 bg-[#FF5C00]/[0.06] p-5">
                      <p className="font-display text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
                        Oportunidades
                      </p>
                      <ul className="mt-3 flex flex-col gap-2.5">
                        {(mock.opportunities as { title: string; evidence: string; confidence: string }[]).map((o) => (
                          <li key={o.title} className="rounded-xl bg-black/50 p-3 text-sm">
                            <p className="font-medium text-white">{o.title}</p>
                            <p className="mt-1 text-xs text-zinc-500">{o.evidence} · confianza {o.confidence}</p>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/50 p-5 text-zinc-200 [&_p]:text-zinc-200 [&_.text-zinc-500]:text-zinc-500">
                      <p className="font-display flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
                        <FileCheck className="h-3.5 w-3.5" /> Post listo para aprobar
                      </p>
                      <div className="mt-3">
                        <DraftPreview
                          initial={mock.draft_post}
                          opportunityTitle={(mock.opportunities as { title: string }[])[0]?.title}
                        />
                      </div>
                    </div>
                  </div>
                  <p className="text-center text-xs text-zinc-600">
                    Datos de ejemplo para la demo. Conectá el backend para análisis reales de tu zona.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            {status === "idle" && (
              <p className="mt-6 text-center text-sm text-zinc-600">
                Tocá “Analizar mi zona” para simular el pipeline completo en ~3 segundos.
              </p>
            )}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
