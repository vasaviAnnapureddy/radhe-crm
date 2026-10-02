import type { Ref, ScoreCell, StatusCell } from "@/lib/types";
import { EntityLink } from "../views/EntityLink";
import { ScorePill, StatusPill, Value } from "./Value";

export const RIGHT_ALIGNED = new Set(["money", "number", "percent", "days"]);

/** One table cell, drawn by the kind the backend sent: link, pill, money, date and so on. */
export function Cell({ value, kind }: { value: unknown; kind: string }) {
  if (value === null || value === undefined || value === "") return <span className="text-neutral">–</span>;
  if (kind === "ref") return <EntityLink entity={value as Ref} />;
  if (kind === "status") return <StatusPill {...(value as StatusCell)} />;
  if (kind === "score") return <ScorePill {...(value as ScoreCell)} />;
  return <Value value={value} kind={kind} />;
}

/** Plain text of a cell, for CSV export. */
export function cellText(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") {
    const cell = value as { label?: string; value?: unknown };
    return String(cell.label ?? cell.value ?? "");
  }
  return String(value);
}
