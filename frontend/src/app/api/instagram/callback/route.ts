import { redirect } from "next/navigation";

/** Puente OAuth: Instagram redirige acá (INSTAGRAM_REDIRECT_URI) y pasamos
 * el code al dashboard, que completa el intercambio con el backend usando
 * el JWT del dueño. Los secretos quedan siempre del lado del backend. */
export async function GET(req: Request): Promise<never> {
  const url = new URL(req.url);
  const dash = new URL("/dashboard", url.origin);
  const error =
    url.searchParams.get("error") ?? url.searchParams.get("error_reason");
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  if (error) {
    dash.searchParams.set("ig_error", error);
  } else if (code && state) {
    dash.searchParams.set("ig_code", code);
    dash.searchParams.set("ig_state", state);
  } else {
    dash.searchParams.set("ig_error", "sin_codigo");
  }
  redirect(dash.toString());
}
