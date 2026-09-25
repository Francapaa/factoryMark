"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { authClient } from "@/lib/auth/client";

export type MenuUser = {
  name?: string | null;
  email?: string | null;
  image?: string | null;
};

export default function UserMenu({ user }: { user: MenuUser }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function logout() {
    setLoading(true);
    await authClient.signOut();
    router.push("/login");
    router.refresh();
  }

  const initial = (user.name ?? user.email ?? "?").trim().charAt(0).toUpperCase();

  return (
    <div className="flex items-center gap-3">
      {user.image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.image} alt="" className="h-8 w-8 rounded-full" />
      ) : (
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-200 text-sm font-semibold text-zinc-700 dark:bg-zinc-700 dark:text-zinc-200">
          {initial}
        </span>
      )}
      <div className="min-w-0 leading-tight">
        <p className="truncate text-sm font-medium">{user.name ?? "Mi cuenta"}</p>
        {user.email && <p className="truncate text-xs text-zinc-500">{user.email}</p>}
      </div>
      <button
        type="button"
        onClick={logout}
        disabled={loading}
        className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-zinc-700"
      >
        {loading ? "Saliendo…" : "Salir"}
      </button>
    </div>
  );
}
