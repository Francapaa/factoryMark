import { Flame } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative border-t border-white/10 bg-black/60 py-10 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-4 sm:flex-row sm:items-center sm:px-6">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#FF5C00]">
            <Flame className="h-4 w-4 text-[#0A0A0B]" strokeWidth={2.5} />
          </span>
          <div>
            <p className="font-display font-bold text-white">
              Factory<span className="text-[#FF5C00]">Mark</span>
            </p>
            <p className="text-xs text-zinc-500">Detectar → decidir → ejecutar.</p>
          </div>
        </div>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-zinc-500">
          <a href="#como-funciona" className="hover:text-[#FFB25C]">Cómo funciona</a>
          <a href="#demo" className="hover:text-[#FFB25C]">Demo</a>
          <a href="#casos" className="hover:text-[#FFB25C]">Casos</a>
          <a href="#faq" className="hover:text-[#FFB25C]">FAQ</a>
          <a href="/login" className="hover:text-[#FFB25C]">Entrar</a>
          <a href="/app" className="hover:text-[#FFB25C]">Dashboard</a>
        </nav>
        <p className="text-xs text-zinc-600">© 2026 FactoryMark · Hecho en Buenos Aires</p>
      </div>
    </footer>
  );
}
