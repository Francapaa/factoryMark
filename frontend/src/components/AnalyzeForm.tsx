"use client";

import { useState } from "react";
import mock from "@/mocks/analyze.json";
import CompetitorsTable from "./CompetitorsTable";
import DraftPreview from "./DraftPreview";

type Status = "idle" | "loading" | "done";

export default function AnalyzeForm() {
  const [businessType, setBusinessType] = useState("café de especialidad");
  const [zone, setZone] = useState("Palermo Soho, Buenos Aires");
  const [status, setStatus] = useState<Status>("idle");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setTimeout(() => setStatus("done"), 600); // simula análisis
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800"
          value={businessType}
          onChange={(e) => setBusinessType(e.target.value)}
          placeholder="Tipo de negocio"
          aria-label="Tipo de negocio"
        />
        <input
          className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800"
          value={zone}
          onChange={(e) => setZone(e.target.value)}
          placeholder="Zona"
          aria-label="Zona"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-lg bg-black px-5 py-2 font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
        >
          {status === "loading" ? "Analizando…" : "Analizar"}
        </button>
      </form>

      {status === "done" && (
        <div className="flex flex-col gap-6">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Competidores (mock)</h2>
            <CompetitorsTable competitors={mock.competitors} />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Oportunidades (mock)</h2>
            <ul className="flex flex-col gap-2">
              {mock.opportunities.map((o) => (
                <li key={o.title} className="rounded-xl border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                  <p className="font-medium">{o.title}</p>
                  <p className="text-zinc-500">{o.evidence} · {o.confidence}</p>
                </li>
              ))}
            </ul>
          </section>
          <DraftPreview initial={mock.draft_post} />
        </div>
      )}
    </div>
  );
}
