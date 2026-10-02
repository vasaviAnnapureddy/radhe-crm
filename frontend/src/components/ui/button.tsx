import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

const VARIANTS = {
  primary: "bg-primary text-white hover:bg-primary/90",
  accent: "bg-accent text-white hover:bg-accent/90", // clay: at most one per screen
  outline: "border border-line bg-surface text-ink hover:bg-subtle",
  ghost: "text-muted hover:bg-subtle hover:text-ink",
};
const SIZES = { sm: "h-8 px-3 text-[13px]", md: "h-10 px-4 text-sm", icon: "h-8 w-8 justify-center" };

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANTS;
  size?: keyof typeof SIZES;
}

export function Button({ variant = "outline", size = "md", className, type = "button", ...rest }: Props) {
  return (
    <button
      type={type}
      className={cn("inline-flex items-center gap-2 rounded-md font-medium transition-colors duration-150",
        "disabled:cursor-not-allowed disabled:opacity-50", VARIANTS[variant], SIZES[size], className)}
      {...rest}
    />
  );
}
