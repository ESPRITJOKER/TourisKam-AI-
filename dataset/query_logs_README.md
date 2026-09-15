# WhatsApp Visitor Query Logs — Synthetic Dataset for Dashboard Demo

**File:** `whatsapp_visitor_query_logs.csv`
**Rows:** 6,200 simulated WhatsApp interactions over a 100-day window
**Purpose:** Feeds Track 4's Ministry Executive Cockpit (Streamlit dashboard) with realistic
volume, so you can demo live heatmaps, trending sites, and alert triggers **before** the real
bot has accumulated real usage data.

## Why this one is legitimately "big data" (unlike the tourism catalog)

The amenities/tariffs/directory data represents **real businesses and real facts** — Cameroon
has a few hundred well-documented tourist sites, not thousands, so inflating that data would
mean inventing fake hotels and fake phone numbers. This query-log dataset is different: it is
**simulated usage data** standing in for logs your WhatsApp bot will generate once live. There
is no real-world ceiling on how many synthetic interactions can be simulated, so scaling to
6,200+ rows is honest and directly useful for demoing the dashboard at a realistic scale.

## Columns

| Column | Description |
|---|---|
| `query_id` | Unique ID per message/query |
| `timestamp` | Date and time of the query (spans a 100-day simulated period) |
| `session_id` | Groups follow-up questions from the same visitor into one conversation session |
| `visitor_id` | Anonymized visitor identifier (no real personal data) |
| `channel` | `text` or `voice_note` |
| `language` | `French`, `English`, or `Pidgin` |
| `visitor_type` | `domestic` or `foreign` |
| `visitor_origin` | Cameroonian region (if domestic) or country (if foreign) |
| `query_type` | `pricing`, `opening_hours`, `directions`, `cultural_info`, `booking_interest`, `transport_fare`, `emergency_sos`, `general_chat` |
| `site_referenced` | Which catalogued site the query was about (matches names in `amenities_directory.csv`); blank for general chat |
| `region_referenced` | Region tied to the referenced site |
| `sentiment` | `positive`, `neutral`, or `negative` (simulated — negative skews higher on pricing/emergency queries, modeling real complaint patterns like overcharging) |
| `response_time_seconds` | Simulated bot response latency |
| `resolved` | Whether the query was successfully answered (True/False) |
| `is_emergency` | Flags SOS-type queries, for testing the alert/broadcast trigger logic |

## What this lets your dashboard demo show

- **National demand heatmap** — group by `region_referenced` + `timestamp` to show which regions/hubs are trending
- **Top attractions** — count by `site_referenced` (already shows realistic variety across all 38 catalogued sites)
- **Foreign vs. domestic split** — `visitor_type` distribution (currently ~37% foreign / 63% domestic)
- **Language/channel usage** — shows the bilingual + Pidgin + voice-note value proposition with real numbers
- **Complaint/sentiment tracking** — filter `sentiment == "negative"` on `pricing`/`transport_fare` queries to demo the anti-overcharging value proposition
- **Emergency SOS trigger demo** — 126 simulated emergency queries to test/demo the alert broadcast interface

## Loading into Supabase

Loaded into the **`demo_query_logs`** table (DDL: `db/demo_query_logs.sql`) by
`rag/load_query_logs.py` — kept separate from the real `query_events` table and
never embedded into the RAG knowledge base. `language` is normalized to
`fr|en|pidgin`; timestamps are stored as Africa/Douala time (UTC+1).
Site names are free-text labels: the `amenities_directory.csv` referenced above is
not in this repo, and most names differ from `touriscam_dataset_final`.

## Note

Replace this with real logged data once the bot is live — this dataset exists purely to make
the dashboard demo-ready and visually convincing for the competition presentation, not as a
claim of real usage.
