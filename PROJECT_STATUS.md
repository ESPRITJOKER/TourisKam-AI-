# TOURISCAM AI STATUS

_Last updated: 2026-09-11 (end of Day 1)_

## Current Phase
**Day 1 — Foundation.** Repo, structure, database schema, seed data, and docs.

## Completed
- ✅ Git repo initialized locally and connected to `ESPRITJOKER/TourisKam-AI-` (Apache LICENSE preserved).
- ✅ Project folder structure (`db`, `knowledge/*`, `rag`, `n8n`, `dashboard`, `docs`, `scripts`).
- ✅ `.gitignore` (secrets protected) and `.env.example` (all credentials templated).
- ✅ `db/schema.sql` — all core tables (destinations, attractions, tariffs, guides, hotels, emergency_contacts, knowledge_documents+pgvector, tourist_queries, query_events), UUIDs, FKs, indexes, constraints, `updated_at` triggers, `match_documents` RPC.
- ✅ `db/seed.sql` — real, honestly-labeled data for Douala, Yaoundé, Limbe, Kribi, West Region.
- ✅ `knowledge/README.md` — verification/trust policy; example doc `knowledge/destinations/limbe.md`.
- ✅ `README.md`, `docs/architecture.md`, this tracker.

## In Progress
- Nothing (Day 1 wrapping up; awaiting user to run SQL in Supabase).

## Blocked
- **Gemini API key** — user to obtain from https://aistudio.google.com/app/apikey (needed Day 2).
- **Supabase SQL execution** — user must run `db/schema.sql` + `db/seed.sql` in their Supabase project (Claude cannot access the console).
- **n8n Cloud instance** — user to create (needed Day 3).

## Next Tasks (Day 2 — RAG)
- Ingestion script: read `knowledge/**`, clean, chunk, embed via Gemini, upsert to `knowledge_documents`.
- Retrieval helper using `match_documents`.
- Guardrailed system prompt (prefer retrieved verified info; refuse to hallucinate).
- Enable `vector` extension check + refresh ivfflat index post-ingest.

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
