import { redirect } from "next/navigation";
import { DashboardClient } from "@/components/dashboard/DashboardClient";
import { getAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let user: { name?: string | null; email?: string | null } | null = null;
  try {
    const { data: session } = await getAuth().getSession();
    user = session?.user ?? null;
  } catch {
    user = null;
  }
  if (!user) redirect("/login");

  return <DashboardClient />;
}
