"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Check } from "lucide-react";
import { PIPELINE } from "@/lib/landing-data";
import { Reveal } from "./Reveal";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const Pipeline3D = dynamic(() => import("./three/Pipeline3D").then((m) => m.Pipeline3D), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse rounded-3xl bg-[#FF5C00]/5" />,
});

export function Pipeline() {
  const [active, setActive] = useState(2);

  return (
    <section id="como-funciona" className="relative scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge variant="ember">Paso a paso, sin humo</Badge>
          <h2 className="font-display mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Cinco pasos.
            <br />
            <span className="bg-gradient-to-r from-[#FF5C00] to-[#FFD9A3] bg-clip-text text-transparent">
              Un post listo.
            </span>
          </h2>
          <p className="mt-4 text-zinc-400">
            Cada paso usa lo que encontró el anterior, hasta dejarte el post armado. Tocá cada paso:
          </p>
        </Reveal>

        <div className="mt-12 grid items-stretch gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Reveal className="relative min-h-[380px] overflow-hidden rounded-3xl border border-[#FF5C00]/20 bg-black/40">
            <div className="absolute inset-0">
              <Pipeline3D active={active} />
            </div>
            <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between rounded-2xl border border-white/10 bg-black/60 px-4 py-3 backdrop-blur-md">
              <div>
                <p className="font-display text-[11px] font-semibold uppercase tracking-[0.2em] text-[#FFB25C]">
                  Red orbital · en vivo
                </p>
                <p className="text-sm font-medium text-white">
                  Nodo activo: {PIPELINE[active].name}
                </p>
              </div>
              <span
                className="h-3 w-3 animate-pulse-glow rounded-full"
                style={{ background: PIPELINE[active].accent, boxShadow: `0 0 16px ${PIPELINE[active].accent}` }}
              />
            </div>
          </Reveal>

          <div className="flex flex-col gap-2.5">
            {PIPELINE.map((step, i) => {
              const isActive = i === active;
              return (
                <button
                  key={step.id}
                  onClick={() => setActive(i)}
                  className={cn(
                    "group cursor-pointer rounded-2xl border p-5 text-left transition-all duration-300",
                    isActive
                      ? "border-[#FF5C00]/50 bg-[#1A1A1E]/95 shadow-[0_12px_48px_rgba(255,92,0,0.22)]"
                      : "border-white/8 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.05]"
                  )}
                >
                  <div className="flex items-center gap-4">
                    <span
                      className={cn(
                        "font-display grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-bold transition-all",
                        isActive ? "bg-[#FF5C00] text-[#0A0A0B]" : "bg-white/8 text-zinc-400"
                      )}
                    >
                      {step.n}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-display text-lg font-semibold text-white">{step.name}</h3>
                        {isActive && <Check className="h-4 w-4 text-emerald-400" />}
                      </div>
                      <p className="truncate text-sm text-zinc-500">{step.tagline}</p>
                    </div>
                    <ArrowRight
                      className={cn(
                        "h-4 w-4 shrink-0 transition-all",
                        isActive ? "translate-x-0 text-[#FF5C00] opacity-100" : "-translate-x-1 opacity-0 group-hover:translate-x-0 group-hover:opacity-60"
                      )}
                    />
                  </div>
                  <AnimatePresence initial={false}>
                    {isActive && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                        className="overflow-hidden"
                      >
                        <div className="grid gap-2.5 pt-4 sm:grid-cols-2">
                          <div className="rounded-xl bg-black/50 p-3.5 text-sm">
                            <p className="font-display text-[11px] font-semibold uppercase tracking-widest text-zinc-500">Entra</p>
                            <p className="mt-1 text-zinc-300">{step.input}</p>
                          </div>
                          <div
                            className="rounded-xl border p-3.5 text-sm"
                            style={{ borderColor: `${step.accent}55`, background: `${step.accent}0D` }}
                          >
                            <p className="font-display text-[11px] font-semibold uppercase tracking-widest" style={{ color: step.accent }}>
                              Sale
                            </p>
                            <p className="mt-1 text-zinc-200">{step.output}</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </button>
              );
            })}
          </div>
        </div>

        <Reveal delay={0.1} className="mt-8">
          <Card className="flex flex-col items-start gap-3 p-6 sm:flex-row sm:items-center">
            <p className="flex-1 text-sm leading-relaxed text-zinc-400">
              <span className="font-semibold text-white">¿Por qué no es un chat más?</span>{" "}
              Lee opiniones reales de tu zona, encuentra huecos concretos y te deja el post armado.
              Vos aprobás antes de que se publique nada.
            </p>
            <a href="#demo" className="font-display shrink-0 rounded-full bg-[#FF5C00] px-5 py-2.5 text-sm font-semibold text-[#0A0A0B] hover:bg-[#FF8A3D]">
              Probarlo ahora
            </a>
          </Card>
        </Reveal>
      </div>
    </section>
  );
}
