"""Small helpers shared by every service: formats, cell builders, filters, paging."""
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

STATUS_TONES = {
    "good": ["paid", "registered", "handed_over", "possession", "resolved", "done", "closed", "booked", "active",
             "replied", "on_time", "low"],
    "watch": ["raised", "blocked", "agreement_signed", "in_progress", "acknowledged", "on_leave", "negotiation",
              "awaiting_disbursement", "medium", "scheduled", "not_raised", "waiting", "sanctioned", "disbursing"],
    "risk": ["overdue", "cancelled", "lost", "delayed", "high", "open", "no_show", "major", "exited"],
}
TONE_OF = {value: tone for tone, values in STATUS_TONES.items() for value in values}


def inr(amount) -> str:
    """Indian money text: 68000000 -> '₹6.8 Cr', 3860000 -> '₹38.6 L'."""
    amount = float(amount or 0)
    for size, unit in ((1e7, "Cr"), (1e5, "L")):
        if abs(amount) >= size:
            return f"₹{amount / size:.2f}".rstrip("0").rstrip(".") + f" {unit}"
    return f"₹{amount:,.0f}"


def nice(value: str) -> str:
    return str(value).replace("_", " ").capitalize()


def ref(kind: str, obj, label: str | None = None) -> dict | None:
    """A clickable pointer to an entity. The frontend opens its quick view and drawer."""
    if obj is None:
        return None
    label = label or getattr(obj, "name", None) or getattr(obj, "firm_name", None) or getattr(obj, "unit_no", "")
    return {"type": kind, "id": str(obj.id), "label": label}


def fact(label: str, value, kind: str = "text", ref: dict | None = None) -> dict:
    """One labelled value. `kind` tells the frontend how to format it (money, percent, date, days ...)."""
    out = {"label": label, "value": value, "kind": kind}
    if ref:
        out["ref"] = ref
    return out


def col(key: str, label: str, kind: str = "text", default: bool = True) -> dict:
    """A table column. `default=False` columns are only shown from the column chooser."""
    return {"key": key, "label": label, "kind": kind, "default": default}


def status(value: str, tone: str | None = None, label: str | None = None) -> dict:
    return {"label": label or nice(value), "tone": tone or TONE_OF.get(value, "neutral")}


def score_cell(value: float, good: float = 75, watch: float = 60) -> dict:
    return {"value": round(value), "tone": "good" if value >= good else "watch" if value >= watch else "risk"}


def mask_phone(phone: str | None) -> str:
    return f"{phone[:2]}xxxxxx{phone[-2:]}" if phone else ""


def mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    name, domain = email.split("@", 1)
    return f"{name[0]}***@{domain}"


def pct(part, whole) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


@dataclass(frozen=True)
class Filters:
    """The global filters from the top bar: a date range and an optional project."""
    date_from: date
    date_to: date
    project_id: uuid.UUID | None = None

    def covers(self, day) -> bool:
        return day is not None and self.date_from <= day <= self.date_to

    def project_ok(self, project_id) -> bool:
        return self.project_id is None or project_id == self.project_id

    def previous(self) -> "Filters":
        """The period of the same length just before this one."""
        span = self.date_to - self.date_from
        end = self.date_from - timedelta(days=1)
        return Filters(end - span, end, self.project_id)


def month_starts(today: date, count: int) -> list[date]:
    """The first day of each of the last `count` months, oldest first."""
    year, month, out = today.year, today.month, []
    for _ in range(count):
        out.append(date(year, month, 1))
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    return out[::-1]


def chart(title: str, x: list, series: list[dict], kind: str = "number", type: str = "bar", **extra) -> dict:
    """A chart the frontend can draw without knowing the page: x labels plus named series."""
    return {"title": title, "type": type, "kind": kind, "x": x, "series": series, **extra}


def _sort_value(cell):
    if isinstance(cell, dict):
        cell = cell.get("value", cell.get("label"))
    return cell


def paginate(columns: list[dict], rows: list[dict], page: int = 1, page_size: int = 25, sort: str | None = None,
             order: str = "asc", q: str | None = None) -> dict:
    if q:
        needle = q.lower()
        rows = [r for r in rows if any(needle in str(_sort_value(v)).lower() for k, v in r.items() if k != "id")]
    if sort and any(c["key"] == sort for c in columns):
        filled = [r for r in rows if _sort_value(r.get(sort)) is not None]
        empty = [r for r in rows if _sort_value(r.get(sort)) is None]
        filled.sort(key=lambda r: _sort_value(r[sort]), reverse=order == "desc")
        rows = filled + empty  # empty cells always go last
    start = (page - 1) * page_size
    return {"columns": columns, "items": rows[start:start + page_size], "total": len(rows), "page": page,
            "page_size": page_size}
