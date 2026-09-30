import { redirect } from "next/navigation";
import AnalyzeForm from "@/components/AnalyzeForm";
import { BusinessGate } from "./components";
import UserMenu from "@/components/UserMenu";
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
