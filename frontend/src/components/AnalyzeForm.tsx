"use client";

import { useRouter } from "next/navigation";
import { useReducer } from "react";
import { AuthRequiredError, apiFetch } from "@/lib/api";
import {
  analyzeFormReducer,
  initialAnalyzeFormState,
  type AnalyzeResult,
} from "@/types/analysis";
import CompetitorsTable from "./CompetitorsTable";
import DraftPreview from "./DraftPreview";

const inputClassName =
  "flex-1 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800";

export default function AnalyzeForm() {
  const router = useRouter();
  const [state, dispatch] = useReducer(analyzeFormReducer, initialAnalyzeFormState);
  const { businessName, businessType, zone, salesChannel, status, error, result } = state;

  function setField(field: "businessName" | "businessType" | "zone" | "salesChannel") {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      dispatch({ type: "setField", field, value: e.target.value });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    dispatch({ type: "submit" });
    try {
      const res = await apiFetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName,
          business_type: businessType,
          zone,
          sales_channel: salesChannel,
        }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
        const detail =
          typeof body?.detail === "string" ? body.detail : `Error ${res.status}`;
        throw new Error(detail);
      }
      dispatch({ type: "success", result: (await res.json()) as AnalyzeResult });
    } catch (err) {
      if (err instanceof AuthRequiredError) {
        router.push("/login");
        return;
      }
      dispatch({
        type: "failure",
        error: err instanceof Error ? err.message : "Error desconocido",
      });
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className={inputClassName}
            value={businessName}
            onChange={setField("businessName")}
            placeholder="Tu comercio (ej: Café Martínez)"
            aria-label="Nombre de tu comercio"
            required
          />
          <input
            className={inputClassName}
            value={businessType}
            onChange={setField("businessType")}
            placeholder="Tipo de negocio"
            aria-label="Tipo de negocio"
            required
          />
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className={inputClassName}
            value={zone}
            onChange={setField("zone")}
            placeholder="Zona"
            aria-label="Zona"
            required
          />
          <select
            className="rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-800"
            value={salesChannel}
            onChange={setField("salesChannel")}
            aria-label="Canal de venta"
          >
            <option value="local">Local (compite por cercanía)</option>
            <option value="online">Online (compite en web)</option>
            <option value="mixto">Mixto (ambos)</option>
          </select>
          <button
            type="submit"
            disabled={status === "loading"}
            className="rounded-lg bg-black px-5 py-2 font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
          >
            {status === "loading" ? "Analizando…" : "Analizar"}
          </button>
        </div>
      </form>

      {status === "error" && (
        <p className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {status === "done" && result && (
        <div className="flex flex-col gap-6">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Competidores</h2>
            <CompetitorsTable competitors={result.competitors} />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Oportunidades</h2>
            <ul className="flex flex-col gap-2">
              {result.opportunities.map((o) => (
                <li key={o.title} className="rounded-xl border border-zinc-200 p-3 text-sm dark:border-zinc-800">
                  <p className="font-medium">{o.title}</p>
                  <p className="text-zinc-500">{o.evidence} · {o.confidence}</p>
                </li>
              ))}
            </ul>
          </section>
          {result.draft_post && (
            <DraftPreview
              initial={result.draft_post}
              opportunityTitle={result.opportunities[0]?.title}
            />
          )}
        </div>
      )}
    </div>
  );
}
