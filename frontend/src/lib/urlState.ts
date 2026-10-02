// State that lives in the URL, so it survives a refresh and the browser Back button works:
//   ?range=90d&project=<id>      the global filters
//   ?view=customer:<id>,unit:<id> the stack of pinned drawers
//   ?explain=<metric key>         the "Explain this number" drawer
import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";
import type { Params } from "./api";
import type { EntityType } from "./types";

export const RANGES: { key: string; label: string; days: number }[] = [
  { key: "30d", label: "Last 30 days", days: 30 },
  { key: "90d", label: "Last 90 days", days: 90 },
  { key: "12m", label: "Last 12 months", days: 365 },
  { key: "all", label: "All time", days: 730 }, // the demo data goes back about 18 months
];
// Start on "All time", so every page first shows the full totals; a shorter range narrows them.
const DEFAULT_RANGE = "all";

function isoDaysAgo(daysAgo: number): string {
  const day = new Date();
  day.setDate(day.getDate() - daysAgo);
  return `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`;
}

/** Keep only the global filters when moving to another page. */
export function keepFilters(search: string): string {
  const from = new URLSearchParams(search);
  const to = new URLSearchParams();
  for (const key of ["range", "project"]) if (from.get(key)) to.set(key, from.get(key)!);
  const text = to.toString();
  return text ? `?${text}` : "";
}

export function useFilters() {
  const [search, setSearch] = useSearchParams();
  const range = RANGES.find((r) => r.key === search.get("range")) ?? RANGES.find((r) => r.key === DEFAULT_RANGE)!;
  const projectId = search.get("project");

  const set = useCallback((key: string, value: string | null) => {
    setSearch((old) => {
      const next = new URLSearchParams(old);
      if (value) next.set(key, value); else next.delete(key);
      return next;
    }, { replace: true });
  }, [setSearch]);

  /** The query parameters every console request carries. */
  const params: Params = useMemo(() => ({
    date_from: isoDaysAgo(range.days - 1),
    project_id: projectId,
  }), [range, projectId]);

  return { range, projectId, params, setRange: (key: string) => set("range", key === DEFAULT_RANGE ? null : key),
           setProject: (id: string | null) => set("project", id) };
}

export interface Pinned { type: EntityType; id: string }

export function useDrawer() {
  const [search, setSearch] = useSearchParams();
  const stack: Pinned[] = useMemo(() => (search.get("view") ?? "").split(",").filter(Boolean).map((item) => {
    const [type, id] = item.split(":");
    return { type: type as EntityType, id };
  }), [search]);

  const write = useCallback((next: Pinned[]) => {
    setSearch((old) => {
      const params = new URLSearchParams(old);
      if (next.length) params.set("view", next.map((p) => `${p.type}:${p.id}`).join(",")); else params.delete("view");
      return params;
    }); // a new history entry each time, so Back closes one drawer
  }, [setSearch]);

  return {
    stack,
    /** Pin an entity. If a drawer is already open, the new one stacks on top of it. */
    open: (type: EntityType, id: string) => {
      const last = stack[stack.length - 1];
      if (!last || last.type !== type || last.id !== id) write([...stack, { type, id }]);
    },
    popTo: (index: number) => write(stack.slice(0, index + 1)),
    close: () => write([]),
  };
}

export function useExplain() {
  const [search, setSearch] = useSearchParams();
  const set = (key: string | null) => setSearch((old) => {
    const params = new URLSearchParams(old);
    if (key) params.set("explain", key); else params.delete("explain");
    return params;
  });
  return { key: search.get("explain"), open: (key: string) => set(key), close: () => set(null) };
}
