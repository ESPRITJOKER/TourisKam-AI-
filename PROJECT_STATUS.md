# TOURISCAM AI STATUS

_Last updated: 2026-09-11 (Day 2 — RAG live & validated ✅)_

## Current Phase
**Day 2 COMPLETE — RAG working end-to-end.** 118 chunks embedded in Supabase;
semantic retrieval + guardrailed multilingual answers validated (EN/FR/miss-case).

## Working models (this Gemini key)
- Embedding: `gemini-embedding-001` (truncated to 768 dims via output_dimensionality).
- Generation: `gemini-flash-latest` — a THINKING model, so `thinking_budget=0` is
  set (otherwise it spends the whole token budget on hidden thoughts → empty text).
- NOT available on this key: `gemini-2.0-flash`, `gemini-2.5-flash`, `text-embedding-004`.

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

## Demo Readiness
- **~35%.** RAG core is demo-ready (retrieval + multilingual guardrailed answers).
  Still needed: WhatsApp round-trip (Day 3), specialized tools (Day 4), dashboard (Day 5).

## Blocked (user actions)
- **n8n Cloud instance** — create (needed Day 3).
- **Twilio WhatsApp Sandbox** — enable (needed Day 3).
- **SECURITY: rotate Supabase DB password AND regenerate the Gemini key after the
  competition** — both were pasted into chat and are in the transcript.

## Next Tasks (Day 3 — WhatsApp)
- n8n Cloud webhook; Twilio inbound/outbound; port the guardrailed RAG (embed →
  match_documents → gemini-flash-latest with thinking_budget=0) into n8n.
- Voice-note pipeline (Gemini native audio).
- Log to tourist_queries (hashed session) + emit query_events.

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
