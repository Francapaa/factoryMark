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
        <img src={user.image} alt="" className="h-8 w-8 rounded-full ring-1 ring-white/15" />
      ) : (
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#FF5C00]/15 text-sm font-semibold text-[#FFB25C] ring-1 ring-[#FF5C00]/30">
          {initial}
        </span>
      )}
      <div className="hidden min-w-0 leading-tight sm:block">
        <p className="truncate text-sm font-medium text-white">{user.name ?? "Mi cuenta"}</p>
        {user.email && <p className="truncate text-xs text-zinc-500">{user.email}</p>}
      </div>
      <button
        type="button"
        onClick={logout}
        disabled={loading}
        className="rounded-full border border-white/10 px-3 py-1.5 text-sm text-zinc-300 transition-colors hover:border-[#FF5C00]/50 hover:text-white disabled:opacity-50"
      >
        {loading ? "Saliendo…" : "Salir"}
      </button>
    </div>
  );
}
