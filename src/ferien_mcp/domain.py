"""Domain logic: shape ferien-api.de responses into compact dicts
(stdlib only).

Data source: the free ferien-api.de API — German school holidays
(Schulferien) per year and federal state, no key, no login. The API is
a thin wrapper over the .ics calendars in the bundesAPI project
(paulbrejla/ferien-api, data in paulbrejla/ferien-api-data).

- GET /api/v1/holidays/{STATE}/{YEAR} — one state, one year; a list of
  HolidayDto objects. A state/year the API has no data for returns an
  empty list (HTTP 200) — e.g. BE/2026 and BY/2030 were empty on
  2026-11-14, while BE/2025 has 7 entries. An unknown state code
  returns HTTP 400 with a Spring error body.
- GET /api/v1/holidays/{STATE} — one state, all years.
- GET /api/v1/holidays — everything (large; not used by the tools).

HolidayDto: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD",
"year": int, "stateCode": "BY", "name": "sommerferien bayern 2026",
"slug": "sommerferien bayern 2026-2026-BY"}. Names are lowercase
German ("<kind> <state name> <year>"), sometimes with a
"(beweglicher ferientag)" suffix for single movable days.

Enrichment: duration_days (inclusive), start/end weekdays (English +
German), and a "kind" derived from the name (winterferien,
frühjahrsferien, osterferien, pfingstferien, sommerferien,
herbstferien, weihnachtsferien, beweglicher ferientag).
"""
from __future__ import annotations

import json
import re
from datetime import date
from urllib.parse import quote_plus

BASE = "https://ferien-api.de/api/v1"

# The 16 federal states (Bundesländer). Codes are the ones the API
# accepts as {STATE}. There is no NATIONAL endpoint — school holidays
# are per-state only.
STATES = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen",
}

STATE_CODES = sorted(STATES)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_MIN, YEAR_MAX = 2000, 2100
MAX_RANGE_DAYS = 731  # holidays_between: at most ~2 years

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
               "Saturday", "Sunday"]
WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
               "Samstag", "Sonntag"]

# (substring in the lowercased name, kind label) — order matters:
# "beweglicher ferientag" must win over the base kind.
KIND_PATTERNS = [
    ("beweglich", "beweglicher ferientag"),
    ("winterferien", "winterferien"),
    ("frühjahrsferien", "frühjahrsferien"),
    ("osterferien", "osterferien"),
    ("pfingstferien", "pfingstferien"),
    ("sommerferien", "sommerferien"),
    ("herbstferien", "herbstferien"),
    ("weihnachtsferien", "weihnachtsferien"),
]


def validate_year(year, default: int | None = None) -> int:
    """A year the API serves (2000..2100); default = current year."""
    if year is None:
        if default is None:
            default = date.today().year
        year = default
    try:
        y = int(year)
    except (TypeError, ValueError):
        raise ValueError(f"year must be a number, got {year!r}") from None
    if not YEAR_MIN <= y <= YEAR_MAX:
        raise ValueError(
            f"year out of range: {year} (expected {YEAR_MIN}..{YEAR_MAX})"
        )
    return y


def validate_state(state: str | None) -> str:
    """A 2-letter state code (case-insensitive). No NATIONAL — school
    holidays are per-state only, so a state is required."""
    if state is None:
        raise ValueError(
            "state is required (one of: " + ", ".join(STATE_CODES) + "); "
            "school holidays are per-state, there is no nationwide list"
        )
    code = state.strip().upper()
    if code not in STATES:
        raise ValueError(
            f"unknown state {state!r} (expected one of: "
            + ", ".join(STATE_CODES) + ")"
        )
    return code


def validate_date(value: str) -> date:
    """A YYYY-MM-DD date."""
    text = (value or "").strip()
    if not DATE_RE.fullmatch(text):
        raise ValueError(
            f"bad date {value!r} (expected YYYY-MM-DD, e.g. 2026-08-03)"
        )
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"bad date {value!r} (not a real calendar date)") from None


def validate_month(month) -> int | None:
    """A month 1..12, or None (no month filter)."""
    if month is None:
        return None
    try:
        m = int(month)
    except (TypeError, ValueError):
        raise ValueError(f"month must be a number, got {month!r}") from None
    if not 1 <= m <= 12:
        raise ValueError(f"month out of range: {month} (expected 1..12)")
    return m


