import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Tone } from "./types";

/** Join class names; later Tailwind classes win over earlier ones. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Colour carries meaning only: these four tones are the only coloured pills in the console. */
export const TONE_PILL: Record<Tone, string> = {
  good: "bg-good/10 text-good",
  watch: "bg-watch/15 text-[#8a6212]",
  risk: "bg-risk/10 text-risk",
  neutral: "bg-subtle text-muted",
};
export const TONE_DOT: Record<Tone, string> = { good: "bg-good", watch: "bg-watch", risk: "bg-risk", neutral: "bg-neutral" };
