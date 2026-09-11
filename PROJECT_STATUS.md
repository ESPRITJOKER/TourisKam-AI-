# TOURISCAM AI STATUS

_Last updated: 2026-09-11 (Day 2 — RAG scripts written)_

## Current Phase
**Day 2 — RAG.** Ingestion, retrieval, and guardrailed prompt written (pending live validation once Python + Supabase creds are in place).

## Completed
- ✅ Git repo initialized locally and connected to `ESPRITJOKER/TourisKam-AI-` (Apache LICENSE preserved).
- ✅ Project folder structure (`db`, `knowledge/*`, `rag`, `n8n`, `dashboard`, `docs`, `scripts`).
- ✅ `.gitignore` (secrets protected) and `.env.example` (all credentials templated).
- ✅ `db/schema.sql` — all core tables (destinations, attractions, tariffs, guides, hotels, emergency_contacts, knowledge_documents+pgvector, tourist_queries, query_events), UUIDs, FKs, indexes, constraints, `updated_at` triggers, `match_documents` RPC.
- ✅ `db/seed.sql` — real, honestly-labeled data for Douala, Yaoundé, Limbe, Kribi, West Region.
- ✅ `knowledge/README.md` — verification/trust policy; example doc `knowledge/destinations/limbe.md`.
- ✅ `README.md`, `docs/architecture.md`, this tracker.

## Completed (Day 2)
- ✅ `rag/` pipeline written: `config.py`, `embed.py`, `ingest.py`, `retrieve.py`, `prompt.py`, `requirements.txt`, `README.md`.
- ✅ Guardrailed multilingual system prompt (single source of truth; will be copied into n8n Day 3).
- ✅ Knowledge docs for Douala, Yaoundé, Limbe, Kribi, Foumban.
- ✅ `db/reindex.sql`; removed embedding-less `knowledge_documents` rows from seed (ingestion now owns that table).

## In Progress
- Live validation of RAG scripts — blocked on Python install + Supabase creds + Gemini key.

## Blocked (all user actions — I can't access these consoles)
- **Install Python 3.11+** — `winget install -e --id Python.Python.3.12` (needed for RAG + Streamlit).
- **Gemini API key** — https://aistudio.google.com/app/apikey → put in `.env`.
- **Supabase**: run `db/schema.sql` then `db/seed.sql`; put URL + service role key in `.env`.
- **n8n Cloud instance** — create (needed Day 3).

## Next Tasks
- Once Python is in: `python rag/ingest.py --dry-run` (validate chunking, no creds needed), then a live ingest + `retrieve.py --answer` smoke test.
- Day 3 — WhatsApp: n8n webhook, Twilio in/out, voice pipeline (Gemini audio), copy guardrailed prompt into n8n.

## Known Bugs
- None yet.

## Technical Debt
- Seed tariffs/guides/emergency rows are **placeholders marked `unverified`** and MUST be replaced with real surveyed/official data before the demo.
- RLS policies not yet defined (`db/policies.sql` planned) — anon key must not be exposed publicly until then.

## Deployment Status
- Not deployed. n8n Cloud + Twilio Sandbox to be wired Day 3. Dashboard hosting TBD (Streamlit local/Community Cloud).

## Demo Readiness
- **~10%.** Foundation only. No live message round-trip yet.

## Priority guardrail
Protect P0: Twilio WhatsApp · n8n · AI response · Tourism RAG · Tariff tool · Supabase · Analytics · Basic dashboard.
