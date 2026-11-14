# ferien-mcp 🏖️

mcp-name: io.github.mohammad-abbasi-sh/ferien-mcp

Inoffizieller **Nur-Lesen**-MCP-Server für **deutsche Schulferien** über die [ferien-api.de API](https://ferien-api.de) (bundesAPI-Projekt): Ferien pro Jahr und Bundesland, Ist-es-ein-Ferientag-Prüfung, die nächsten Ferien ab einem Datum und Ferien in einem Zeitraum. Kein Schlüssel, keine Anmeldung nötig.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory". Keine Verbindung zu ferien-api.de / dem bundesAPI-Projekt.

## Für KI-Agenten

In die MCP-Client-Konfiguration eintragen (stdio):

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

Oder lokal starten: `python -m ferien_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|--------------|
| `ferien_list_holidays` | Schulferien eines Jahres in einem Bundesland (optional nach Monat gefiltert) |
| `ferien_is_holiday` | Liegt ein Datum (YYYY-MM-DD) in den Schulferien eines Bundeslandes? |
| `ferien_next_holiday` | Die nächsten Schulferien ab einem Datum (gibt die laufenden Ferien zurück, wenn das Datum in den Ferien liegt; blickt auch ins nächste Jahr) |
| `ferien_holidays_between` | Schulferien, die einen Zeitraum überschneiden (max. ca. 2 Jahre) |
| `ferien_list_states` | Alle 16 Bundesländer |
| `ferien_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`ferien_is_holiday` / 2026-08-10, BY):

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

Hinweise:
- Bundesland-Codes sind die 2-Buchstaben-Codes: BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH. Es gibt **keine bundesweite Liste** — Schulferien sind Ländersache, jede Abfrage braucht ein Bundesland. `ferien_list_states` liefert die vollständige Liste.
- Feriennamen sind deutsch („sommerferien bayern 2026"); jede Zeile trägt zusätzlich eine `kind` (winterferien, frühjahrsferien, osterferien, pfingstferien, sommerferien, herbstferien, weihnachtsferien, beweglicher ferientag) und die Dauer in Tagen.
- **Die Abdeckung variiert je nach Bundesland und Jahr**: Die API liefert eine leere Liste für ein Bundesland/Jahr, zu dem sie keine Daten hat — z. B. war Berlin 2026 am 2026-11-14 leer, während Berlin 2025 sieben Einträge hat. Wichtige Termine bitte an der offiziellen Quelle prüfen.
- Jahresübergreifende Ferien (z. B. Weihnachtsferien bis in den Januar) werden von `ferien_holidays_between` einbezogen, wenn sie den Zeitraum überschneiden.
- Jahre 2000–2100 werden akzeptiert.
- Die API setzt aggressive Ratenbegrenzungen pro IP (laut Doku: „heavily abused, aggressive rate limiting is in place"). Meldet ein Aufruf HTTP 429, ein paar Minuten warten und erneut versuchen — am 2026-11-14 war die Sperre nach ca. 10 Minuten wieder aufgehoben.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
