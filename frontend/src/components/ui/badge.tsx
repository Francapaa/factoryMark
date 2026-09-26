import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-display text-[11px] font-semibold uppercase tracking-[0.18em]",
  {
    variants: {
      variant: {
        ember: "border-[#FF5C00]/40 bg-[#FF5C00]/10 text-[#FFB25C]",
        solid: "border-transparent bg-[#FF5C00] text-[#0A0A0B]",
        ghost: "border-white/15 bg-white/5 text-zinc-300",
        amber: "border-[#6B3A0A]/25 bg-[#6B3A0A]/10 text-[#92400E]",
        cream: "border-[#0A0A0B]/15 bg-[#0A0A0B]/5 text-[#44403C]",
      },
    },
    defaultVariants: { variant: "ember" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
