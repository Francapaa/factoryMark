"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Flame, MapPin, ShieldCheck, Star, Store } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import UserMenu, { type MenuUser } from "@/components/UserMenu";
import OnboardingFlow from "./OnboardingFlow";
import OnboardingGate from "./OnboardingGate";

const ease = [0.22, 1, 0.36, 1] as const;

function Rise({
  delay = 0,
  children,
  className,
}: {
  delay?: number;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay, ease }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export default function OnboardingScreen({ user }: { user: MenuUser }) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-[#0A0A0B]">
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute -top-40 left-1/2 h-[560px] w-[900px] -translate-x-1/2 rounded-full bg-[#FF5C00]/20 blur-[140px] animate-pulse-glow" />
        <div className="absolute top-[38%] -left-40 h-[480px] w-[480px] rounded-full bg-[#FF5C00]/12 blur-[120px]" />
        <div className="absolute -right-40 bottom-[-120px] h-[520px] w-[520px] rounded-full bg-[#FFB25C]/14 blur-[130px]" />
        <div className="absolute inset-0 bg-grid-orange opacity-60" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#0A0A0B] to-transparent" />
      </div>

      <Rise className="relative z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#FF5C00] shadow-[0_0_24px_rgba(255,92,0,0.55)]">
              <Flame className="h-5 w-5 text-[#0A0A0B]" strokeWidth={2.5} />
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-white">
              Factory<span className="text-[#FF5C00]">Mark</span>
            </span>
          </Link>
          <UserMenu user={user} />
        </div>
      </Rise>

      <main className="relative z-10 mx-auto grid w-full max-w-6xl flex-1 items-center gap-10 px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:pt-12">
        <div>
          <Rise delay={0.05}>
            <Badge variant="ember">
              <Store className="h-3 w-3" /> Onboarding · 2 minutos
            </Badge>
          </Rise>
          <Rise delay={0.12}>
            <h1 className="font-display mt-6 text-5xl font-bold leading-[0.95] tracking-tight text-white sm:text-6xl">
              Contanos cuál es
              <br />
              <span className="bg-gradient-to-r from-[#FF5C00] via-[#FF8A3D] to-[#FFD9A3] bg-clip-text text-transparent text-glow-orange">
                tu local.
              </span>
            </h1>
          </Rise>
          <Rise delay={0.2}>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-400">
              Lo buscamos en Google Maps{" "}
              <span className="font-semibold text-[#FFB25C]">una sola vez</span> y lo
              guardamos para todos tus análisis. Después investigamos tu zona y te dejamos el
              post listo.
            </p>
          </Rise>
          <Rise delay={0.28}>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-zinc-500">
              <span className="flex items-center gap-1.5">
                <Star className="h-4 w-4 fill-[#FF5C00] text-[#FF5C00]" /> 4.6★ en negocios piloto
              </span>
              <span>· 400+ opiniones por zona</span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-400" /> Nada se publica sin tu OK
              </span>
            </div>
          </Rise>

          <Rise delay={0.36} className="mt-8 hidden lg:block">
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="glass-dark inline-block rounded-2xl p-3.5 text-xs"
            >
              <p className="font-display font-semibold uppercase tracking-widest text-[#FFB25C]">
                Cómo funciona
              </p>
              <p className="mt-1 flex max-w-[280px] items-center gap-1.5 font-medium text-white">
                <MapPin className="h-3.5 w-3.5 shrink-0 text-[#FF5C00]" />
                Buscás tu local → confirmás → analizamos la zona
              </p>
              <p className="mt-1 text-emerald-400">1 perfil = 1 local</p>
            </motion.div>
          </Rise>
        </div>

        <Rise delay={0.18}>
          <motion.section
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.18, ease }}
            className="glass-dark noise relative rounded-[2rem] p-8 shadow-[0_8px_60px_rgba(0,0,0,0.5)] sm:p-10"
          >
            <div
              className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-[#FF5C00]/60 to-transparent"
              aria-hidden
            />
            <p className="font-display text-xs font-semibold uppercase tracking-[0.3em] text-[#FFB25C]">
              FactoryMark · Onboarding
            </p>
            <h2 className="font-display mt-3 text-3xl font-bold tracking-tight text-white">
              Registrá tu negocio
            </h2>

            <div className="mt-7">
              <OnboardingGate>
                <OnboardingFlow />
              </OnboardingGate>
            </div>
          </motion.section>
        </Rise>
      </main>
    </div>
  );
}
