"use client";

import dynamic from "next/dynamic";
import { motion, useScroll, useTransform } from "framer-motion";
import { ArrowRight, Play, Star, MapPin } from "lucide-react";
import { useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const Hero3D = dynamic(() => import("./three/Hero3D").then((m) => m.Hero3D), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse rounded-3xl bg-[#FF5C00]/5" />,
});

export function Hero() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y3d = useTransform(scrollYProgress, [0, 1], [0, 140]);
  const fade = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.92]);

  return (
    <section id="top" ref={ref} className="relative overflow-hidden pt-32 pb-16 sm:pt-40 sm:pb-24">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.div style={{ opacity: fade }} className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="flex flex-wrap items-center gap-2"
          >
            <Badge variant="ember">
              <MapPin className="h-3 w-3" /> Para negocios de barrio
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="font-display mt-6 text-5xl font-bold leading-[0.95] tracking-tight text-white sm:text-7xl"
          >
            Tu competencia habla.
            <br />
            <span className="bg-gradient-to-r from-[#FF5C00] via-[#FF8A3D] to-[#FFD9A3] bg-clip-text text-transparent text-glow-orange">
              Nosotros la escuchamos.
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-400"
          >
            FactoryMark investiga tu cuadra, lee cientos de opiniones por vos y te deja el{" "}
            <span className="font-semibold text-[#FFB25C]">post listo para publicar</span> en 5
            minutos. Detectar → decidir → ejecutar.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <a href="#demo">
              <Button variant="primary" size="xl">
                <Play className="h-5 w-5" /> Ver demo en vivo
              </Button>
            </a>
            <a href="/login">
              <Button variant="dark" size="xl">
                Entrar con Google <ArrowRight className="h-5 w-5" />
              </Button>
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-zinc-500"
          >
            <span className="flex items-center gap-1.5">
              <Star className="h-4 w-4 fill-[#FF5C00] text-[#FF5C00]" /> 4.6★ en negocios piloto
            </span>
            <span>· 400+ opiniones por zona</span>
            <span>· Nada se publica sin tu OK</span>
          </motion.div>
        </motion.div>

        <motion.div style={{ y: y3d, scale }} className="relative z-10 h-[420px] sm:h-[540px]">
          <div className="absolute inset-0 rounded-[2rem] border border-[#FF5C00]/20 bg-gradient-to-b from-[#FF5C00]/10 to-transparent" />
          <div className="absolute inset-0">
            <Hero3D />
          </div>
          <motion.div
            animate={{ y: [0, -12, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            className="glass-dark absolute left-4 top-8 rounded-2xl p-3.5 text-xs"
          >
            <p className="font-display font-semibold uppercase tracking-widest text-[#FFB25C]">Hueco detectado</p>
            <p className="mt-1 max-w-[190px] font-medium text-white">“0/40 opiniones hablan de merienda de tarde”</p>
            <p className="mt-1 text-emerald-400">Confianza: alta</p>
          </motion.div>
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="glass-dark absolute bottom-8 right-4 rounded-2xl p-3.5 text-xs"
          >
            <p className="font-display font-semibold uppercase tracking-widest text-[#FFB25C]">Post listo</p>
            <p className="mt-1 max-w-[200px] font-medium text-white">“Tarde sin espera en Café Ejemplo ☕ 16–19h”</p>
            <p className="mt-1 text-zinc-400">#consumelocal #barrio</p>
          </motion.div>
        </motion.div>
      </div>

    </section>
  );
}
