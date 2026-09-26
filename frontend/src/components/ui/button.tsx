import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-display font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FF5C00] disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        primary:
          "bg-[#FF5C00] text-[#0A0A0B] shadow-[0_0_32px_rgba(255,92,0,0.45)] hover:bg-[#FF8A3D] hover:shadow-[0_0_48px_rgba(255,92,0,0.65)] hover:-translate-y-0.5",
        dark: "bg-[#0A0A0B] text-[#FFF7ED] border border-[#FF5C00]/40 hover:border-[#FF5C00] hover:shadow-[0_0_24px_rgba(255,92,0,0.35)]",
        ghost: "text-zinc-300 hover:text-white hover:bg-white/5 border border-transparent hover:border-white/10",
        amber:
          "bg-[#0A0A0B] text-[#FFD9A3] shadow-[0_8px_32px_rgba(10,10,11,0.4)] hover:-translate-y-0.5 hover:shadow-[0_12px_40px_rgba(10,10,11,0.5)]",
        light:
          "bg-[#FFF7ED] text-[#0A0A0B] hover:bg-white hover:-translate-y-0.5 shadow-lg",
      },
      size: {
        sm: "h-9 px-4 text-sm",
        md: "h-11 px-6 text-[15px]",
        lg: "h-12 px-8 py-3.5 text-base",
        xl: "h-14 px-10 py-4 text-lg",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
);
Button.displayName = "Button";

export { Button, buttonVariants };
