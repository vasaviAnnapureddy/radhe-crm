import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "@/components/data/PageHeader";
import { RiskCard } from "@/components/data/RiskCard";
import { EmptyState, ErrorState, Skeleton } from "@/components/data/States";
import { EntityLink } from "@/components/views/EntityLink";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { RiskCard as Risk } from "@/lib/types";

interface RisksReply { high_open: number; categories: Record<string, number>; items: Risk[] }
type Status = Risk["status"];

const CATEGORIES = ["Construction", "Collections", "Sales", "Customer", "Inventory", "People", "Partner"];
const STATUSES: { key: Status; label: string }[] = [
  { key: "open", label: "Open" }, { key: "acknowledged", label: "Acknowledged" }, { key: "resolved", label: "Resolved" },
];
const chip = "rounded-full border px-3 py-1 text-[13px] font-medium transition-colors duration-150";
const chipOn = "border-primary bg-primary text-white";
const chipOff = "border-line bg-surface text-muted hover:border-neutral hover:text-ink";

/** Risks & Alerts: every risk the rules found, with its facts, linked entities and suggested action. */
export default function Risks() {
  const client = useQueryClient();
  const [category, setCategory] = useState<string | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const { data, isPending, error, refetch } = useQuery({ queryKey: ["risks"], queryFn: () => api<RisksReply>("/risks") });

  // The only change the console can make: a risk's status. It is saved and written to the audit log.
  const change = useMutation({
    mutationFn: (input: { id: string; status: Status }) => api<Risk>(`/risks/${input.id}`, { method: "PATCH", body: { status: input.status } }),
    onSuccess: () => {
      for (const key of ["risks", "overview", "metric", "metrics"]) client.invalidateQueries({ queryKey: [key] });
    },
  });

  const shown = (data?.items ?? []).filter((risk) => (!category || risk.category === category) && (!status || risk.status === status));
  const high = data?.high_open ?? 0;

  return (
    <>
      <PageHeader title="Risks & Alerts"
        question={data ? `${high} high-priority ${high === 1 ? "item needs" : "items need"} attention` : "What needs attention first?"} />

      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filter by category">
        <button type="button" onClick={() => setCategory(null)} className={cn(chip, category === null ? chipOn : chipOff)}>All</button>
        {CATEGORIES.map((name) => (
          <button key={name} type="button" onClick={() => setCategory(category === name ? null : name)} aria-pressed={category === name}
            className={cn(chip, category === name ? chipOn : chipOff)}>
            {name}{data?.categories[name] ? <span className="ml-1.5 opacity-70">{data.categories[name]}</span> : null}
          </button>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-[13px] text-muted" role="group" aria-label="Filter by status">
        Status:
        {STATUSES.map((item) => (
          <button key={item.key} type="button" onClick={() => setStatus(status === item.key ? null : item.key)} aria-pressed={status === item.key}
            className={cn("rounded-md px-2 py-1 font-medium", status === item.key ? "bg-subtle text-ink" : "hover:text-ink")}>{item.label}</button>
        ))}
      </div>

      {change.isError && <p role="alert" className="mt-4 rounded-md bg-risk/10 px-3 py-2 text-sm text-risk">The status could not be saved: {(change.error as Error).message}</p>}

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        {error && <div className="rounded-card border border-line bg-surface xl:col-span-2"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>}
        {isPending && Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-64 rounded-card" />)}
        {data && !shown.length && <div className="rounded-card border border-line bg-surface xl:col-span-2"><EmptyState title="Nothing here" text="No risks match these filters." /></div>}
        {shown.map((risk) => (
          <RiskCard key={risk.id} risk={risk} footer={
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-3">
              <p className="text-xs text-muted">Owner: {risk.owner ? <EntityLink entity={risk.owner} className="font-normal" /> : "Not assigned"}</p>
              <div className="flex gap-1" role="group" aria-label="Change status">
                {STATUSES.map((item) => (
                  <button key={item.key} type="button" disabled={change.isPending} aria-pressed={risk.status === item.key}
                    onClick={() => risk.status !== item.key && change.mutate({ id: risk.id, status: item.key })}
                    className={cn("rounded-md px-2.5 py-1 text-xs font-medium transition-colors duration-150",
                      risk.status === item.key ? (item.key === "resolved" ? "bg-good/15 text-good" : item.key === "acknowledged" ? "bg-watch/20 text-[#8a6212]" : "bg-subtle text-ink") : "text-muted hover:bg-subtle hover:text-ink")}>
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          } />
        ))}
      </div>
    </>
  );
}
