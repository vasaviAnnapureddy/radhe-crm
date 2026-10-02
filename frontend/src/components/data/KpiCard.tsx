import { useQuery } from "@tanstack/react-query";
import { ArrowDownRight, ArrowUpRight, Info } from "lucide-react";
import { api } from "@/lib/api";
import { changePct, formatValue, percent } from "@/lib/format";
import type { Metric } from "@/lib/types";
import { useExplain, useFilters } from "@/lib/urlState";
import { ErrorState, Skeleton } from "./States";

/** A tiny trend line. No axes: it only shows the direction. */
function Sparkline({ points }: { points: number[] }) {
  const max = Math.max(...points), min = Math.min(...points);
  const span = max - min || 1;
  const path = points.map((p, i) => `${(i / (points.length - 1)) * 96},${26 - ((p - min) / span) * 22}`).join(" ");
  return (
    <svg width="96" height="28" viewBox="0 0 96 28" aria-hidden="true" className="text-sage">
      <polyline points={path} fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** One KPI: value, change against the previous period, a tiny trend, and the Explain icon. */
export function KpiCard({ metric }: { metric: Metric }) {
  const explain = useExplain();
  const change = changePct(metric.value, metric.previous_value);
  const Arrow = change !== null && change < 0 ? ArrowDownRight : ArrowUpRight;
  return (
    <article className="flex min-h-[132px] flex-col justify-between rounded-card border border-line bg-surface p-5">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-[13px] font-medium text-muted">{metric.label}</h3>
        <button type="button" onClick={() => explain.open(metric.key)} aria-label={`Explain ${metric.label}`} title="Explain this number"
          className="-mr-1 -mt-1 rounded-md p-1 text-neutral transition-colors duration-150 hover:bg-subtle hover:text-primary">
          <Info size={15} strokeWidth={1.75} />
        </button>
      </div>
      <div className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="whitespace-nowrap text-2xl font-semibold leading-none tracking-tight text-ink">{formatValue(metric.value, metric.kind)}</p>
          {/* The second line says plainly whether the number follows the date filter. */}
          <p className="mt-2 text-xs leading-snug text-muted">
            {!metric.is_flow ? (metric.period_note ?? "As of today")
              : change === null ? "In this period"
              : (<span className="inline-flex items-center gap-1"><Arrow size={13} strokeWidth={2} />{percent(Math.abs(change))} vs previous period</span>)}
          </p>
        </div>
        {/* The trend line is shown only when the card is wide enough for it. */}
        {metric.sparkline && metric.sparkline.length > 1 && <span className="hidden shrink-0 2xl:block"><Sparkline points={metric.sparkline} /></span>}
      </div>
    </article>
  );
}

/** A row of KPI cards. At most five per page, at most four across. */
export function KpiRow({ keys }: { keys: string[] }) {
  const { params } = useFilters();
  const { data, isError, error, refetch } = useQuery({
    queryKey: ["metrics", keys, params],
    queryFn: () => api<Metric[]>("/metrics", { params: { ...params, keys: keys.join(",") } }),
  });
  if (isError) return <div className="rounded-card border border-line bg-surface"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>;
  const columns = keys.length >= 5 ? "xl:grid-cols-5" : "xl:grid-cols-4";
  return (
    <div className={`grid grid-cols-2 gap-4 lg:grid-cols-3 ${columns}`}>
      {data ? data.map((metric) => <KpiCard key={metric.key} metric={metric} />)
        : keys.map((key) => <Skeleton key={key} className="h-[132px] rounded-card" />)}
    </div>
  );
}
