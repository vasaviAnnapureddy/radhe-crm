import { useQuery } from "@tanstack/react-query";
import { CircleAlert } from "lucide-react";
import { api } from "@/lib/api";
import { dateText } from "@/lib/format";
import { useEntityBase } from "@/lib/entityBase";
import { entityUrl, type EntityView, type Fact, type Ref } from "@/lib/types";
import { ErrorState, SkeletonBlock } from "../data/States";
import { StatusPill, Value } from "../data/Value";

/** Label and value pairs in two columns. Used by the hover card and by drawer tabs. */
export function FactGrid({ facts, renderRef }: { facts: Fact[]; renderRef?: (fact: Fact) => React.ReactNode }) {
  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
      {facts.map((fact) => (
        <div key={fact.label} className="min-w-0">
          <dt className="text-xs text-muted">{fact.label}</dt>
          <dd className="mt-0.5 truncate text-sm font-medium text-ink">
            {fact.ref && renderRef ? renderRef(fact) : <Value value={fact.value} kind={fact.kind} />}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** The same order for every entity: identity, the numbers that matter, status, attention, last activity. */
export function QuickView({ view }: { view: EntityView }) {
  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-semibold text-ink">{view.title}</p>
          <p className="truncate text-xs text-muted">{view.subtitle}</p>
        </div>
        <StatusPill {...view.status} />
      </div>
      <div className="mt-4"><FactGrid facts={view.facts} /></div>
      {view.attention && (
        <p className="mt-4 flex items-start gap-2 rounded-md bg-risk/10 px-3 py-2 text-[13px] font-medium text-risk">
          <CircleAlert size={15} strokeWidth={1.75} className="mt-0.5 shrink-0" />
          {view.attention}
        </p>
      )}
      {view.last_activity && (
        <p className="mt-3 border-t border-line pt-3 text-xs text-muted">
          {view.last_activity.at && <span className="font-medium text-ink">{dateText(view.last_activity.at)}: </span>}
          {view.last_activity.text}
        </p>
      )}
    </div>
  );
}

export function useEntity(entity: { type: Ref["type"]; id: string }, quick: boolean, enabled = true) {
  const base = useEntityBase();
  return useQuery({
    queryKey: ["entity", base, entity.type, entity.id, quick ? "quick" : "full"],
    queryFn: () => api<EntityView>(entityUrl(base, entity.type, entity.id), { params: { view: quick ? "quick" : "full" } }),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/** Loads the small quick view only when the hover card opens. */
export function QuickViewLoader({ entity }: { entity: Ref }) {
  const { data, isError, error } = useEntity(entity, true);
  if (isError) return <ErrorState message={(error as Error).message} />;
  if (!data) return <SkeletonBlock rows={5} />;
  return <QuickView view={data} />;
}
