import { useQuery } from "@tanstack/react-query";
import { ChartCard } from "@/components/data/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { KpiRow } from "@/components/data/KpiCard";
import { Card, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { EmptyState, ErrorState, SkeletonBlock } from "@/components/data/States";
import { Area, DateText, Money, RiskBadge, ScorePill, StatusPill } from "@/components/data/Value";
import { Button } from "@/components/ui/button";
import { EntityLink } from "@/components/views/EntityLink";
import { QuickView } from "@/components/views/QuickView";
import { api } from "@/lib/api";
import type { Chart, EntityView, Ref } from "@/lib/types";
import { useFilters } from "@/lib/urlState";

const SWATCHES = [
  ["Background", "bg-bg"], ["Surface", "bg-surface"], ["Subtle", "bg-subtle"], ["Ink", "bg-ink"], ["Muted", "bg-muted"],
  ["Border", "bg-line"], ["Primary", "bg-primary"], ["Sidebar", "bg-sidebar"], ["Accent (clay)", "bg-accent"],
  ["Good", "bg-good"], ["Watch", "bg-watch"], ["Risk", "bg-risk"], ["Sage", "bg-sage"], ["Sand", "bg-sand"],
];

function Section({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return (
    <section className="mt-12">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      {note && <p className="mb-4 mt-1 text-sm text-muted">{note}</p>}
      <div className={note ? "" : "mt-4"}>{children}</div>
    </section>
  );
}

/** Every reusable component on one page, with live data, so the look can be reviewed in one place. */
export default function Styleguide() {
  const { params } = useFilters();
  const overview = useQuery({ queryKey: ["overview", params], queryFn: () => api<{ monthly: Chart; funnel: Chart }>("/overview", { params }) });
  const found = useQuery({ queryKey: ["search", "karthik reddy"], queryFn: () => api<{ items: Ref[] }[]>("/search", { params: { q: "karthik reddy" } }) });
  const karthik = found.data?.[0]?.items[0];
  const quick = useQuery({
    queryKey: ["entity", "customer", karthik?.id, "quick"],
    queryFn: () => api<EntityView>(`/customers/${karthik!.id}`, { params: { view: "quick" } }),
    enabled: Boolean(karthik),
  });

  return (
    <>
      <PageHeader title="Styleguide" question="Every reusable component in one place. Check it against docs/DESIGN.md sections 6.3 and 6.4."
        actions={<Button variant="accent">One clay action per screen</Button>} />

      <Section title="Colour" note="Colour carries meaning only: status and risk. Everything else is ink on warm off-white.">
        <div className="grid grid-cols-4 gap-3 md:grid-cols-7">
          {SWATCHES.map(([name, cls]) => (
            <div key={name}><div className={`h-12 rounded-md border border-line ${cls}`} /><p className="mt-1.5 text-xs text-muted">{name}</p></div>
          ))}
        </div>
      </Section>

      <Section title="Type" note="Fraunces for page titles. Manrope for everything else, with tabular numbers.">
        <Card>
          <p className="font-display text-[30px] leading-tight">Homes that grow with the land.</p>
          <p className="mt-3 text-sm text-ink">Body text in Manrope. Money <Money value={42500000} />, <Money value={3860000} /> and <Money value={12500} />. Area <Area value={2400} />. Date <DateText value="2026-10-01" />.</p>
          <p className="mt-1 text-xs text-muted">Secondary text is used for labels and hints.</p>
        </Card>
      </Section>

      <Section title="Buttons and pills">
        <Card>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary">Primary</Button><Button>Outline</Button><Button variant="ghost">Ghost</Button><Button disabled>Disabled</Button>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <StatusPill label="Paid" tone="good" /><StatusPill label="Agreement signed" tone="watch" /><StatusPill label="Overdue" tone="risk" /><StatusPill label="Available" tone="neutral" />
            <ScorePill value={88} tone="good" /><ScorePill value={64} tone="watch" /><ScorePill value={42} tone="risk" />
            <RiskBadge severity="high" /><RiskBadge severity="medium" /><RiskBadge severity="low" />
          </div>
        </Card>
      </Section>

      <Section title="KPI cards" note="At most four in a row and five on a page. The small icon opens Explain: formula, filters and rows.">
        <KpiRow keys={["bookings_value", "collections_received", "collections_overdue", "unsold_inventory_value"]} />
      </Section>

      <Section title="Charts" note="At most two main visuals above the fold. Each title says what the chart shows. Hover for exact values.">
        <div className="grid gap-6 xl:grid-cols-2">
          <ChartCard chart={overview.data?.monthly} isLoading={overview.isPending} error={overview.error as Error | null} />
          <ChartCard chart={overview.data?.funnel} isLoading={overview.isPending} error={overview.error as Error | null} />
        </div>
      </Section>

      <Section title="Hover to peek, click to pin" note="Hover the name for the quick view. Click it to pin the drawer. Links inside the drawer stack with a breadcrumb.">
        <div className="grid gap-6 xl:grid-cols-2">
          <Card title="Entity link">
            {karthik ? <p className="text-sm">Buyer: <EntityLink entity={karthik} /></p> : <SkeletonBlock rows={1} />}
          </Card>
          <Card title="Quick view card (shown here without hovering)">
            {quick.data ? <QuickView view={quick.data} /> : <SkeletonBlock rows={5} />}
          </Card>
        </div>
      </Section>

      <Section title="Data table" note="Six to seven columns by default; more from the column chooser. Search, sort, paging, CSV export. Click a row to pin its drawer.">
        <DataTable endpoint="/customers" params={params} pageSize={6} />
      </Section>

      <Section title="Tabs" note="Everything that does not fit above the fold goes into tabs.">
        <SectionTabs items={[
          { key: "stalled", label: "Stalled negotiations", content: <DataTable endpoint="/sales/stalled" params={params} pageSize={5} /> },
          { key: "partners", label: "Channel partners", content: <DataTable endpoint="/channel-partners" params={params} pageSize={5} /> },
        ]} />
      </Section>

      <Section title="Loading, empty and error states" note="Every data block has all three.">
        <div className="grid gap-6 md:grid-cols-3">
          <Card title="Loading"><SkeletonBlock rows={5} /></Card>
          <Card title="Empty"><EmptyState text="There are no rows for these filters." /></Card>
          <Card title="Error"><ErrorState message="Cannot reach the server." onRetry={() => undefined} /></Card>
        </div>
      </Section>
    </>
  );
}
