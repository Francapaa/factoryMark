"use client";

import dynamic from "next/dynamic";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { Reveal } from "./Reveal";
import { Button } from "@/components/ui/button";

const Final3D = dynamic(() => import("./three/Final3D").then((m) => m.Final3D), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-[#FF5C00]/5" />,
});

export function FinalCta() {
  return (
    <section className="relative overflow-hidden py-20 sm:py-28">
      <div className="absolute inset-0 opacity-70">
        <Final3D />
      </div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#0A0A0B]" />
      <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
        <Reveal>
          <p className="font-display text-xs font-semibold uppercase tracking-[0.3em] text-[#FFB25C]">
            Fase 1 · Demo técnica viva
          </p>
          <h2 className="font-display mt-4 text-5xl font-bold leading-[0.95] tracking-tight text-white sm:text-6xl">
            Tu cuadra ya se movió.
            <br />
            <span className="bg-gradient-to-r from-[#FF5C00] to-[#FFD9A3] bg-clip-text text-transparent text-glow-orange">
              Movete vos.
            </span>
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-lg text-zinc-400">
            Pasame tu rubro y tu zona. En minutos tenés competidores, huecos y un post con tu marca.
            Vos aprobás, nosotros ejecutamos.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <a href="#demo">
              <Button variant="primary" size="xl">
                Analizar mi zona gratis <ArrowRight className="h-5 w-5" />
              </Button>
            </a>
            <a href="/login">
              <Button variant="dark" size="xl">
                Entrar con Google
              </Button>
            </a>
          </div>
          <p className="mt-6 flex items-center justify-center gap-2 text-sm text-zinc-500">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Legal · Human-in-the-loop · Nada se publica sin tu OK
          </p>
        </Reveal>
      </div>
    </section>
  );
}
