# MINTOUL dashboard (Streamlit)

Anonymous tourism-demand signals from the WhatsApp bot, for the ministry view of
the demo.

```bash
rag/.venv/Scripts/python.exe -m pip install -r dashboard/requirements.txt
rag/.venv/Scripts/python.exe -m streamlit run dashboard/app.py      # http://localhost:8501
```

## Tabs

| Tab | Source | Notes |
|---|---|---|
| **Demo (simulated)** | `demo_query_logs` (6,200 rows) | Synthetic interactions, 1 Jun – 8 Sep 2026. Banner says so on every view — never present it as real usage. |
| **Live bot** | `query_events` | One anonymized row per real WhatsApp message (no phone numbers; hashed session ids). Empty until the Twilio Sandbox is wired. |

Views: KPI tiles (queries, foreign share, resolved, average response, voice-note
share, SOS count) · demand heatmap by region × week · most asked-about sites ·
sentiment by query type (diverging, the overcharging signal) · language split ·
latest SOS queries. Filters (date range, region, visitor type) sit in one row and
scope every chart; each chart has a table view.

## Configuration

Reads the project `.env` through `rag/config.py` (direct Postgres, Session pooler):
`SUPABASE_DB_HOST/PORT/NAME/USER/PASSWORD`. Optional `DASHBOARD_PASSWORD` gates
access — until it is set, the app shows a warning and stays open, so set it before
sharing the URL or deploying.

## Design notes

Charts follow the `dataviz` skill: one-hue blue sequential ramp for the heatmap,
a single colour for bars (length already encodes magnitude), blue↔red diverging
with a neutral grey for sentiment, three validated categorical slots for
languages (with direct labels, because light-mode aqua sits below 3:1 contrast),
legends plus selective direct labels, hairline grids, 2px surface gaps and a
table view under every chart. The palette is theme-aware (light/dark) and was
checked with the skill's validator in both modes.

## Hosting

Local-only for the demo: it connects with the database password, which must not
ship to a public host. For Streamlit Community Cloud, switch to the Supabase anon
key with RLS policies (`db/policies.sql`, not yet written) and put the password in
the platform's secrets store.
