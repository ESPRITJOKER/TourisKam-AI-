# TOURISCAM AI STATUS

_Last updated: 2026-09-12 (Day 3 — WhatsApp workflow built in n8n ✅)_

## Current Phase
**Day 3 IN PROGRESS — WhatsApp round-trip built (text), pending live credentials.**
The full text pipeline is built and validated as an n8n workflow (`TourisCam
WhatsApp`, id `LACeG3RxqrtB7Jwn`). It runs the same guardrailed RAG as Day 2
(embed → match_documents → gemini-flash-latest, thinking_budget=0) and logs
anonymous analytics. Live phone test is gated on the user adding 3 credentials +
wiring the Twilio Sandbox webhook. Voice notes are Phase 2.

_Day 2 COMPLETE — RAG working end-to-end._ 118 chunks embedded in Supabase;
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

## Dataset — synthetic query logs (user-provided, 2026-09-15)
- `dataset/whatsapp_visitor_query_logs.csv` — 6,200 **simulated** WhatsApp
  interactions (2026-06-01 → 2026-09-08) for the Day 5 dashboard demo. Checked:
  no duplicate ids, consistent SOS flags/site→region mapping.
- Loaded into new `demo_query_logs` table (`db/demo_query_logs.sql`) via
  `rag/load_query_logs.py` (truncate + reload). NOT in `knowledge_documents`
  (not RAG knowledge) and NOT in `query_events` (keeps real traffic clean).
- Site names reference `amenities_directory.csv`, which isn't in the repo; treat
  them as free-text labels. Drop the table once real usage data exists.

## Completed (Day 3 — WhatsApp workflow)
- ✅ n8n Cloud connected via n8n MCP (`thementalist.app.n8n.cloud`).
- ✅ Built & validated the `TourisCam WhatsApp` workflow (19 nodes, id
  `LACeG3RxqrtB7Jwn`) — text round-trip: Twilio webhook (instant ACK) → normalize
  → Gemini embed (768) → Supabase `match_documents(embedding,5,0.5)` → format
  context w/ trust labels → Gemini generate (`thinking_budget=0`, SYSTEM_PROMPT) →
  **async** Twilio reply → SHA256 session hash → log `tourist_queries` +
  `query_events`. Graceful fallback + `response_status='error'` on any
  embed/retrieve/generate failure; retry on Gemini 503.
- ✅ Decision: HTTP Request nodes for Gemini (reuse validated request shapes +
  `thinking_budget` control), native Postgres node for retrieval/logging — not the
  LangChain Gemini/AI-Agent nodes.
- ✅ Deliverables in `n8n/`: `touriscam_whatsapp.workflow.json` (importable
  backup), `SYSTEM_PROMPT.txt` (synced with `rag/prompt.py`), `README.md` (setup +
  test script).

## Demo Readiness
- **~55%.** RAG core + WhatsApp orchestration built. Needs live credential wiring
  for the phone test; then Phase 2 voice, specialized tools (Day 4), dashboard (Day 5).

## Completed (Day 3 — go-live wiring, 2026-09-13)
- ✅ 3 n8n credentials created (Header Auth `x-goog-api-key`, Postgres pooler,
  Twilio API-key) and attached to all 8 nodes via MCP.
- ✅ Workflow **published/active** (activeVersionId `74a6f175…`, triggerCount 1).
  Production webhook `https://thementalist.app.n8n.cloud/webhook/touriscam-whatsapp`.

## Blocked (user actions — final gate for the live phone test)
- **Set the Twilio WhatsApp Sandbox "when a message comes in"** to the webhook
  above (POST), then **join** the sandbox from the test phone.
- (Recommended) set n8n env var `SESSION_HASH_SALT`.
- **SECURITY: rotate Supabase DB password, Gemini key, Twilio API key/secret, AND
  the n8n API key after the competition** — several were pasted in chat.

## Next Tasks
- Live WhatsApp test (4 cases in `n8n/README.md`) once credentials are added.
- **Phase 2:** voice-note branch (Twilio media fetch → Gemini audio transcription).
- Day 4: specialized tool tables from the dataset CSVs; Day 5: dashboard.

## Known Bugs
- None yet.

## Technical Debt
- Seed tariffs/guides/emergency rows are **placeholders marked `unverified`** and MUST be replaced with real surveyed/official data before the demo.
- RLS policies not yet defined (`db/policies.sql` planned) — anon key must not be exposed publicly until then.

## Deployment Status
- n8n workflow deployed to n8n Cloud (inactive until credentials + Sandbox webhook
  are wired, then Activate). Dashboard hosting TBD (Streamlit local/Community Cloud).

## Priority guardrail
Protect P0: Twilio WhatsApp · n8n · AI response · Tourism RAG · Tariff tool · Supabase · Analytics · Basic dashboard.
