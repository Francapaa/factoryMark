"use client";

import { apiErrorCode, apiErrorMessage, type MyBusiness } from "@/lib/businesses";
import { apiFetch } from "@/lib/api";
import type { AnalyzeResult } from "@/types/analysis";

export class AnalysisError extends Error {
  status: number;
  code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = "AnalysisError";
    this.status = status;
    this.code = code;
  }
}

async function responseError(res: Response): Promise<AnalysisError> {
  const body = await res.json().catch(() => null);
  return new AnalysisError(
    res.status,
    apiErrorMessage(body, `Error ${res.status}`),
    apiErrorCode(body)
  );
}

/** Último análisis guardado. 404/409 significan que todavía no hay nada que mostrar. */
export async function getLatestAnalysis(): Promise<AnalyzeResult | null> {
  const res = await apiFetch("/api/analysis/latest");
  if (res.status === 404 || res.status === 409) return null;
  if (!res.ok) throw await responseError(res);
  return (await res.json()) as AnalyzeResult;
}

/** Corre el pipeline sobre el negocio guardado y persiste la corrida. */
export async function runAnalysis(
  business: MyBusiness,
  { refreshPlaces }: { refreshPlaces: boolean }
): Promise<AnalyzeResult> {
  const res = await apiFetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      business_name: business.name,
      business_type: business.business_type,
      zone: business.zone,
      sales_channel: business.sales_channel,
      refresh_places: refreshPlaces,
    }),
  });
  if (!res.ok) throw await responseError(res);
  return (await res.json()) as AnalyzeResult;
}
