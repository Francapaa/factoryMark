import { redirect } from "next/navigation";
import OnboardingScreen from "./components/OnboardingScreen";
import { getAuth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  let user: { name?: string | null; email?: string | null; image?: string | null } | null =
    null;
  try {
    const { data: session } = await getAuth().getSession();
    user = session?.user ?? null;
  } catch {
    user = null;
  }
  if (!user) redirect("/login");

  return <OnboardingScreen user={user} />;
}
