"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Flame, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { href: "#como-funciona", label: "Cómo funciona" },
    { href: "#demo", label: "Demo" },
    { href: "#casos", label: "Casos" },
    { href: "#faq", label: "FAQ" },
  ];

  return (
    <motion.header
      initial={{ y: -70, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className="fixed inset-x-0 top-0 z-50"
    >
      <div
        className={cn(
          "mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 transition-all duration-300 sm:px-6",
          scrolled ? "py-2" : "py-4"
        )}
      >
        <div
          className={cn(
            "flex w-full items-center justify-between gap-4 rounded-2xl border px-4 py-2.5 transition-all",
            scrolled
              ? "border-[#FF5C00]/25 bg-[#0A0A0B]/85 shadow-[0_8px_40px_rgba(0,0,0,0.5)] backdrop-blur-xl"
              : "border-white/10 bg-[#0A0A0B]/40 backdrop-blur-lg"
          )}
        >
          <a href="#top" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#FF5C00] shadow-[0_0_24px_rgba(255,92,0,0.55)]">
              <Flame className="h-5 w-5 text-[#0A0A0B]" strokeWidth={2.5} />
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-white">
              Factory<span className="text-[#FF5C00]">Mark</span>
            </span>
          </a>
          <nav className="hidden items-center gap-7 md:flex">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="font-display text-sm font-medium text-zinc-400 transition-colors hover:text-[#FFB25C]"
              >
                {l.label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <a href="/login" className="hidden sm:block">
              <Button variant="ghost" size="sm">
                Entrar
              </Button>
            </a>
            <a href="#demo">
              <Button variant="primary" size="sm">
                Probar demo <ArrowRight className="h-4 w-4" />
              </Button>
            </a>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
