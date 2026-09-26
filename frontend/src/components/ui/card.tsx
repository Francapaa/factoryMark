import * as React from "react";
import { cn } from "@/lib/utils";

function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-white/10 bg-[#121214]/80 backdrop-blur-xl",
        className
      )}
      {...props}
    />
  );
}

function CardAmber({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-[#6B3A0A]/15 bg-[#FFF7ED]/90 backdrop-blur-xl shadow-[0_24px_80px_rgba(107,58,10,0.18)]",
        className
      )}
      {...props}
    />
  );
}

export { Card, CardAmber };
