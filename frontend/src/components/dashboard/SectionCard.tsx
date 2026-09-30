import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function SectionCard({
  badge,
  title,
  hint,
  action,
  children,
  className,
}: {
  badge: string;
  title: string;
  hint?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("noise relative overflow-hidden p-6 sm:p-7", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Badge variant="ember">{badge}</Badge>
          <h2 className="font-display mt-3 text-2xl font-bold tracking-tight text-white">
            {title}
          </h2>
          {hint && <p className="mt-1 max-w-xl text-sm text-zinc-400">{hint}</p>}
        </div>
        {action}
      </div>
      <div className="mt-5">{children}</div>
    </Card>
  );
}

export function EmptyState({
  text,
  action,
}: {
  text: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/50 p-5 text-center">
      <p className="text-sm text-zinc-400">{text}</p>
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorState({ text, onRetry }: { text: string; onRetry: () => void }) {
  return (
    <div className="rounded-2xl border border-red-500/30 bg-red-500/[0.06] p-5 text-center">
      <p className="text-sm text-red-300">{text}</p>
      <button
        type="button"
        onClick={onRetry}
        className="font-display mt-3 inline-flex h-9 items-center rounded-full border border-red-400/40 px-4 text-sm font-semibold text-red-200 transition-colors hover:border-red-300"
      >
        Reintentar
      </button>
    </div>
  );
}
