import { getAuth } from "@/lib/auth/server";

type Ctx = { params: Promise<{ path: string[] }> };

type AuthHandlers = ReturnType<ReturnType<typeof getAuth>["handler"]>;

async function dispatch(req: Request, ctx: Ctx): Promise<Response> {
  const handlers = getAuth().handler() as AuthHandlers;
  const fn = handlers[req.method as keyof AuthHandlers] as
    | ((req: Request, ctx: Ctx) => Promise<Response>)
    | undefined;
  if (!fn) return Response.json({ error: "Método no soportado" }, { status: 405 });
  return fn(req, ctx);
}

export const GET = dispatch;
export const POST = dispatch;
export const PUT = dispatch;
export const DELETE = dispatch;
export const PATCH = dispatch;
