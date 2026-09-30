import { redirect } from "next/navigation";
import { OnboardingFlow } from "./components";
import UserMenu from "@/components/UserMenu";
import { getAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  let user: { name?: string | null; email?: string | null; image?: string | null } | null = null;
  try {
    const { data: session } = await getAuth().getSession();
    user = session?.user ?? null;
  } catch {
    user = null;
  }
  if (!user) redirect("/login");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-2xl flex-col gap-6 rounded-2xl bg-white p-10 shadow-sm dark:bg-zinc-900">
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm font-medium uppercase tracking-widest text-zinc-500">
            FactoryMark · Onboarding
          </p>
          <UserMenu user={user} />
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
          Registrá tu negocio
        </h1>
        <OnboardingFlow />
      </main>
    </div>
  );
}
