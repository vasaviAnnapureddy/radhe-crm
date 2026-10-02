import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ChartCard } from "@/components/data/ChartCard";
import { DataTable } from "@/components/data/DataTable";
import { KpiRow } from "@/components/data/KpiCard";
import { Card, PageHeader, SectionTabs } from "@/components/data/PageHeader";
import { ErrorState, SkeletonBlock } from "@/components/data/States";
import { ScorePill } from "@/components/data/Value";
import { BlockView } from "@/components/views/Blocks";
import { EntityLink } from "@/components/views/EntityLink";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Block, Chart, Ref, ScoreCell } from "@/lib/types";
import { useDrawer, useFilters } from "@/lib/urlState";

interface Member { ref: Ref; role: string; headline: string; score: ScoreCell; is_new: boolean; is_head: boolean; on_leave: boolean }
interface Team {
  name: string; headcount: number; head: Ref | null; avg_score: ScoreCell; needs_attention: number; joined_in_period: number;
  roles: { role: string; count: number }[]; members: Member[];
}
type Workload = Chart & { average: number; refs: Ref[] };
interface Summary { teams: Team[]; leaderboards: Block[]; by_department: Chart; workload: Workload }

const tag = "rounded-full px-1.5 py-px text-[10px] font-semibold";

/** One person in the team directory. Hover the name for the quick view; click to pin the drawer. */
function MemberTile({ member }: { member: Member }) {
  return (
    <li className="rounded-md border border-line p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <EntityLink entity={member.ref} className="text-[13px]" />
          <p className="mt-0.5 truncate text-xs text-muted">{member.role}</p>
        </div>
        <ScorePill {...member.score} />
      </div>
      <p className="mt-2 truncate text-xs text-ink" title={member.headline}>{member.headline}</p>
      {(member.is_head || member.is_new || member.on_leave) && (
        <p className="mt-2 flex gap-1.5">
          {member.is_head && <span className={cn(tag, "bg-primary/10 text-primary")}>Team head</span>}
          {member.is_new && <span className={cn(tag, "bg-good/10 text-good")}>New joiner</span>}
          {member.on_leave && <span className={cn(tag, "bg-subtle text-muted")}>On leave</span>}
        </p>
      )}
    </li>
  );
}

/** Employees & Teams: "Which teams and people are doing well, and who needs support?" */
export default function Employees() {
  const { params } = useFilters();
  const drawer = useDrawer();
  const [teamName, setTeamName] = useState<string | null>(null);
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ["employees-summary", params],
    queryFn: () => api<Summary>("/employees/summary", { params }),
  });
  useEffect(() => { if (!teamName && data?.teams.length) setTeamName(data.teams[0].name); }, [data, teamName]);
  const team = data?.teams.find((item) => item.name === teamName);

  // Clicking a bar in the workload chart pins that relationship manager.
  function pickManager(name: string) {
    const person = data?.workload.refs.find((item) => item.label === name);
    if (person) drawer.open(person.type, person.id);
  }

  return (
    <>
      <PageHeader title="Employees & Teams" question="Which teams and people are doing well, and who needs support?" />
      <KpiRow keys={["headcount", "new_joiners", "avg_target_achievement", "people_needing_attention", "overdue_tasks"]} />

      {error && <div className="mt-6 rounded-card border border-line bg-surface"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></div>}

      {/* Two main visuals: the nine teams, and the people inside the team you pick. */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.7fr)]">
        <Card title="Teams" hint="Click a team to see its people.">
          {isPending && <SkeletonBlock rows={9} />}
          <ul className="-mx-2">
            {data?.teams.map((item) => (
              <li key={item.name}>
                <button type="button" onClick={() => setTeamName(item.name)} aria-pressed={item.name === teamName}
                  className={cn("flex w-full items-center justify-between gap-3 rounded-md px-2 py-2.5 text-left transition-colors duration-150",
                    item.name === teamName ? "bg-subtle" : "hover:bg-bg")}>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium text-ink">{item.name}</span>
                    <span className="block truncate text-xs text-muted">
                      {item.headcount} people{item.head && `, led by ${item.head.label}`}
                      {item.joined_in_period > 0 && ` · ${item.joined_in_period} joined in this period`}
                    </span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    {item.needs_attention > 0 && <span className={cn(tag, "bg-risk/10 text-risk")}>{item.needs_attention} need support</span>}
                    <ScorePill {...item.avg_score} />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <Card title={team ? `${team.name}: ${team.headcount} people` : "Team"}
          hint={team?.roles.map((role) => `${role.count} ${role.role}`).join(", ")}>
          {isPending && <SkeletonBlock rows={9} />}
          <ul className="grid max-h-[470px] gap-3 overflow-y-auto pr-1 sm:grid-cols-2 2xl:grid-cols-3">
            {team?.members.map((member) => <MemberTile key={member.ref.id} member={member} />)}
          </ul>
        </Card>
      </div>

      <SectionTabs items={[
        { key: "top", label: "Top performers", content: (
          <div className="grid gap-6 xl:grid-cols-2">
            {data?.leaderboards.map((board, i) => <BlockView key={i} block={board} />) ?? <SkeletonBlock rows={6} />}
          </div>
        ) },
        { key: "joiners", label: "New joiners", content: <DataTable endpoint="/metrics/new_joiners/rows" params={params} exportName="new-joiners" /> },
        { key: "attention", label: "Needs support", content: <DataTable endpoint="/metrics/people_needing_attention/rows" params={params} exportName="needs-support" /> },
        { key: "workload", label: "Workload and scores", content: (
          <div className="grid gap-6 xl:grid-cols-2">
            <ChartCard chart={data?.workload} isLoading={isPending} onSelect={pickManager}
              hint={data ? `Team average is ${data.workload.average} buyers. Click a bar to open that person.` : undefined} />
            <ChartCard chart={data?.by_department} isLoading={isPending} />
          </div>
        ) },
        { key: "people", label: "All 110 people", content: <DataTable endpoint="/employees" params={params} pageSize={15} exportName="employees" /> },
        { key: "tasks", label: "Overdue tasks", content: <DataTable endpoint="/metrics/overdue_tasks/rows" params={params} exportName="overdue-tasks" /> },
      ]} />
    </>
  );
}
