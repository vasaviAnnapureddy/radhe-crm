// Indian formats for everything shown on screen: ₹ lakh and crore, en-IN grouping, dates in India time.

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DASH = "–";

function trim(value: number, decimals: number): string {
  return value.toFixed(decimals).replace(/\.?0+$/, "");
}

/** 42500000 -> "₹4.25 Cr", 3860000 -> "₹38.6 L", 12500 -> "₹12,500". */
export function inr(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) return DASH;
  const sign = amount < 0 ? "-" : "";
  const abs = Math.abs(amount);
  if (abs >= 1e7) {
    const crore = abs / 1e7;  // fewer decimals as the number grows: 4.25 Cr, 596.5 Cr, 2,851 Cr
    const decimals = crore >= 1000 ? 0 : crore >= 100 ? 1 : 2;
    return `${sign}₹${crore.toLocaleString("en-IN", { maximumFractionDigits: decimals })} Cr`;
  }
  if (abs >= 1e5) return `${sign}₹${trim(abs / 1e5, 1)} L`;
  return `${sign}₹${Math.round(abs).toLocaleString("en-IN")}`;
}

/** 1234567 -> "12,34,567". */
export function num(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return value.toLocaleString("en-IN", { maximumFractionDigits: decimals });
}

export function percent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return DASH;
  return `${trim(value, 1)}%`;
}

export function days(value: number | null | undefined): string {
  if (value === null || value === undefined) return DASH;
  return `${num(value)} ${Math.abs(value) === 1 ? "day" : "days"}`;
}

export function area(value: number | null | undefined, unit: "sqft" | "sqyd" = "sqft"): string {
  if (value === null || value === undefined) return DASH;
  return `${num(value)} ${unit === "sqft" ? "sq ft" : "sq yd"}`;
}

/** Year, month, day, hour, minute in India time. A value without a time zone is already India time. */
function istParts(value: string): [number, number, number, number, number] | null {
  const plain = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(value);
  if (!plain) return null;
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value);
  if (!hasZone) return [+plain[1], +plain[2], +plain[3], +(plain[4] ?? 0), +(plain[5] ?? 0)];
  const moment = new Date(value);
  if (Number.isNaN(moment.getTime())) return null;
  const ist = new Date(moment.getTime() + 330 * 60 * 1000); // India is UTC+5:30, with no daylight saving
  return [ist.getUTCFullYear(), ist.getUTCMonth() + 1, ist.getUTCDate(), ist.getUTCHours(), ist.getUTCMinutes()];
}

/** "2026-10-01" -> "01 Oct 2026". */
export function dateText(value: string | null | undefined): string {
  const parts = value ? istParts(value) : null;
  if (!parts) return DASH;
  return `${String(parts[2]).padStart(2, "0")} ${MONTHS[parts[1] - 1]} ${parts[0]}`;
}

/** "2026-10-01T09:15:00+00:00" -> "01 Oct 2026, 2:45 pm". */
export function dateTimeText(value: string | null | undefined): string {
  const parts = value ? istParts(value) : null;
  if (!parts) return DASH;
  const hour = parts[3] % 12 === 0 ? 12 : parts[3] % 12;
  return `${dateText(value)}, ${hour}:${String(parts[4]).padStart(2, "0")} ${parts[3] < 12 ? "am" : "pm"}`;
}

/** Change against the previous period, in percent. Null when there is nothing to compare with. */
export function changePct(current: number, previous: number | null | undefined): number | null {
  if (previous === null || previous === undefined || previous === 0) return null;
  return ((current - previous) / Math.abs(previous)) * 100;
}

/** Format a value by the `kind` the backend sends with it. */
export function formatValue(value: unknown, kind: string): string {
  if (value === null || value === undefined || value === "") return DASH;
  switch (kind) {
    case "money": return inr(value as number);
    case "percent": return percent(value as number);
    case "number": return num(value as number, 1);
    case "score": return num(value as number);
    case "days": return days(value as number);
    case "date": return dateText(value as string);
    case "datetime": return dateTimeText(value as string);
    case "sqft": return area(value as number, "sqft");
    case "sqyd": return area(value as number, "sqyd");
    default: return String(value);
  }
}
