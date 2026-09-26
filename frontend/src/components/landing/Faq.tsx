"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Plus } from "lucide-react";
import { FAQS } from "@/lib/landing-data";
import { Reveal } from "./Reveal";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="relative scroll-mt-24 py-20 sm:py-24">
      <div className="mx-auto max-w-3xl px-4 sm:px-6">
        <Reveal className="text-center">
          <Badge variant="ember">Preguntas posta</Badge>
          <h2 className="font-display mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Lo que todo dueño pregunta
          </h2>
        </Reveal>
        <div className="mt-10 flex flex-col gap-3">
          {FAQS.map((f, i) => {
            const isOpen = open === i;
            return (
              <Reveal key={f.q} delay={i * 0.05}>
                <button
                  onClick={() => setOpen(isOpen ? null : i)}
                  className={cn(
                    "w-full cursor-pointer rounded-2xl border p-5 text-left transition-all",
                    isOpen
                      ? "border-[#FF5C00]/45 bg-[#1A1A1E]"
                      : "border-white/10 bg-white/[0.02] hover:border-white/25"
                  )}
                >
                  <div className="flex items-center justify-between gap-4">
                    <h3 className="font-display text-[17px] font-semibold text-white">{f.q}</h3>
                    <span
                      className={cn(
                        "grid h-8 w-8 shrink-0 place-items-center rounded-full transition-all",
                        isOpen ? "rotate-45 bg-[#FF5C00] text-[#0A0A0B]" : "bg-white/8 text-zinc-300"
                      )}
                    >
                      <Plus className="h-4 w-4" />
                    </span>
                  </div>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <p className="pt-3 leading-relaxed text-zinc-400">{f.a}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </button>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
