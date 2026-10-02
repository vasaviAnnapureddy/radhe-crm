import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { dateText, formatValue, num } from "@/lib/format";
import type { Metric } from "@/lib/types";
import { useExplain, useFilters } from "@/lib/urlState";
import { DataTable } from "../data/DataTable";
import { ErrorState, SkeletonBlock } from "../data/States";
import { Sheet } from "../ui/sheet";

/** "Explain this number": the formula, the filters in use, and the exact rows behind a KPI. */
export function ExplainDrawer() {
  const explain = useExplain();
  const { params } = useFilters();
  const key = explain.key;
  const { data, isError, error } = useQuery({
    queryKey: ["metric", key, params],
    queryFn: () => api<Metric>(`/metrics/${key}`, { params }),
    enabled: Boolean(key),
  });
  if (!key) return null;
  const period = data?.filters.date_from ? `${dateText(data.filters.date_from)} to ${dateText(data.filters.date_to)}` : "As of today";
  return (
    <Sheet open onClose={explain.close} title={data?.label ?? "Explain"} description="How this number is calculated" wide>
      {isError && <ErrorState message={(error as Error).message} />}
      {!data && !isError && <SkeletonBlock rows={6} />}
      {data && (
        <div className="space-y-6">
          <div className="rounded-card border border-line bg-surface p-5">
            <p className="text-3xl font-semibold text-ink">{formatValue(data.value, data.kind)}</p>
            {data.previous_value !== null && <p className="mt-1 text-xs text-muted">Previous period: {formatValue(data.previous_value, data.kind)}</p>}
            <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-muted">Formula</h3>
            <p className="mt-1 text-sm text-ink">{data.formula_text}</p>
            <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-muted">Filters</h3>
            <p className="mt-1 text-sm text-ink">{period} · {data.filters.project}</p>
          </div>
          <div>
            <h3 className="mb-3 text-sm font-semibold text-ink">The {num(data.row_count)} rows behind this number</h3>
            <DataTable endpoint={`/metrics/${key}/rows`} params={params} exportName={key} />
          </div>
        </div>
      )}
    </Sheet>
  );
}
