import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatValue, inr, num, percent } from "@/lib/format";
import type { Chart } from "@/lib/types";
import { Card } from "./PageHeader";
import { EmptyState, ErrorState, SkeletonBlock } from "./States";

// Forest, sage, sand, clay. Never more than four colours in one chart.
export const CHART_COLOURS = ["#2F4A3A", "#8FA88F", "#C9B38C", "#B5643C"];

function axisText(value: number, kind: string): string {
  if (kind === "money") return inr(value);
  if (kind === "percent") return percent(value);
  return num(value);
}

function ExactTooltip({ active, payload, label, kind }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string; kind: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-line bg-surface px-3 py-2 text-xs shadow-float">
      <p className="mb-1 font-semibold text-ink">{label}</p>
      {payload.map((item) => (
        <p key={item.name} className="flex items-center justify-between gap-4 text-muted">
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm" style={{ background: item.color }} />{item.name}</span>
          <span className="font-medium text-ink">{formatValue(item.value, kind)}</span>
        </p>
      ))}
    </div>
  );
}

/** Horizontal bars, each a share of the first step. Quieter than a funnel shape and easier to read. */
function Funnel({ chart, onSelect }: { chart: Chart; onSelect?: (label: string) => void }) {
  const values = chart.series[0]?.data ?? [];
  const top = values[0] || 1;
  return (
    <ol className="space-y-3">
      {chart.x.map((label, i) => (
        <li key={label}>
          <button type="button" onClick={() => onSelect?.(label)} className="block w-full text-left" disabled={!onSelect}>
            <div className="mb-1 flex justify-between text-xs">
              <span className="font-medium text-ink">{label}</span>
              <span className="text-muted">{num(values[i])} <span className="text-neutral">({percent(((values[i] ?? 0) / top) * 100)})</span></span>
            </div>
            <div className="h-2.5 rounded-sm bg-subtle">
              <div className="h-full rounded-sm bg-primary transition-[width] duration-200" style={{ width: `${Math.max(((values[i] ?? 0) / top) * 100, 1)}%` }} />
            </div>
          </button>
        </li>
      ))}
    </ol>
  );
}

/**
 * A chart in a card with a title that says what it shows. Tooltips give exact values.
 * Pass onSelect to let a click on a bar or point filter the table below.
 */
export function ChartCard({ chart, isLoading, error, onSelect, height = 260, hint }: {
  chart?: Chart; isLoading?: boolean; error?: Error | null; onSelect?: (label: string) => void; height?: number; hint?: string;
}) {
  if (error) return <Card title={chart?.title}><ErrorState message={error.message} /></Card>;
  if (isLoading || !chart) return <Card><SkeletonBlock rows={7} /></Card>;
  const empty = chart.series.every((s) => s.data.every((v) => !v));
  const rows = chart.x.map((x, i) => ({ x, ...Object.fromEntries(chart.series.map((s) => [s.name, s.data[i]])) }));
  const click = onSelect ? (entry: unknown) => {
    const picked = entry as { payload?: { x?: string }; activeLabel?: string };
    const label = picked?.payload?.x ?? picked?.activeLabel;
    if (label) onSelect(label);
  } : undefined;
  const axes = (
    <>
      <CartesianGrid vertical={false} stroke="#E3DFD6" />
      <XAxis dataKey="x" tickLine={false} axisLine={false} fontSize={11} tick={{ fill: "#5E635F" }} interval="preserveStartEnd" />
      <YAxis tickLine={false} axisLine={false} fontSize={11} width={62} tick={{ fill: "#5E635F" }} tickFormatter={(v: number) => axisText(v, chart.kind)} />
      <Tooltip content={<ExactTooltip kind={chart.kind} />} cursor={{ fill: "#EFECE5", stroke: "#E3DFD6" }} />
    </>
  );
  return (
    <Card title={chart.title} hint={hint}>
      {empty ? <EmptyState text="No data for these filters." /> : chart.type === "funnel" ? <Funnel chart={chart} onSelect={onSelect} /> : (
        <>
          <ResponsiveContainer width="100%" height={height}>
            {chart.type === "line" ? (
              <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} onClick={click}>
                {axes}
                {chart.series.map((s, i) => <Line key={s.name} dataKey={s.name} stroke={CHART_COLOURS[i % 4]} strokeWidth={2} dot={{ r: 2.5 }} isAnimationActive={false} connectNulls />)}
              </LineChart>
            ) : (
              <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap="28%">
                {axes}
                {chart.series.map((s, i) => (
                  <Bar key={s.name} dataKey={s.name} fill={CHART_COLOURS[i % 4]} stackId={chart.type === "stacked" ? "stack" : undefined}
                    radius={chart.type === "stacked" ? 0 : [3, 3, 0, 0]} isAnimationActive={false} onClick={click}
                    className={onSelect ? "cursor-pointer" : undefined} />
                ))}
              </BarChart>
            )}
          </ResponsiveContainer>
          {chart.series.length > 1 && (
            <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
              {chart.series.map((s, i) => (
                <li key={s.name} className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm" style={{ background: CHART_COLOURS[i % 4] }} />{s.name}</li>
              ))}
            </ul>
          )}
        </>
      )}
    </Card>
  );
}
