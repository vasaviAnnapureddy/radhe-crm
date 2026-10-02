import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Link, useLocation } from "react-router";
import { DataTable } from "@/components/data/DataTable";
import { KpiRow } from "@/components/data/KpiCard";
import { Card, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { EmptyState, ErrorState, SkeletonBlock } from "@/components/data/States";
import { Money } from "@/components/data/Value";
import { BlockView } from "@/components/views/Blocks";
import { EntityLink } from "@/components/views/EntityLink";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { dateText, days } from "@/lib/format";
import type { Block, Ref } from "@/lib/types";
import { keepFilters, useFilters } from "@/lib/urlState";

interface Stage { id: string; label: string; planned: string; actual: string | null; slip_days: number; state: "done" | "delayed" | "upcoming" }
interface Impact {
  milestone: Ref; tower: Ref; stage: string; planned: string; slip_days: number; contractor: Ref | null; cause: string | null;
  bookings: number; amount: number; buyers: Ref[]; demands: Block;
}
interface Summary { timeline: { title: string; towers: { tower: Ref; stages: Stage[] }[] }; delay_impact: Impact[] }

const ON_TIME_GRACE_DAYS = 7; // same rule as the backend: up to a week late still counts as on time

function stageStyle(stage: Stage): string {
  if (stage.state === "delayed") return "bg-risk text-white";
  if (stage.state === "upcoming") return "border border-line bg-surface text-muted";
  return stage.slip_days > ON_TIME_GRACE_DAYS ? "bg-watch/30 text-ink" : "bg-good/15 text-ink";
}

const shortDate = (value: string) => dateText(value).replace(/ 20(\d\d)$/, " '$1");

/** Planned vs actual, one row per tower and one column per stage. Hover a cell for the milestone. */
function Timeline({ data }: { data: Summary["timeline"] }) {
  if (!data.towers.length) return <EmptyState text="This project has no towers to track." />;
  const labels = data.towers[0].stages.map((stage) => stage.label);
  return (
    <div>
      <ul className="mb-4 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted" aria-label="Legend">
        {[["bg-good/15", "Done on time"], ["bg-watch/30", "Done late"], ["bg-risk", "Late and still open"], ["border border-line bg-surface", "Upcoming"]].map(([cls, label]) => (
          <li key={label} className="flex items-center gap-2"><span className={cn("h-3 w-3 rounded-[3px]", cls)} />{label}</li>
        ))}
      </ul>
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-1 text-[11px]">
          <thead>
            <tr>
              <th className="pr-3 text-left font-medium text-muted">Tower</th>
              {labels.map((label) => <th key={label} className="px-1 pb-1 text-left font-medium text-muted">{label}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.towers.map((row) => (
              <tr key={row.tower.id}>
                <th scope="row" className="whitespace-nowrap pr-3 text-left text-xs font-normal"><EntityLink entity={row.tower} /></th>
                {row.stages.map((stage) => (
                  <td key={stage.id} className="p-0">
                    <EntityLink plain entity={{ type: "milestone", id: stage.id, label: stage.label }}
                      className={cn("block w-full min-w-[84px] rounded-[4px] px-2 py-1.5 text-left leading-tight transition-shadow duration-150 hover:shadow-float", stageStyle(stage))}>
                      <span className="block font-medium">{shortDate(stage.actual ?? stage.planned)}</span>
                      <span className="block opacity-80">
                        {stage.state === "upcoming" ? "planned" : stage.slip_days > 0 ? `${stage.slip_days} d late` : "on time"}
                      </span>
                    </EntityLink>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** What one late stage costs: the demands it blocks, the buyers affected, the money not yet raised. */
function DelayImpact({ items }: { items: Impact[] }) {
  const { search } = useLocation();
  if (!items.length) return <EmptyState title="No open delays" text="Every stage is on or ahead of its planned date." />;
  return (
    <div className="space-y-6">
      {items.map((item) => (
        <article key={item.milestone.id}>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-sm font-semibold text-ink">
              <EntityLink entity={item.milestone} className="font-semibold">{item.stage}</EntityLink>, <EntityLink entity={item.tower} className="font-semibold" />
            </h3>
            <span className="rounded-full bg-risk/10 px-2.5 py-0.5 text-xs font-semibold text-risk">{days(item.slip_days)} late</span>
          </div>
          <p className="mt-1 text-xs text-muted">
            Planned {dateText(item.planned)}{item.contractor && <> · Contractor <EntityLink entity={item.contractor} className="font-normal" /></>}
          </p>

          <div className="mt-4 grid gap-x-12 gap-y-4 lg:grid-cols-2">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">Observed</h4>
              <dl className="mt-2 grid grid-cols-3 gap-4">
                <div><dt className="text-xs text-muted">Money not yet raised</dt><dd className="text-xl font-semibold text-ink"><Money value={item.amount} /></dd></div>
                <div><dt className="text-xs text-muted">Bookings blocked</dt><dd className="text-xl font-semibold text-ink">{item.bookings}</dd></div>
                <div><dt className="text-xs text-muted">Buyers affected</dt><dd className="text-xl font-semibold text-ink">{item.buyers.length}</dd></div>
              </dl>
              {item.cause && (<>
                <h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">Reported cause</h4>
                <p className="mt-1 text-sm text-ink">{item.cause}</p>
              </>)}
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">Buyers waiting</h4>
              <p className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[13px]">
                {item.buyers.slice(0, 10).map((buyer) => <EntityLink key={buyer.id} entity={buyer} className="font-normal" />)}
                {item.buyers.length > 10 && <span className="text-muted">and {item.buyers.length - 10} more</span>}
              </p>
              <Link to={{ pathname: "/console/collections", search: `${keepFilters(search) || "?"}${keepFilters(search) ? "&" : ""}tab=blocked` }}
                className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-medium text-primary hover:underline">
                See the {item.bookings} blocked demands in Collections <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

/** Construction: "Are we building on time, and what does a delay cost us?" */
export default function Construction() {
  const { params } = useFilters();
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ["construction-summary", params],
    queryFn: () => api<Summary>("/construction/summary", { params }),
  });
  return (
    <>
      <PageHeader title="Construction" question="Are we building on time, and what does a delay cost us?" />
      <KpiRow keys={["towers_on_schedule", "average_slip_days", "milestones_due_this_month", "cost_variance_pct", "open_quality_issues"]} />

      {error && <div className="mt-6 rounded-card border border-line bg-surface"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>}
      {/* Two main visuals, stacked: the timeline needs the full width for its nine stages. */}
      <div className="mt-6 space-y-6">
        <Card title="What the delay costs" hint="Construction links to Collections and to Customers here.">
          {isPending ? <SkeletonBlock rows={6} /> : data && <DelayImpact items={data.delay_impact} />}
        </Card>
        <Card title="Planned vs actual milestones, by tower" hint="Each cell shows the actual date, or the planned date if the stage has not finished.">
          {isPending ? <SkeletonBlock rows={9} /> : data && <Timeline data={data.timeline} />}
        </Card>
      </div>

      <SectionTabs items={[
        { key: "blocked", label: "Blocked demands", content: data?.delay_impact.length
          ? <div className="space-y-6">{data.delay_impact.map((item) => <BlockView key={item.milestone.id} block={item.demands} />)}</div>
          : <div className="rounded-card border border-line bg-surface"><EmptyState text="No demands are blocked." /></div> },
        { key: "milestones", label: "All milestones", content: <DataTable endpoint="/construction/milestones" params={params} exportName="milestones" /> },
        { key: "contractors", label: "Contractors", content: <DataTable endpoint="/construction/contractors" params={params} pageSize={12} exportName="contractors" /> },
        { key: "budgets", label: "Budgets vs actual", content: <DataTable endpoint="/construction/budgets" params={params} pageSize={25} searchable={false} exportName="budgets" /> },
        { key: "quality", label: "Quality log", content: <DataTable endpoint="/construction/quality" params={params} exportName="quality-issues" /> },
        { key: "safety", label: "Safety log", content: <DataTable endpoint="/construction/safety" params={params} searchable={false} exportName="safety" /> },
      ]} />
    </>
  );
}
