import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

/** A slow, gentle rise as a block scrolls into view. Plays once. Skipped for people who ask for less motion. */
export function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  const still = useReducedMotion();
  if (still) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, delay, ease: [0.2, 0.7, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
}

/** The small label above each section title. */
export function Eyebrow({ children, light }: { children: ReactNode; light?: boolean }) {
  return <p className={`text-xs font-semibold uppercase tracking-[0.18em] ${light ? "text-bg/70" : "text-accent"}`}>{children}</p>;
}
