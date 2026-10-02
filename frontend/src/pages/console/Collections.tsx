import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router";
import { ChartCard } from "@/components/data/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { KpiRow } from "@/components/data/KpiCard";
import { FilterChip, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { api } from "@/lib/api";
import type { Chart } from "@/lib/types";
import { useFilters } from "@/lib/urlState";

/** Collections: "How much money is due, what came in, and what is stuck?" */
export default function Collections() {
  const { params } = useFilters();
  const [search] = useSearchParams();
  // Other pages can link straight to a tab, for example /console/collections?tab=blocked
  const [tab, setTab] = useState(search.get("tab") === "blocked" ? "blocked" : "overdue");
  const [bank, setBank] = useState<string | null>(null);
  const summary = useQuery({ queryKey: ["collections-summary", params], queryFn: () => api<{ ageing: Chart; by_bank: Chart }>("/collections/summary", { params }) });

  // Clicking a bank bar opens the overdue demands of buyers who borrow from that bank.
  function pickBank(name: string) {
    setBank(name === "No loan" ? null : name);
    setTab("overdue");
    document.getElementById("page-tabs")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <>
      <PageHeader title="Collections" question="How much money is due, what came in, and what is stuck?" />
      <KpiRow keys={["demands_raised", "collected", "collection_efficiency", "collections_overdue", "blocked_by_delay"]} />

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <ChartCard chart={summary.data?.ageing} isLoading={summary.isPending} error={summary.error as Error | null} />
        <ChartCard chart={summary.data?.by_bank} isLoading={summary.isPending} error={summary.error as Error | null}
          onSelect={pickBank} hint="Click a bank to see its overdue demands." />
      </div>

      <SectionTabs value={tab} onChange={setTab} items={[
        { key: "overdue", label: "Overdue", content: (
          <>
            {bank && <FilterChip label={bank} onClear={() => setBank(null)} />}
            <DataTable endpoint="/demands" params={{ ...params, tab: "overdue" }} search={bank ?? ""} exportName="overdue-demands" />
          </>
        ) },
        { key: "bank", label: "Awaiting bank disbursement", content: <DataTable endpoint="/demands" params={{ ...params, tab: "awaiting_bank" }} exportName="awaiting-bank" /> },
        { key: "blocked", label: "Blocked by construction delay", content: <DataTable endpoint="/demands" params={{ ...params, tab: "blocked" }} exportName="blocked-demands" /> },
        { key: "all", label: "All demands", content: <DataTable endpoint="/demands" params={{ ...params, tab: "all" }} exportName="demands" /> },
      ]} />
    </>
  );
}
