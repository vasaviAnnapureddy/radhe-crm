import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ChartCard } from "@/components/data/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { KpiRow } from "@/components/data/KpiCard";
import { FilterChip, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { api } from "@/lib/api";
import type { Chart } from "@/lib/types";
import { useFilters } from "@/lib/urlState";

/** Sales & Leads: "Is our sales engine healthy, and where are deals stuck?" */
export default function Sales() {
  const { params } = useFilters();
  const [tab, setTab] = useState("stalled");
  const [source, setSource] = useState<string | null>(null);
  const funnel = useQuery({ queryKey: ["sales-funnel", params], queryFn: () => api<{ funnel: Chart; sources: Chart }>("/sales/funnel", { params }) });
  const lost = useQuery({ queryKey: ["sales-lost", params], queryFn: () => api<{ lost: Chart; cancelled: Chart }>("/sales/lost/summary", { params }) });

  // Clicking a source bar opens "All leads" filtered to that source.
  function pickSource(name: string) {
    setSource(name);
    setTab("leads");
    document.getElementById("page-tabs")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <>
      <PageHeader title="Sales & Leads" question="Is our sales engine healthy, and where are deals stuck?" />
      <KpiRow keys={["new_leads", "site_visits", "visit_to_booking_conversion", "bookings_value", "cancellations"]} />

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <ChartCard chart={funnel.data?.funnel} isLoading={funnel.isPending} error={funnel.error as Error | null} />
        <ChartCard chart={funnel.data?.sources} isLoading={funnel.isPending} error={funnel.error as Error | null}
          onSelect={pickSource} hint="Click a source to see its leads." />
      </div>

      <SectionTabs value={tab} onChange={setTab} items={[
        { key: "stalled", label: "Stalled negotiations", content: <DataTable endpoint="/sales/stalled" params={params} exportName="stalled-negotiations" /> },
        { key: "lost", label: "Lost and cancelled", content: (
          <div className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-2">
              <ChartCard chart={lost.data?.lost} isLoading={lost.isPending} height={220} />
              <ChartCard chart={lost.data?.cancelled} isLoading={lost.isPending} height={220} />
            </div>
            <DataTable endpoint="/sales/lost" params={params} exportName="lost-leads" />
          </div>
        ) },
        { key: "partners", label: "Channel partners", content: <DataTable endpoint="/channel-partners" params={{ ...params, sort: "value", order: "desc" }} exportName="channel-partners" /> },
        { key: "leads", label: "All leads", content: (
          <>
            {source && <FilterChip label={source} onClear={() => setSource(null)} />}
            <DataTable endpoint="/leads" params={params} search={source ?? ""} exportName="leads" />
          </>
        ) },
        { key: "bookings", label: "All bookings", content: <DataTable endpoint="/bookings" params={params} exportName="bookings" /> },
      ]} />
    </>
  );
}
