import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ChartCard } from "@/components/data/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { Card, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { ErrorState, Skeleton, SkeletonBlock } from "@/components/data/States";
import { ScorePill } from "@/components/data/Value";
import { COLOUR_MODES, UnitGrid, type ColourBy, type GridFloor } from "@/components/inventory/UnitGrid";
import { BlockView } from "@/components/views/Blocks";
import { EntityLink } from "@/components/views/EntityLink";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { dateText, num, percent } from "@/lib/format";
import type { Block, Chart, ScoreCell } from "@/lib/types";
import { useFilters } from "@/lib/urlState";

interface ProjectCard {
  id: string; name: string; kind: string; locality: string; rera_no: string; launch_date: string; expected_possession: string;
  status: string; units: number; sold: number; sold_pct: number; construction_pct: number | null; health: ScoreCell;
  towers: { id: string; name: string }[];
}
interface InventoryReply {
  towers: { id: string; name: string }[]; floors: GridFloor[]; price_range: [number, number] | null;
  status_counts: Record<string, number>; price_trend: Chart; towers_table: Block;
}

const pill = "rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors duration-150";
const pillOn = "bg-primary text-white";
const pillOff = "text-muted hover:bg-subtle hover:text-ink";

/** Projects & Inventory: "What are we building, what is sold, and what is not moving?" */
export default function Projects() {
  const { projectId: filterProject } = useFilters();
  const projects = useQuery({ queryKey: ["projects"], queryFn: () => api<ProjectCard[]>("/projects"), staleTime: Infinity });
  const [projectId, setProjectId] = useState<string | null>(null);
  const [towerId, setTowerId] = useState<string | null>(null);
  const [mode, setMode] = useState<ColourBy>("status");

  // Start on the project chosen in the top bar, or the first one.
  useEffect(() => {
    const wanted = filterProject ?? projectId ?? projects.data?.[0]?.id ?? null;
    if (wanted !== projectId) { setProjectId(wanted); setTowerId(null); }
  }, [filterProject, projects.data]);  // eslint-disable-line react-hooks/exhaustive-deps

  const project = projects.data?.find((p) => p.id === projectId);
  const inventory = useQuery({
    queryKey: ["inventory", projectId, towerId],
    queryFn: () => api<InventoryReply>(`/projects/${projectId}/inventory`, { params: { tower_id: towerId } }),
    enabled: Boolean(projectId),
  });
  const activeTower = towerId ?? inventory.data?.towers[0]?.id ?? null;

  return (
    <>
      <PageHeader title="Projects & Inventory" question="What are we building, what is sold, and what is not moving?" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-5">
        {projects.isPending && Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-[190px] rounded-card" />)}
        {projects.data?.map((p) => (
          // Capture phase: a click anywhere on the card, including on the project name, selects it for the grid.
          <article key={p.id} onClickCapture={() => { if (p.id !== projectId) { setProjectId(p.id); setTowerId(null); } }}
            className={cn("cursor-pointer rounded-card border bg-surface p-4 transition-colors duration-150", p.id === projectId ? "border-primary" : "border-line hover:border-neutral")}>
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <EntityLink entity={{ type: "project", id: p.id, label: p.name }} className="text-sm" />
                <p className="mt-0.5 truncate text-xs text-muted">{p.kind}, {p.locality}</p>
              </div>
              <ScorePill {...p.health} />
            </div>
            <dl className="mt-4 space-y-1.5 text-xs">
              <div className="flex justify-between"><dt className="text-muted">Sold</dt><dd className="font-medium">{num(p.sold)} of {num(p.units)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted">Construction</dt><dd className="font-medium">{percent(p.construction_pct)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted">Launched</dt><dd className="font-medium">{dateText(p.launch_date)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted">Possession</dt><dd className="font-medium">{dateText(p.expected_possession)}</dd></div>
            </dl>
            <p className="mt-3 truncate border-t border-line pt-2.5 text-[11px] text-neutral" title="Fictional registration number">RERA {p.rera_no}</p>
            <p className={cn("mt-2 text-[11px] font-medium", p.id === projectId ? "text-primary" : "text-muted")}>
              {p.id === projectId ? "Shown in the grid below" : "Click to show its units"}
            </p>
          </article>
        ))}
      </div>

      <Card className="mt-6" title={project ? `Unit inventory, ${project.name}` : "Unit inventory"}
        hint="Hover a unit for its details. Click to pin it."
        actions={
          <div className="flex flex-wrap items-center justify-end gap-1" role="group" aria-label="Colour the grid by">
            {COLOUR_MODES.map((item) => (
              <button key={item.key} type="button" onClick={() => setMode(item.key)} aria-pressed={mode === item.key}
                className={cn(pill, mode === item.key ? pillOn : pillOff)}>{item.label}</button>
            ))}
          </div>
        }>
        {(inventory.data?.towers.length ?? 0) > 1 && (
          <div className="mb-5 flex gap-1 border-b border-line pb-4" role="group" aria-label="Tower">
            {inventory.data!.towers.map((tower) => (
              <button key={tower.id} type="button" onClick={() => setTowerId(tower.id)} aria-pressed={activeTower === tower.id}
                className={cn(pill, activeTower === tower.id ? "bg-subtle text-ink" : pillOff)}>{tower.name}</button>
            ))}
          </div>
        )}
        {inventory.isError && <ErrorState message={(inventory.error as Error).message} onRetry={() => inventory.refetch()} />}
        {inventory.isPending && <SkeletonBlock rows={10} />}
        {inventory.data && <UnitGrid floors={inventory.data.floors} mode={mode} priceRange={inventory.data.price_range} />}
      </Card>

      {projectId && (
        <SectionTabs items={[
          { key: "ageing", label: "Inventory ageing", content: <DataTable endpoint="/units" params={{ project_id: projectId, ageing: 1 }} exportName="inventory-ageing" /> },
          { key: "price", label: "Price trend", content: <div className="max-w-3xl"><ChartCard chart={inventory.data?.price_trend} isLoading={inventory.isPending} /></div> },
          { key: "towers", label: "Towers", content: inventory.data ? <BlockView block={{ ...inventory.data.towers_table, title: null } as Block} /> : <SkeletonBlock /> },
        ]} />
      )}
    </>
  );
}
