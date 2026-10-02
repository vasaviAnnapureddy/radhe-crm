// The shapes the backend sends. They are documented in docs/PROGRESS.md (Phase 4, API contract).

export type Tone = "good" | "watch" | "risk" | "neutral";
export type EntityType =
  | "customer" | "unit" | "tower" | "project" | "employee" | "lead" | "booking" | "partner" | "demand"
  | "milestone" | "contractor";

/** A clickable pointer to an entity. */
export interface Ref { type: EntityType; id: string; label: string }
export interface StatusCell { label: string; tone: Tone }
export interface ScoreCell { value: number; tone: Tone }

export interface Fact { label: string; value: unknown; kind: string; ref?: Ref }
export interface Column { key: string; label: string; kind: string; default: boolean }
/** `type` + `target_id` say which entity a row opens. `id` is only a unique key for the row. */
export type Row = Record<string, unknown> & { id: string; type?: EntityType; target_id?: string };
export interface ListReply { columns: Column[]; items: Row[]; total: number; page: number; page_size: number }

export interface Chart {
  title: string;
  type: "bar" | "line" | "stacked" | "funnel";
  kind: string;
  x: string[];
  series: { name: string; data: (number | null)[] }[];
}

export interface Metric {
  key: string; label: string; kind: string; value: number; previous_value: number | null;
  formula_text: string; row_count: number; sparkline: number[] | null; drilldown_url: string;
  is_flow: boolean;            // true: counted over the date range. false: an "as of today" number.
  period_note: string | null;  // for "as of today" numbers: what changed inside the date range
  filters: { date_from: string | null; date_to: string | null; project: string };
}

export interface ScorePart { key: string; label: string; weight: number; points: number; detail?: string }
export interface ScorecardPart extends ScorePart { target: number; actual: number; kind: string; achievement_pct: number }

export type Block =
  | { kind: "facts"; title?: string | null; items: Fact[] }
  | { kind: "table"; title?: string | null; columns: Column[]; rows: Row[] }
  | { kind: "timeline"; items: { at: string | null; title: string; text: string; tone: Tone }[] }
  | { kind: "score"; title: string; score: number; parts: ScorePart[]; formula: string }
  | { kind: "scorecard"; score: number; parts: ScorecardPart[]; formula: string; needs_attention: boolean }
  | { kind: "chart"; chart: Chart }
  | { kind: "notice"; tone: Tone; text: string }
  | { kind: "journey"; title: string; unit: Ref | string; next_step: string; steps: JourneyStep[] };

/** One step of a buyer's journey, from booking to living in the home. */
export interface JourneyStep {
  key: string; label: string; state: "done" | "current" | "upcoming" | "issue"; date: string | null; text: string; here: boolean;
}

/** A page of the employee or customer portal: the server sends everything the page shows. */
export interface PortalReply {
  title: string; subtitle: string; blocks: Block[];
  kpis: { label: string; value: number; kind: string; note: string | null }[];
}

export interface EntityView {
  type: EntityType; id: string; title: string; subtitle: string; status: StatusCell; facts: Fact[];
  attention: string | null; last_activity: { at: string | null; text: string } | null;
  tabs?: { key: string; label: string; blocks: Block[] }[];
}

export interface RiskCard {
  id: string; category: string; severity: "high" | "medium" | "low"; title: string; facts: Fact[]; impact: number;
  refs: Ref[]; suggested_action: string; status: "open" | "acknowledged" | "resolved"; owner: Ref | null;
}

export type Role = "admin" | "employee" | "customer";
/** `home` is where this person lands after signing in: the console, the employee portal or the customer portal. */
export interface User { id: string; name: string; email: string; role: Role; home: string }

/**
 * Where entity quick views and drawers are fetched from. Admin pages use each entity's own route
 * (/customers/{id}); portals use /portal/entity/{type}/{id}, which checks the record is yours.
 */
export function entityUrl(base: string | null, type: EntityType, id: string): string {
  return base ? `${base}/${type}/${id}` : `/${ENTITY_PATH[type]}/${id}`;
}

/** Where each entity type lives in the API. */
export const ENTITY_PATH: Record<EntityType, string> = {
  customer: "customers", unit: "units", tower: "towers", project: "projects", employee: "employees",
  lead: "leads", booking: "bookings", partner: "channel-partners", demand: "demands", milestone: "milestones",
  contractor: "contractors",
};
