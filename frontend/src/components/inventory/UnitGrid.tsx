import type { CSSProperties } from "react";
import { EntityLink } from "../views/EntityLink";

export interface UnitCell {
  id: string; unit_no: string; config: string; facing: string; status: string;
  price_psf: number; days_unsold: number | null; payment_health: number | null;
}
export interface GridFloor { label: string; units: UnitCell[] }
export type ColourBy = "status" | "price" | "ageing" | "health";

export const COLOUR_MODES: { key: ColourBy; label: string }[] = [
  { key: "status", label: "Status" }, { key: "price", label: "Price per sq ft" },
  { key: "ageing", label: "Days unsold" }, { key: "health", label: "Buyer payment health" },
];

type Swatch = { label: string; style: CSSProperties };
const paint = (background: string, color = "#1C1F1D", borderColor = "transparent"): CSSProperties => ({ background, color, borderColor });
const QUIET = paint("#EFECE5", "#7A7F7B");

const STATUS: Record<string, Swatch> = {
  available: { label: "Available", style: paint("#FFFFFF", "#5E635F", "#E3DFD6") },
  blocked: { label: "Blocked", style: paint("#EBD3A0") },
  booked: { label: "Booked", style: paint("#C7D5C7") },
  registered: { label: "Registered", style: paint("#8FA88F") },
  handed_over: { label: "Handed over", style: paint("#2F4A3A", "#FFFFFF") },
};
const PRICE = [paint("#F1EADB"), paint("#DFCCA9"), paint("#CB9E78"), paint("#B5643C", "#FFFFFF")];
const AGEING: (Swatch & { max: number })[] = [
  { label: "Up to 90 days", max: 90, style: paint("#F1EADB") }, { label: "91 to 180", max: 180, style: paint("#DFCCA9") },
  { label: "181 to 270", max: 270, style: paint("#D9A94E") }, { label: "Over 270", max: Infinity, style: paint("#B4483C", "#FFFFFF") },
];
const HEALTH: (Swatch & { min: number })[] = [
  { label: "Healthy (75+)", min: 75, style: paint("#BFD8C9") }, { label: "Watch (60 to 74)", min: 60, style: paint("#EBD3A0") },
  { label: "At risk (below 60)", min: 0, style: paint("#B4483C", "#FFFFFF") },
];

function styleOf(unit: UnitCell, mode: ColourBy, range: [number, number] | null): CSSProperties {
  if (mode === "status") return (STATUS[unit.status] ?? STATUS.available).style;
  if (mode === "price") {
    if (!range || range[1] === range[0]) return PRICE[1];
    return PRICE[Math.min(3, Math.floor(((unit.price_psf - range[0]) / (range[1] - range[0])) * 4))];
  }
  if (mode === "ageing") return unit.days_unsold === null ? QUIET : AGEING.find((step) => unit.days_unsold! <= step.max)!.style;
  return unit.payment_health === null ? QUIET : HEALTH.find((step) => unit.payment_health! >= step.min)!.style;
}

function legendOf(mode: ColourBy, range: [number, number] | null): Swatch[] {
  if (mode === "status") return Object.values(STATUS);
  if (mode === "price") {
    const [low, high] = range ?? [0, 0];
    const step = (high - low) / 4;
    return PRICE.map((style, i) => ({ style, label: `₹${Math.round(low + step * i).toLocaleString("en-IN")} to ₹${Math.round(low + step * (i + 1)).toLocaleString("en-IN")}` }));
  }
  if (mode === "ageing") return [...AGEING, { label: "Sold", style: QUIET }];
  return [...HEALTH, { label: "Not sold", style: QUIET }];
}

/**
 * The unit grid: floors as rows, units as cells, coloured four different ways.
 * Hover a cell for the unit's quick view; click to pin its drawer.
 */
export function UnitGrid({ floors, mode, priceRange }: { floors: GridFloor[]; mode: ColourBy; priceRange: [number, number] | null }) {
  return (
    <div>
      <ul className="mb-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted" aria-label="Colour legend">
        {legendOf(mode, priceRange).map((item) => (
          <li key={item.label} className="flex items-center gap-2">
            <span className="h-3.5 w-3.5 rounded-[3px] border" style={item.style} />{item.label}
          </li>
        ))}
      </ul>
      <div className="max-h-[560px] overflow-auto pr-1">
        <table className="border-separate border-spacing-1">
          <tbody>
            {floors.map((floor) => (
              <tr key={floor.label}>
                <th scope="row" className="sticky left-0 whitespace-nowrap bg-surface pr-3 text-left text-xs font-medium text-muted">{floor.label}</th>
                {floor.units.map((unit) => (
                  <td key={unit.id} className="p-0">
                    <EntityLink plain entity={{ type: "unit", id: unit.id, label: unit.unit_no }}
                      className="flex h-8 w-[72px] items-center justify-center rounded-[4px] text-[11px] font-medium transition-transform duration-150 hover:scale-[1.06] hover:shadow-float">
                      <span style={styleOf(unit, mode, priceRange)} className="flex h-full w-full items-center justify-center rounded-[3px] border" aria-label={`${unit.unit_no}, ${unit.config}, ${unit.status.replace("_", " ")}`}>
                        {unit.unit_no}
                      </span>
                    </EntityLink>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
