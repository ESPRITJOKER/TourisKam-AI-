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

## Completed (validation)
- ✅ Python 3.13 installed; `rag/.venv` created; deps installed.
- ✅ Ingestion dry-run passed (5 docs, chunking OK).
- ✅ Reworked scripts to connect via **direct Postgres (psycopg2)** through the
  Supabase **Session pooler** (IPv4) — direct `db.*` host is IPv6-only.
- ✅ `db/schema.sql` + `db/seed.sql` applied to Supabase (verified: 9 tables,
  pgvector + pgcrypto extensions, `match_documents` RPC, seed rows present).

## Dataset (user-provided, 2026-09-11)
- `dataset/touriscam_dataset_final/` — curated MINTOUL/UNESCO/OSM-sourced package
  with `RAG_POLICY.md` (guardrails), CSVs (attractions, hotels, guides, heritage,
  events, practical info, sources), and consolidated RAG JSONL (113 records:
  hotel 32, heritage 20, event 16, practical 17, attraction 14, guide 14).
- `rag/ingest_dataset.py` merges both JSONL files + enriches with `sources.csv`
  (URL/authority) → `knowledge_documents`. Dry-run validated (113 records, all
  with source_url). No schema change needed.
- Note: dataset CSVs → relational tables (hotels/guides/etc. for the specialized
  tools) is a **Day 4** task; will replace the placeholder seed rows then.

## In Progress
- Live ingest (embeddings) of dataset + destination docs — blocked ONLY on Gemini key.

## Blocked (user actions)
- **Gemini API key** — https://aistudio.google.com/app/apikey → paste into `.env` `GEMINI_API_KEY`.
- **n8n Cloud instance** — create (needed Day 3).
- **Rotate Supabase DB password after competition** — it was pasted in chat.

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
