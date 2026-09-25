"use client";

import { useState } from "react";

type Draft = {
  copy_text: string;
  hashtags: string[];
  status: string;
};

export default function DraftPreview({ initial }: { initial: Draft }) {
  const [status, setStatus] = useState(initial.status);

  return (
    <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <p className="text-sm uppercase tracking-widest text-zinc-500">Borrador · {status}</p>
      <p className="mt-2">{initial.copy_text}</p>
      <p className="mt-1 text-sm text-zinc-500">{initial.hashtags.join(" ")}</p>
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => setStatus("approved")}
          className="rounded-lg bg-green-600 px-4 py-1.5 text-sm font-medium text-white"
        >
          Aprobar
        </button>
        <button
          onClick={() => setStatus("rejected")}
          className="rounded-lg border border-zinc-300 px-4 py-1.5 text-sm dark:border-zinc-700"
        >
          Rechazar
        </button>
      </div>
    </div>
  );
}
