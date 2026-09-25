"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthRequiredError, apiFetch } from "@/lib/api";

type Draft = {
  copy_text: string;
  hashtags: string[];
  status: string;
};

export default function DraftPreview({
  initial,
  opportunityTitle,
}: {
  initial: Draft;
  opportunityTitle?: string;
}) {
  const router = useRouter();
  const [status, setStatus] = useState(initial.status);
  const [saving, setSaving] = useState(false);

  async function vote(approved: boolean) {
    setSaving(true);
    try {
      // Human-in-the-loop real: registra la decisión en el backend (exige sesión).
      const res = await apiFetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          approved,
          opportunity_title: opportunityTitle ?? "oportunidad detectada",
        }),
      });
      if (res.ok) {
        const body = (await res.json()) as { status: string };
        setStatus(body.status);
      } else {
        setStatus(approved ? "approved" : "rejected");
      }
    } catch (e) {
      if (e instanceof AuthRequiredError) {
        router.push("/login");
        return;
      }
      // Backend caído (modo mock): refleja la decisión solo en pantalla.
      setStatus(approved ? "approved" : "rejected");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <p className="text-sm uppercase tracking-widest text-zinc-500">Borrador · {status}</p>
      <p className="mt-2">{initial.copy_text}</p>
      <p className="mt-1 text-sm text-zinc-500">{initial.hashtags.join(" ")}</p>
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => vote(true)}
          disabled={saving}
          className="rounded-lg bg-green-600 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Aprobar
        </button>
        <button
          onClick={() => vote(false)}
          disabled={saving}
          className="rounded-lg border border-zinc-300 px-4 py-1.5 text-sm disabled:opacity-50 dark:border-zinc-700"
        >
          Rechazar
        </button>
      </div>
    </div>
  );
}
