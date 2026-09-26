import { Star } from "lucide-react";
import { Reveal } from "./Reveal";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

const ITEMS = [
  {
    name: "Martina G.",
    role: "Café Ejemplo · Palermo",
    text: "Pensé que necesitaba una agencia. Resulta que necesitaba que alguien leyera mis opiniones. El post de la tarde se hizo en minutos y funcionó.",
    stars: 5,
  },
  {
    name: "Damián R.",
    role: "Navaja & Co. · Villa Crespo",
    text: "Lo de las reservas por WhatsApp nos cambió los sábados. Ningún competidor lo tenía visible y el agente lo vio antes que nosotros.",
    stars: 5,
  },
  {
    name: "Lucía F.",
    role: "Forno Barrial · Caballito",
    text: "Lo de 'llega fría' dolió pero era verdad. Cambiamos packaging, publicamos 3 veces por semana y el delivery explotó.",
    stars: 5,
  },
];

export function Testimonials() {
  return (
    <section className="relative py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge variant="ember">Dueños, no influencers</Badge>
          <h2 className="font-display mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Barrios que ya espían legal
          </h2>
        </Reveal>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {ITEMS.map((t, i) => (
            <Reveal key={t.name} delay={i * 0.1}>
              <Card className="flex h-full flex-col p-7 transition-all hover:-translate-y-1 hover:border-[#FF5C00]/40">
                <div className="flex gap-1">
                  {Array.from({ length: t.stars }).map((_, s) => (
                    <Star key={s} className="h-4 w-4 fill-[#FF5C00] text-[#FF5C00]" />
                  ))}
                </div>
                <p className="mt-4 flex-1 leading-relaxed text-zinc-300">“{t.text}”</p>
                <div className="mt-5 border-t border-white/10 pt-4">
                  <p className="font-display font-semibold text-white">{t.name}</p>
                  <p className="text-sm text-zinc-500">{t.role}</p>
                </div>
              </Card>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
