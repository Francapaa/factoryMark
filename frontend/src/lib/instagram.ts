"use client";

import { apiFetch } from "./api";
import type { ScheduledPost } from "@/types/dashboard";

export type PublishResult = {
  estado: string;
  media_id: string;
  container_id: string;
};

export type RunDueResult = {
  revisados: number;
  publicados: number;
  errores: { id: string; error: string }[];
};

async function readError(res: Response, fallback: string): Promise<Error> {
  const body = await res.json().catch(() => null);
  const detail = (body as { detail?: unknown } | null)?.detail;
  return new Error(typeof detail === "string" ? detail : `${fallback} (${res.status})`);
}

export async function completeInstagramCallback(code: string, state: string) {
  const res = await apiFetch(
    `/api/instagram/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
  );
  if (!res.ok) throw await readError(res, "No pudimos completar la conexión");
  return (await res.json()) as {
    estado: string;
    username?: string;
    followers_count?: number;
    media_count?: number;
    can_publish?: boolean;
  };
}

export async function publishNow(imageUrl: string, caption: string): Promise<PublishResult> {
  const res = await apiFetch("/api/instagram/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: imageUrl, caption }),
  });
  if (!res.ok) throw await readError(res, "No pudimos publicar");
  return (await res.json()) as PublishResult;
}

export async function getPublishingLimit(): Promise<Record<string, unknown>> {
  const res = await apiFetch("/api/instagram/limit");
  if (!res.ok) throw await readError(res, "No pudimos leer la cuota");
  return (await res.json()) as Record<string, unknown>;
}

export async function getScheduledPosts(): Promise<ScheduledPost[]> {
  const res = await apiFetch("/api/instagram/scheduled");
  if (!res.ok) throw await readError(res, "No pudimos listar programadas");
  return (await res.json()) as ScheduledPost[];
}

export async function createScheduledPost(input: {
  image_url: string;
  caption: string;
  copy_text?: string;
  hashtags?: string[];
  programada_para: string;
}): Promise<ScheduledPost> {
  const res = await apiFetch("/api/instagram/scheduled", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw await readError(res, "No pudimos programar");
  return (await res.json()) as ScheduledPost;
}

export async function cancelScheduledPost(id: string): Promise<ScheduledPost> {
  const res = await apiFetch(`/api/instagram/scheduled/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw await readError(res, "No pudimos cancelar");
  return (await res.json()) as ScheduledPost;
}

export async function publishScheduledNow(id: string): Promise<PublishResult> {
  const res = await apiFetch(`/api/instagram/scheduled/${encodeURIComponent(id)}/publish-now`, {
    method: "POST",
  });
  if (!res.ok) throw await readError(res, "No pudimos publicar");
  return (await res.json()) as PublishResult;
}

export async function runDueScheduled(): Promise<RunDueResult> {
  const res = await apiFetch("/api/instagram/scheduled/run-due", { method: "POST" });
  if (!res.ok) throw await readError(res, "No pudimos publicar vencidas");
  return (await res.json()) as RunDueResult;
}
