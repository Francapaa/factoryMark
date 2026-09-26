import { Clock, EyeOff, Megaphone } from "lucide-react";
import { Reveal } from "./Reveal";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const PAINS = [
  {
    icon: EyeOff,
    title: "No ves lo que pasa en tu cuadra",
    body: "Abren dos locales nuevos, cambian precios, suben promos… y te enterás tarde. Monitorear 12 competidores a mano es imposible.",
  },
  {
    icon: Clock,
    title: "Las opiniones se acumulan y nadie las lee",
    body: "400 reseñas con quejas de espera, frialdad o mala atención. El insight está ahí, pero no tenés 6 horas para leerlas.",
  },
  {
    icon: Megaphone,
    title: "El marketing queda para “cuando haya tiempo”",
    body: "Crear un post te lleva 3 horas entre copy, diseño y dudas. Resultado: publicás 1 vez por mes mientras tu competencia sube 5 por semana.",
  },
];

export function Problem() {
  return (
    <section className="relative py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge variant="ember">El problema</Badge>
          <h2 className="font-display mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Tu negocio es bueno.
            <br />
            <span className="text-zinc-500">Tu visibilidad, no.</span>
          </h2>
        </Reveal>
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {PAINS.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.12}>
              <Card className="group h-full p-7 transition-all duration-300 hover:-translate-y-1.5 hover:border-[#FF5C00]/40 hover:shadow-[0_20px_60px_rgba(255,92,0,0.18)]">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[#FF5C00]/12 text-[#FF8A3D] transition-colors group-hover:bg-[#FF5C00] group-hover:text-[#0A0A0B]">
                  <p.icon className="h-6 w-6" />
                </span>
                <h3 className="font-display mt-5 text-xl font-semibold text-white">{p.title}</h3>
                <p className="mt-2.5 leading-relaxed text-zinc-400">{p.body}</p>
              </Card>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
