import { cn, TONE_DOT, TONE_PILL } from "@/lib/cn";
import { area, dateText, dateTimeText, formatValue, inr } from "@/lib/format";
import type { ScoreCell, StatusCell, Tone } from "@/lib/types";

/** Money in ₹ lakh and crore. The full rupee amount shows on hover. */
export function Money({ value, className }: { value: number | null | undefined; className?: string }) {
  const full = value === null || value === undefined ? undefined : `₹${Math.round(value).toLocaleString("en-IN")}`;
  return <span title={full} className={className}>{inr(value)}</span>;
}

export function Area({ value, unit = "sqft" }: { value: number | null | undefined; unit?: "sqft" | "sqyd" }) {
  return <span>{area(value, unit)}</span>;
}

export function DateText({ value, withTime }: { value: string | null | undefined; withTime?: boolean }) {
  return <time dateTime={value ?? undefined}>{withTime ? dateTimeText(value) : dateText(value)}</time>;
}

/** Any value, formatted by the kind the backend sent. */
export function Value({ value, kind }: { value: unknown; kind: string }) {
  if (kind === "money") return <Money value={value as number | null} />;
  return <span>{formatValue(value, kind)}</span>;
}

export function StatusPill({ label, tone }: StatusCell) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium", TONE_PILL[tone])}>
      <span className={cn("h-1.5 w-1.5 rounded-full", TONE_DOT[tone])} />
      {label}
    </span>
  );
}

export function ScorePill({ value, tone }: ScoreCell) {
  return (
    <span className={cn("inline-flex min-w-9 justify-center rounded-md px-1.5 py-0.5 text-xs font-semibold", TONE_PILL[tone])}>
      {value}
    </span>
  );
}

const SEVERITY: Record<string, { label: string; tone: Tone }> = {
  high: { label: "High", tone: "risk" }, medium: { label: "Medium", tone: "watch" }, low: { label: "Low", tone: "neutral" },
};

export function RiskBadge({ severity }: { severity: string }) {
  const { label, tone } = SEVERITY[severity] ?? SEVERITY.low;
  return <StatusPill label={label} tone={tone} />;
}
