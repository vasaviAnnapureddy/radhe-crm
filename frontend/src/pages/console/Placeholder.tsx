import type { NavItem } from "@/app/nav";
import { PageHeader } from "@/components/data/PageHeader";
import { EmptyState } from "@/components/data/States";

/** Stands in for a console page until its phase builds it. */
export default function Placeholder({ item }: { item: NavItem }) {
  return (
    <>
      <PageHeader title={item.label} question={item.question} />
      <div className="rounded-card border border-line bg-surface">
        <EmptyState title="Not built yet" text={`This page is built in Phase ${item.phase}.`} />
      </div>
    </>
  );
}
