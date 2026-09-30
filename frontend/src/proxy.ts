import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getAuth } from "@/lib/auth/server";

let cached: ((request: NextRequest) => Promise<NextResponse>) | null = null;

export default async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // Públicas: landing y login (+ callback de OAuth). Todo lo demás exige sesión.
  if (pathname === "/" || pathname === "/login") return NextResponse.next();
  try {
    cached ??= getAuth().middleware({ loginUrl: "/login" });
  } catch {
    // Sin .env configurado: mandar área privada a /login sin romper nada público.
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return cached(request);
}

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)"],
};
