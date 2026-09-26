import { Coffee, Scissors, Pizza, Store, Croissant, Beer } from "lucide-react";

const ITEMS = [
  { icon: Coffee, label: "Cafés de especialidad" },
  { icon: Scissors, label: "Barberías" },
  { icon: Pizza, label: "Pizzerías" },
  { icon: Croissant, label: "Panaderías" },
  { icon: Beer, label: "Bares" },
  { icon: Store, label: "Comercios" },
];

export function LogoMarquee() {
  const row = [...ITEMS, ...ITEMS];
  return (
    <section className="relative border-y border-white/8 bg-black/30 py-6 backdrop-blur-sm">
      <div className="mask-fade-x overflow-hidden">
        <div className="flex w-max animate-marquee gap-4 pr-4">
          {row.map((item, i) => (
            <div
              key={i}
              className="flex shrink-0 items-center gap-2.5 rounded-full border border-white/10 bg-white/[0.04] px-5 py-2.5 font-display text-sm font-medium text-zinc-300"
            >
              <item.icon className="h-4 w-4 text-[#FF5C00]" />
              {item.label}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
