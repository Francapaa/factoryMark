"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Quote, ArrowRight, TrendingUp, MapPin } from "lucide-react";
import { USE_CASES } from "@/lib/landing-data";
import { Reveal } from "./Reveal";
import { Badge } from "@/components/ui/badge";
import { CardAmber } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const Cases3D = dynamic(() => import("./three/Cases3D").then((m) => m.Cases3D), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse rounded-3xl bg-[#6B3A0A]/10" />,
});

/**
 * TRAMO ÁMBAR CLARO — fondo claro, texto oscuro, 3D de cristales dorados.
 * Es el quiebre visual de la landing: del negro al día soleado del éxito.
 */
export function UseCases() {
  const [active, setActive] = useState(USE_CASES[0].id);
  const current = USE_CASES.find((u) => u.id === active) ?? USE_CASES[0];

  return (
    <section id="casos" className="relative scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="overflow-hidden rounded-[2.5rem] border border-[#6B3A0A]/15 bg-[#FFF7ED]/95 shadow-[0_40px_120px_rgba(107,58,10,0.25)] backdrop-blur-xl">
          <div className="grid lg:grid-cols-[0.9fr_1.1fr]">
            {/* 3D ámbar */}
            <div className="relative min-h-[320px] bg-gradient-to-b from-[#FDE9C8] to-[#FFF7ED] lg:min-h-full">
              <div className="absolute inset-0">
                <Cases3D />
              </div>
              <div className="absolute left-6 top-6">
                <Badge variant="amber">Casos reales · negocios chicos</Badge>
              </div>
              <div className="absolute bottom-6 left-6 right-6 rounded-2xl border border-[#6B3A0A]/15 bg-white/70 p-4 backdrop-blur-md">
                <p className="flex items-center gap-2 font-display text-[11px] font-semibold uppercase tracking-[0.2em] text-[#92400E]">
                  <MapPin className="h-3.5 w-3.5" /> {current.negocio} · {current.zona}
                </p>
                <p className="font-display mt-1.5 text-xl font-bold leading-snug text-[#1C1917]">
                  “{current.quote}”
                </p>
                <p className="mt-1 text-sm text-[#78716C]">— {current.dueno}</p>
              </div>
            </div>

            {/* Contenido */}
            <div className="p-6 sm:p-10">
              <Reveal>
                <h2 className="font-display text-4xl font-bold tracking-tight text-[#1C1917] sm:text-[2.75rem] sm:leading-[1.02]">
                  Cómo mejoramos a tres negocios de barrio
                </h2>
                <p className="mt-3 text-[#78716C]">
                  No son slides de consultora: son huecos encontrados en opiniones + posts que se pueden
                  publicar + números de antes y después.
                </p>
              </Reveal>

              <div className="mt-6 flex flex-wrap gap-2">
                {USE_CASES.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => setActive(u.id)}
                    className={cn(
                      "cursor-pointer rounded-full border px-4 py-2 font-display text-sm font-semibold transition-all",
                      active === u.id
                        ? "border-[#1C1917] bg-[#1C1917] text-[#FFD9A3] shadow-lg"
                        : "border-[#6B3A0A]/20 bg-white/60 text-[#57534E] hover:border-[#1C1917]/40"
                    )}
                  >
                    {u.rubro}
                  </button>
                ))}
              </div>

              <AnimatePresence mode="wait">
                <motion.div
                  key={current.id}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -14 }}
                  transition={{ duration: 0.35 }}
                  className="mt-6"
                >
                  <div className="grid gap-3 text-sm">
                    <div className="rounded-2xl bg-white/70 p-4">
                      <p className="font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-[#B45309]">Problema</p>
                      <p className="mt-1 text-[#44403C]">{current.problema}</p>
                    </div>
                    <div className="rounded-2xl bg-[#1C1917] p-4 text-sm">
                      <p className="font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-[#FFB25C]">Hallazgo del agente</p>
                      <p className="mt-1 text-[#E7E5E4]">{current.hallazgo}</p>
                    </div>
                    <div className="rounded-2xl border-2 border-dashed border-[#B45309]/40 bg-[#FFFBEB] p-4">
                      <p className="font-display text-[11px] font-semibold uppercase tracking-[0.18em] text-[#B45309]">Acción ejecutada</p>
                      <p className="mt-1 font-medium text-[#1C1917]">{current.accion}</p>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    {current.metricas.map((m) => (
                      <div key={m.label} className="rounded-2xl border border-[#6B3A0A]/12 bg-white/80 p-4">
                        <p className="text-xs font-medium text-[#78716C]">{m.label}</p>
                        <p className="mt-1.5 text-xs text-[#A8A29E]">
                          <span className="line-through">{m.antes}</span> →{" "}
                          <span className="font-bold text-[#1C1917]">{m.despues}</span>
                        </p>
                        <p className="font-display mt-1 flex items-center gap-1 text-lg font-bold text-[#15803D]">
                          <TrendingUp className="h-4 w-4" /> {m.delta}
                        </p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              </AnimatePresence>

              <a
                href="#demo"
                className="font-display mt-6 inline-flex items-center gap-2 rounded-full bg-[#1C1917] px-6 py-3 text-sm font-semibold text-[#FFD9A3] transition-all hover:-translate-y-0.5 hover:shadow-xl"
              >
                Quiero esto para mi negocio <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>

        <Reveal delay={0.1}>
          <div className="mx-auto mt-6 flex max-w-3xl items-start gap-3 rounded-2xl border border-[#6B3A0A]/20 bg-[#1C1917]/85 p-4 text-sm text-[#E7E5E4] backdrop-blur-md">
            <Quote className="mt-0.5 h-4 w-4 shrink-0 text-[#FFB25C]" />
            <p>
              Métricas ilustrativas basadas en patrones reales de opiniones de la demo. Cuando conectes
              tu zona, calculamos las tuyas con datos reales.
            </p>
          </div>
        </Reveal>

        {/* Resultados / contadores */}
        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { v: "+72%", l: "visitas en horario hueco (café)" },
            { v: "-97%", l: "tiempo creando contenido" },
            { v: "5 min", l: "de dato a post listo" },
            { v: "400+", l: "opiniones leídas por zona" },
          ].map((s, i) => (
            <Reveal key={s.l} delay={i * 0.08}>
              <CardAmber className="p-6 text-center">
                <p className="font-display text-4xl font-bold text-[#1C1917]">{s.v}</p>
                <p className="mt-1.5 text-sm text-[#78716C]">{s.l}</p>
              </CardAmber>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
