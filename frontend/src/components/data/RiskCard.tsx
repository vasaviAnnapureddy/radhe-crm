import { ArrowRight } from "lucide-react";
import { Link, useLocation } from "react-router";
import type { RiskCard as Risk } from "@/lib/types";
import { keepFilters } from "@/lib/urlState";
import { EntityLink } from "../views/EntityLink";
import { RiskBadge, Value } from "./Value";

/** The console page where each risk category is explained in full. */
const PAGE_OF: Record<string, string> = {
  Construction: "construction", Collections: "collections", Sales: "sales", Customer: "customers",
  Inventory: "projects", People: "employees", Partner: "sales",
};

/**
 * One risk. Facts ("Observed") and the suggested action are kept apart, so a guess is never shown as a fact.
 * `compact` is the short form used in the Overview attention list.
 */
export function RiskCard({ risk, compact, footer }: { risk: Risk; compact?: boolean; footer?: React.ReactNode }) {
  const { search } = useLocation();
  const page = PAGE_OF[risk.category] ?? "risks";
  const refs = risk.refs.slice(0, compact ? 3 : 8);
  return (
    <article className={compact ? "py-4 first:pt-0 last:pb-0" : "rounded-card border border-line bg-surface p-5"}>
      <div className="flex items-start justify-between gap-3">
        <Link to={{ pathname: `/console/${page}`, search: keepFilters(search) }}
          className="group flex items-start gap-1.5 text-sm font-semibold leading-snug text-ink hover:text-primary">
          <span>{risk.title}</span>
          <ArrowRight size={14} strokeWidth={2} className="mt-0.5 shrink-0 text-neutral transition-transform duration-150 group-hover:translate-x-0.5" />
        </Link>
        <RiskBadge severity={risk.severity} />
      </div>
      <p className="mt-1 text-xs text-muted">{risk.category}</p>

      {!compact && (
        <>
          <h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">Observed</h4>
          <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-3">
            {risk.facts.map((fact) => (
              <div key={fact.label} className={String(fact.value).length > 40 ? "col-span-full" : undefined}>
                <dt className="text-xs text-muted">{fact.label}</dt>
                <dd className="text-sm font-medium text-ink"><Value value={fact.value} kind={fact.kind} /></dd>
              </div>
            ))}
          </dl>
          <h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">Suggested action</h4>
          <p className="mt-1 text-sm text-ink">{risk.suggested_action}</p>
        </>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px]">
        {refs.map((entity) => <EntityLink key={`${entity.type}:${entity.id}`} entity={entity} className="font-normal" />)}
        {risk.refs.length > refs.length && <span className="text-xs text-muted">and {risk.refs.length - refs.length} more</span>}
      </div>
      {footer}
    </article>
  );
}
