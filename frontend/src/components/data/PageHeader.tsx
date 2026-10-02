import type { ReactNode } from "react";
import { Tabs, type TabItem } from "../ui/tabs";

/** The top of every console page: a serif title and the question the page answers. */
export function PageHeader({ title, question, actions }: { title: string; question?: string; actions?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-[30px] leading-tight text-ink">{title}</h1>
        {question && <p className="mt-1 text-sm text-muted">{question}</p>}
      </div>
      {actions}
    </header>
  );
}

/** A white card with a short title. Every data block on a page sits in one of these. */
export function Card({ title, hint, actions, children, className }: {
  title?: string; hint?: string; actions?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`rounded-card border border-line bg-surface ${className ?? ""}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 px-5 pt-4">
          <div>
            {title && <h2 className="text-sm font-semibold text-ink">{title}</h2>}
            {hint && <p className="mt-0.5 text-xs text-muted">{hint}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

/** Tabs inside a page. Everything that does not fit above the fold goes here. */
export function SectionTabs({ items, value, onChange }: { items: TabItem[]; value?: string; onChange?: (key: string) => void }) {
  return <div className="mt-8 scroll-mt-20" id="page-tabs"><Tabs items={items} value={value} onChange={onChange} /></div>;
}

/** Shows which chart filter is on, with a way to clear it. */
export function FilterChip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-subtle px-3 py-1 text-xs text-ink">
      Filtered by chart: <span className="font-semibold">{label}</span>
      <button type="button" onClick={onClear} className="text-muted underline underline-offset-2 hover:text-ink">Clear</button>
    </p>
  );
}
