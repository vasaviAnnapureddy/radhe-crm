import { useQuery } from "@tanstack/react-query";
import { useMe } from "@/app/auth";
import { ChartCard } from "@/components/data/ChartCard";
import { KpiRow } from "@/components/data/KpiCard";
import { Card, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { RiskCard } from "@/components/data/RiskCard";
import { EmptyState, ErrorState, Skeleton, SkeletonBlock } from "@/components/data/States";
import { ScorePill } from "@/components/data/Value";
import { BlockView } from "@/components/views/Blocks";
import { EntityLink } from "@/components/views/EntityLink";
import { api } from "@/lib/api";
import { dateText, percent } from "@/lib/format";
import type { Block, Chart, Ref, RiskCard as Risk, ScoreCell } from "@/lib/types";
import { useFilters } from "@/lib/urlState";

interface ProjectHealth {
  project: Ref; type: string; sold_pct: number; construction_pct: number | null; collection_efficiency: number | null; health: ScoreCell;
}
interface OverviewReply {
  monthly: Chart; attention: Risk[]; project_health: ProjectHealth[]; funnel: Chart;
  site_visits_today: Block; handovers: Block; top_rms: Block; top_partners: Block;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <dt className="text-muted">{label}</dt>
      <dd className="font-medium text-ink">{value}</dd>
    </div>
  );
}

/** Overview: "How is Radhe doing, and what needs my attention?" */
export default function Overview() {
  const { params } = useFilters();
  const { data: me } = useMe();
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ["overview", params],
    queryFn: () => api<OverviewReply>("/overview", { params }),
  });
  const today = new Date().toISOString();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <>
      <PageHeader title={`${greeting}, ${me?.name.split(" ")[0] ?? ""}`}
        question={`${dateText(today)}. How is Radhe doing, and what needs your attention?`} />

      <KpiRow keys={["bookings_value", "collections_received", "collections_overdue", "unsold_inventory_value", "open_high_risks"]} />

      {error && <div className="mt-6 rounded-card border border-line bg-surface"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>}

      {/* Above the fold: the KPI row and two main visuals only. */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <ChartCard chart={data?.monthly} isLoading={isPending} height={300} />
        <Card title="What needs attention" hint="The five most important open risks. Click a title to see the full picture.">
          {isPending && <SkeletonBlock rows={8} />}
          {data && !data.attention.length && <EmptyState title="All clear" text="There are no open risks." />}
          <div className="divide-y divide-line">
            {data?.attention.map((risk) => <RiskCard key={risk.id} risk={risk} compact />)}
          </div>
        </Card>
      </div>

      <h2 className="mb-4 mt-12 text-sm font-semibold text-ink">Project health</h2>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-5">
        {isPending && Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-[150px] rounded-card" />)}
        {data?.project_health.map((item) => (
          <article key={item.project.id} className="rounded-card border border-line bg-surface p-4">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <EntityLink entity={item.project} className="text-sm" />
                <p className="mt-0.5 text-xs text-muted">{item.type}</p>
              </div>
              <ScorePill {...item.health} />
            </div>
            <dl className="mt-4 space-y-1.5">
              <Stat label="Sold" value={percent(item.sold_pct)} />
              <Stat label="Construction" value={percent(item.construction_pct)} />
              <Stat label="Collection efficiency" value={percent(item.collection_efficiency)} />
            </dl>
          </article>
        ))}
      </div>

      {data && (
        <SectionTabs items={[
          { key: "funnel", label: "Sales funnel", content: <div className="max-w-2xl"><ChartCard chart={data.funnel} /></div> },
          { key: "today", label: "Today's site visits", content: <BlockView block={{ ...data.site_visits_today, title: null } as Block} /> },
          { key: "handovers", label: "Upcoming handovers", content: <BlockView block={{ ...data.handovers, title: null } as Block} /> },
          { key: "rms", label: "Top 5 RMs", content: <BlockView block={{ ...data.top_rms, title: null } as Block} /> },
          { key: "partners", label: "Top 5 channel partners", content: <BlockView block={{ ...data.top_partners, title: null } as Block} /> },
        ]} />
      )}
    </>
  );
}
