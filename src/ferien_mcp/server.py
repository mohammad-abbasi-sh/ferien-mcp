"""MCP server: unofficial read-only access to German school holidays
(Schulferien) via the ferien-api.de API (bundesAPI project) — holidays
per year and federal state, is-it-a-holiday checks, the next holiday
from a date, holidays in a date range and the list of states. No key,
no login.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for German school holidays
(Schulferien) — the ferien-api.de API (bundesAPI project): holidays
per year and federal state (Bundesland), is-it-a-holiday checks, the
next holiday from a date, and holidays in a date range. No key, no
login. State codes are the 2-letter codes (BW, BY, BE, BB, HB, HH,
HE, MV, NI, NW, RP, SL, SN, ST, SH, TH) — there is no nationwide
list, school holidays are per-state. Holiday names are German
("sommerferien bayern 2026"); each row also carries a "kind"
(sommerferien, osterferien, ...) and the duration in days. Note the
API's coverage varies by state and year: a state/year it has no data
for returns an empty list (e.g. Berlin 2026 was empty on 2026-11-14)
— verify important dates against the official source. The API also
rate-limits aggressively per IP; if a call reports HTTP 429, retry
a few minutes later.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — \
Germany MCP factory.
"""

_SOURCE = "ferien-api.de (bundesAPI project)"
_DISCLAIMER = ("Unofficial read-only data from ferien-api.de; coverage "
               "varies by state/year — verify on ferien-api.de or the "
               "official source before acting on it.")


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


def _fetch_year(year: int, state: str) -> list:
    """Holiday rows for one year + state (live fetch + parse)."""
    return _dom.parse_holidays(
        _http.fetch_text(_dom.holidays_url(year, state)))


mcp = FastMCP("ferien-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
def ferien_list_holidays(year: int | None = None,
                         state: str | None = None,
                         month: int | None = None) -> str:
    """List the school holidays of one year in one German federal state.
    year: e.g. 2026 (default: current year). state: 2-letter code
    (BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH)
    — required, there is no nationwide list. month: 1..12 to filter
    to holidays overlapping one month (default: whole year). An empty
    list means the API has no data for that state/year."""
    try:
        y = _dom.validate_year(year)
        code = _dom.validate_state(state)
        m = _dom.validate_month(month)
        rows = _dom.holidays_in_month(_fetch_year(y, code), m)
    except (_http.FerienMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": y, "state": code, "state_name": _dom.STATES[code],
                "month": m, "count": len(rows), "holidays": rows,
                "coverage_note":
                    "empty list = the API has no data for this state/year"
                    if not rows else None})


@mcp.tool()
def ferien_is_holiday(day: str, state: str | None = None) -> str:
    """Is a date inside the school holidays in one German federal state?
    day: YYYY-MM-DD, e.g. 2026-08-03. state: 2-letter code (required).
    Returns is_holiday plus the holiday period(s) covering the date."""
    try:
        d = _dom.validate_date(day)
        code = _dom.validate_state(state)
        rows = _dom.is_holiday(_fetch_year(d.year, code), d)
    except (_http.FerienMcpError, ValueError) as e:
        return _err(e)
    return _ok({"date": d.isoformat(), "weekday": _dom.WEEKDAYS_EN[d.weekday()],
                "weekday_de": _dom.WEEKDAYS_DE[d.weekday()],
                "state": code, "state_name": _dom.STATES[code],
                "is_holiday": bool(rows),
                "holidays": [r["name"] for r in rows],
                "details": rows})


@mcp.tool()
def ferien_next_holiday(from_date: str | None = None,
                        state: str | None = None) -> str:
    """The next school holiday on or after a date in one German state.
    from_date: YYYY-MM-DD (default: today). state: 2-letter code
    (required). If the date falls inside a holiday, that ongoing
    holiday is returned (ongoing: true). Looks into the next year if
    the current year has no holiday left."""
    try:
        start = (_dom.validate_date(from_date) if from_date
                 else date.today())
        code = _dom.validate_state(state)
        row = _dom.next_holiday(_fetch_year(start.year, code), start)
        year = start.year
        if row is None:
            year = start.year + 1
            row = _dom.next_holiday(_fetch_year(year, code), start)
    except (_http.FerienMcpError, ValueError) as e:
        return _err(e)
    if row is None:
        return _ok({"from_date": start.isoformat(), "state": code,
                    "state_name": _dom.STATES[code],
                    "next_holiday": None})
    return _ok({"from_date": start.isoformat(), "state": code,
                "state_name": _dom.STATES[code], "year": year,
                "next_holiday": row})


@mcp.tool()
def ferien_holidays_between(start_date: str, end_date: str,
                            state: str | None = None) -> str:
    """School holidays overlapping a date range in one German state.
    start_date / end_date: YYYY-MM-DD (max range ~2 years).
    state: 2-letter code (required). Cross-year holidays (e.g.
    Weihnachtsferien running into January) are included when they
    overlap the range."""
    try:
        start = _dom.validate_date(start_date)
        end = _dom.validate_date(end_date)
        code = _dom.validate_state(state)
        rows_by_year = {
            y: _fetch_year(y, code)
            for y in range(start.year, end.year + 1)
        }
        rows = _dom.holidays_between(rows_by_year, start, end)
    except (_http.FerienMcpError, ValueError) as e:
        return _err(e)
    return _ok({"start_date": start.isoformat(),
                "end_date": end.isoformat(), "state": code,
                "state_name": _dom.STATES[code], "count": len(rows),
                "holidays": rows})


@mcp.tool()
def ferien_list_states() -> str:
    """All 16 German federal states (Bundesländer) — the state codes
    the other tools accept. There is no nationwide school-holiday
    list; every query needs one state."""
    return _ok({"count": len(_dom.STATES),
                "states": _dom.list_states()})


@mcp.tool()
def ferien_health() -> str:
    """Check whether the ferien-api.de API is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