def holidays_url(year: int, state: str) -> str:
    """API URL for one year + state."""
    return (f"{BASE}/holidays/"
            f"{quote_plus(validate_state(state))}/{validate_year(year)}")


def derive_kind(name: str) -> str | None:
    """Holiday kind from the German name, e.g. 'sommerferien'."""
    lowered = (name or "").lower()
    for needle, kind in KIND_PATTERNS:
        if needle in lowered:
            return kind
    return None


def _holiday_row(entry: dict) -> dict:
    start = entry.get("start")
    end = entry.get("end")
    if not isinstance(start, str) or not isinstance(end, str):
        raise ValueError(f"unexpected holiday entry: {entry!r}")
    try:
        d_start = date.fromisoformat(start)
        d_end = date.fromisoformat(end)
    except ValueError:
        raise ValueError(f"bad holiday dates in {entry!r}") from None
    if d_end < d_start:
        raise ValueError(f"holiday ends before it starts: {entry!r}")
    name = entry.get("name") or ""
    return {
        "name": name,
        "kind": derive_kind(name),
        "slug": entry.get("slug"),
        "state": entry.get("stateCode"),
        "year": entry.get("year"),
        "start": start,
        "end": end,
        "duration_days": (d_end - d_start).days + 1,
        "start_weekday": WEEKDAYS_EN[d_start.weekday()],
        "start_weekday_de": WEEKDAYS_DE[d_start.weekday()],
        "end_weekday": WEEKDAYS_EN[d_end.weekday()],
        "end_weekday_de": WEEKDAYS_DE[d_end.weekday()],
    }


def parse_holidays(text: str) -> list:
    """API JSON list -> sorted list of holiday rows.

    An empty list is valid: the API returns [] (HTTP 200) for a
    state/year it has no data for. Raises ValueError on bad shapes.
    """
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid holidays response: {e}") from e
    if not isinstance(payload, list):
        raise ValueError("unexpected holidays shape: not a JSON list")
    rows = [_holiday_row(entry) for entry in payload]
    rows.sort(key=lambda r: (r["start"], r["name"]))
    return rows


def list_states() -> list:
    """All 16 state codes with their German names (static data)."""
    return [{"code": code, "name": STATES[code]} for code in STATE_CODES]


def holidays_in_month(rows: list, month: int | None) -> list:
    """Holiday rows overlapping one month (None = no filter). A row
    overlaps the month when any of its days fall in it."""
    if month is None:
        return rows
    return [r for r in rows
            if int(r["start"][5:7]) == month or int(r["end"][5:7]) == month]


def is_holiday(rows: list, day: date) -> list:
    """Holiday rows covering one date (start <= day <= end)."""
    target = day.isoformat()
    return [r for r in rows if r["start"] <= target <= r["end"]]


def next_holiday(rows: list, start: date) -> dict | None:
    """First holiday period on or after `start` — the ongoing one if
    `start` falls inside a holiday — or None. The row carries an
    "ongoing" flag (True when start is inside the period)."""
    dated = sorted(rows, key=lambda r: r["start"])
    for row in dated:
        if row["end"] >= start.isoformat():
            return {**row, "ongoing": row["start"] <= start.isoformat()}
    return None


def holidays_between(rows_by_year: dict[int, list], start: date,
                     end: date) -> list:
    """Merge per-year holiday rows into one sorted list overlapping
    [start, end]. A row overlaps when start <= row.end and
    row.start <= end — so cross-year holidays (e.g. Weihnachtsferien
    running into January) are included."""
    if end < start:
        raise ValueError(
            f"end date {end} is before start date {start}"
        )
    if (end - start).days > MAX_RANGE_DAYS:
        raise ValueError(
            f"date range too wide: {(end - start).days} days "
            f"(max {MAX_RANGE_DAYS})"
        )
    out = []
    for rows in rows_by_year.values():
        for row in rows:
            if row["start"] <= end.isoformat() and \
                    row["end"] >= start.isoformat():
                out.append(row)
    out.sort(key=lambda r: r["start"])
    return out
