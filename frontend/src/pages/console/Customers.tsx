import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ChartCard } from "@/components/data/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { KpiRow } from "@/components/data/KpiCard";
import { FilterChip, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { api } from "@/lib/api";
import type { Chart } from "@/lib/types";
import { useFilters } from "@/lib/urlState";

// Each bar of the health chart, as the score range the buyers list filters on.
const BAND_OF: Record<string, { min: number; max: number; label: string }> = {
  "Below 40": { min: 0, max: 39, label: "Health below 40" }, "40-59": { min: 40, max: 59, label: "Health 40 to 59" },
  "60-74": { min: 60, max: 74, label: "Health 60 to 74" }, "75-89": { min: 75, max: 89, label: "Health 75 to 89" },
  "90-100": { min: 90, max: 100, label: "Health 90 to 100" },
};

/** Customers: "Who are our buyers, and who is unhappy or at risk?" */
export default function Customers() {
  const { params } = useFilters();
  const [tab, setTab] = useState("buyers");
  const [band, setBand] = useState<{ min: number; max: number; label: string } | null>(null);
  const summary = useQuery({ queryKey: ["customers-summary", params], queryFn: () => api<{ health: Chart; types: Chart; countries: Chart }>("/customers/summary", { params }) });

  function pickBand(bar: string) {
    setBand(BAND_OF[bar] ?? null);
    setTab("buyers");
    document.getElementById("page-tabs")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <>
      <PageHeader title="Customers" question="Who are our buyers, and who is unhappy or at risk?" />
      <KpiRow keys={["total_buyers", "nri_share", "average_health", "at_risk_buyers", "open_queries"]} />

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <ChartCard chart={summary.data?.health} isLoading={summary.isPending} error={summary.error as Error | null}
          onSelect={pickBand} hint="Click a bar to list those buyers." />
        <ChartCard chart={summary.data?.types} isLoading={summary.isPending} error={summary.error as Error | null} />
      </div>

      <SectionTabs value={tab} onChange={setTab} items={[
        { key: "buyers", label: "Buyers", content: (
          <>
            {band && <FilterChip label={band.label} onClear={() => setBand(null)} />}
            <DataTable endpoint="/customers" params={{ ...params, health_min: band?.min, health_max: band?.max, sort: band ? "health" : undefined }} exportName="buyers" />
          </>
        ) },
        { key: "queries", label: "Open queries", content: <DataTable endpoint="/metrics/open_queries/rows" params={params} exportName="open-queries" /> },
        { key: "countries", label: "By country", content: <div className="max-w-3xl"><ChartCard chart={summary.data?.countries} isLoading={summary.isPending} /></div> },
      ]} />
    </>
  );
}
