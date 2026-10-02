import { Check, Info } from "lucide-react";
import { cn, TONE_DOT } from "@/lib/cn";
import { dateText, dateTimeText, formatValue } from "@/lib/format";
import type { Block, Fact, JourneyStep, Ref, ScorecardPart, ScorePart } from "@/lib/types";
import { useDrawer } from "@/lib/urlState";
import { Cell, RIGHT_ALIGNED } from "../data/Cell";
import { ChartCard } from "../data/ChartCard";
import { EmptyState } from "../data/States";
import { EntityLink } from "./EntityLink";
import { FactGrid } from "./QuickView";

const MAX_ROWS = 50;

function linkFact(fact: Fact) {
  return <EntityLink entity={{ ...(fact.ref as Ref), label: String(fact.value) }} />;
}

function BlockTitle({ text }: { text?: string | null }) {
  return text ? <h3 className="mb-3 text-sm font-semibold text-ink">{text}</h3> : null;
}

function TableBlock({ block }: { block: Extract<Block, { kind: "table" }> }) {
  const drawer = useDrawer();
  const columns = block.columns.filter((c) => c.default);
  if (!block.rows.length) return <div><BlockTitle text={block.title} /><div className="rounded-card border border-line bg-surface"><EmptyState text="No rows." /></div></div>;
  return (
    <div>
      <BlockTitle text={block.title} />
      <div className="overflow-x-auto rounded-card border border-line bg-surface">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-line">
              {columns.map((c) => <th key={c.key} className={cn("whitespace-nowrap px-3 py-2.5 text-xs font-semibold text-muted", RIGHT_ALIGNED.has(c.kind) ? "text-right" : "text-left")}>{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {block.rows.slice(0, MAX_ROWS).map((row) => (
              <tr key={row.id} onClick={row.type ? () => drawer.open(row.type!, row.target_id ?? row.id) : undefined}
                className={cn("border-b border-line last:border-0", row.type && "cursor-pointer hover:bg-bg")}>
                {columns.map((c) => <td key={c.key} className={cn("max-w-[200px] truncate px-3 py-2.5", RIGHT_ALIGNED.has(c.kind) && "text-right")}><Cell value={row[c.key]} kind={c.kind} /></td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {block.rows.length > MAX_ROWS && <p className="mt-2 text-xs text-muted">Showing the first {MAX_ROWS} of {block.rows.length} rows.</p>}
    </div>
  );
}

/** A score with its parts, so the admin can see why the number is what it is. */
function ScoreBlock({ title, score, parts, formula }: { title: string; score: number; parts: ScorePart[]; formula: string }) {
  return (
    <div className="rounded-card border border-line bg-surface p-5">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        <p className="text-2xl font-semibold text-ink">{score}<span className="text-sm font-normal text-muted"> / 100</span></p>
      </div>
      <ul className="mt-4 space-y-4">
        {parts.map((part) => (
          <li key={part.key}>
            <div className="flex justify-between text-[13px]">
              <span className="font-medium text-ink">{part.label}</span>
              <span className="text-muted">{part.points} of {part.weight}</span>
            </div>
            <div className="mt-1.5 h-1.5 rounded-full bg-subtle"><div className="h-full rounded-full bg-primary" style={{ width: `${(part.points / part.weight) * 100}%` }} /></div>
            {part.detail && <p className="mt-1 text-xs text-muted">{part.detail}</p>}
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t border-line pt-3 text-xs text-muted">{formula}</p>
    </div>
  );
}

function ScorecardBlock({ block }: { block: Extract<Block, { kind: "scorecard" }> }) {
  const parts: ScorePart[] = block.parts.map((p: ScorecardPart) => ({
    ...p, detail: `Target ${formatValue(p.target, p.kind)}, actual ${formatValue(p.actual, p.kind)}, achievement ${p.achievement_pct}%`,
  }));
  return <ScoreBlock title="Scorecard" score={block.score} parts={parts} formula={block.formula} />;
}

function TimelineBlock({ block }: { block: Extract<Block, { kind: "timeline" }> }) {
  if (!block.items.length) return <div className="rounded-card border border-line bg-surface"><EmptyState text="No activity yet." /></div>;
  return (
    <ol className="space-y-0">
      {block.items.slice(0, MAX_ROWS).map((item, i) => (
        <li key={i} className="relative border-l border-line pb-5 pl-5 last:pb-0">
          <span className={cn("absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full ring-2 ring-bg", TONE_DOT[item.tone])} />
          <p className="text-xs text-muted">{dateTimeText(item.at)} · {item.title}</p>
          <p className={cn("mt-0.5 text-sm", item.tone === "risk" ? "font-medium text-risk" : "text-ink")}>{item.text}</p>
        </li>
      ))}
    </ol>
  );
}

/** One honest line the person should read first, for example a delay or a waiting reply. */
function Notice({ tone, text }: { tone: string; text: string }) {
  const style = tone === "risk" ? "border-risk/30 bg-risk/10 text-risk" : tone === "good" ? "border-good/30 bg-good/10 text-good" : "border-line bg-subtle text-muted";
  return (
    <p className={cn("flex items-start gap-2.5 rounded-card border px-4 py-3 text-sm font-medium", style)}>
      <Info size={16} strokeWidth={1.75} className="mt-0.5 shrink-0" />{text}
    </p>
  );
}

const STEP_STYLE: Record<JourneyStep["state"], string> = {
  done: "border-good bg-good text-white", current: "border-primary bg-surface text-primary",
  issue: "border-risk bg-risk text-white", upcoming: "border-line bg-surface text-neutral",
};

/** A buyer's path from booking to living in the home. The current step is marked "You are here". */
function Journey({ block }: { block: Extract<Block, { kind: "journey" }> }) {
  return (
    <section className="rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-xl text-ink">{block.title}</h2>
        {typeof block.unit !== "string" && <EntityLink entity={block.unit} className="text-[13px] font-normal">See unit details</EntityLink>}
      </div>
      <p className="mt-4 rounded-md bg-subtle px-4 py-3 text-sm text-ink">
        <span className="font-semibold">What happens next: </span>{block.next_step}
      </p>
      <ol className="mt-6">
        {block.steps.map((step, i) => (
          <li key={step.key} className="relative flex gap-4 pb-6 last:pb-0">
            {i < block.steps.length - 1 && <span className={cn("absolute left-[13px] top-7 h-full w-px", step.state === "done" ? "bg-good" : "bg-line")} />}
            <span className={cn("relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold", STEP_STYLE[step.state])}>
              {step.state === "done" ? <Check size={14} strokeWidth={2.5} /> : step.state === "issue" ? "!" : i + 1}
            </span>
            <div className={cn("min-w-0 flex-1 rounded-md", step.here && "-mt-2 border border-line bg-bg px-4 py-3")}>
              <div className="flex flex-wrap items-baseline justify-between gap-x-4">
                <h3 className={cn("text-sm font-semibold", step.state === "upcoming" ? "text-muted" : "text-ink")}>
                  {step.label}
                  {step.here && <span className="ml-2 rounded-full bg-primary px-2 py-0.5 text-[10px] font-semibold text-white">You are here</span>}
                </h3>
                {step.date && <span className="text-xs text-muted">{dateText(step.date)}</span>}
              </div>
              <p className={cn("mt-1 text-[13px] leading-relaxed", step.state === "issue" ? "text-ink" : "text-muted")}>{step.text}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

/** Draws one block of a drawer tab. The backend decides which blocks a tab has. */
export function BlockView({ block }: { block: Block }) {
  switch (block.kind) {
    case "facts":
      return (
        <div>
          <BlockTitle text={block.title} />
          <div className="rounded-card border border-line bg-surface p-5"><FactGrid facts={block.items} renderRef={linkFact} /></div>
        </div>
      );
    case "table": return <TableBlock block={block} />;
    case "timeline": return <TimelineBlock block={block} />;
    case "score": return <ScoreBlock {...block} />;
    case "scorecard": return <ScorecardBlock block={block} />;
    case "chart": return <ChartCard chart={block.chart} height={220} />;
    case "notice": return <Notice tone={block.tone} text={block.text} />;
    case "journey": return <Journey block={block} />;
  }
}
