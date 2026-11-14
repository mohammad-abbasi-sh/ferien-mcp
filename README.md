# ferien-mcp 🏖️

mcp-name: io.github.mohammad-abbasi-sh/ferien-mcp

Unofficial **read-only** MCP server for **German school holidays** (Schulferien) via the [ferien-api.de API](https://ferien-api.de) (bundesAPI project): holidays per year and federal state, is-it-a-holiday checks, the next holiday from a date, and holidays in a date range. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with ferien-api.de / the bundesAPI project.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "ferien": {
      "command": "uvx",
      "args": ["ferien-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m ferien_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `ferien_list_holidays` | School holidays of one year in one federal state (optional month filter) |
| `ferien_is_holiday` | Is a date (YYYY-MM-DD) inside the school holidays in one state? |
| `ferien_next_holiday` | The next school holiday on or after a date (returns the ongoing one if inside a holiday; looks into the next year) |
| `ferien_holidays_between` | School holidays overlapping a date range (max ~2 years) |
| `ferien_list_states` | All 16 German federal states |
| `ferien_health` | Reachability check (ok / blocked / error) — one polite request |

Example output (`ferien_is_holiday` / 2026-08-10, BY):

```json
{"date": "2026-08-10", "weekday": "Monday", "weekday_de": "Montag",
 "state": "BY", "state_name": "Bayern", "is_holiday": true,
 "holidays": ["sommerferien bayern 2026"],
 "details": [{"name": "sommerferien bayern 2026", "kind": "sommerferien",
   "slug": "sommerferien bayern 2026-2026-BY", "state": "BY",
   "year": 2026, "start": "2026-08-03", "end": "2026-09-15",
   "duration_days": 44, "start_weekday": "Monday",
   "start_weekday_de": "Montag", "end_weekday": "Tuesday",
   "end_weekday_de": "Dienstag"}]}
```

Notes:
- State codes are the 2-letter codes: BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH. There is **no nationwide list** — school holidays are per-state, so every query needs one state. Use `ferien_list_states` for the full list.
- Holiday names are German ("sommerferien bayern 2026"); each row also carries a `kind` (winterferien, frühjahrsferien, osterferien, pfingstferien, sommerferien, herbstferien, weihnachtsferien, beweglicher ferientag) and the duration in days.
- **Coverage varies by state and year**: the API returns an empty list for a state/year it has no data for — e.g. Berlin 2026 was empty on 2026-11-14 while Berlin 2025 has 7 entries. Verify important dates against the official source.
- Cross-year holidays (e.g. Weihnachtsferien running into January) are included by `ferien_holidays_between` when they overlap the range.
- Years 2000–2100 are accepted.
- The API rate-limits aggressively per IP (its docs: "heavily abused, aggressive rate limiting is in place"). If a call reports HTTP 429, wait a few minutes and retry — on 2026-11-14 the limit cleared after ~10 minutes.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
