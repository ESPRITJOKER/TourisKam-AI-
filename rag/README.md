# RAG pipeline

Ingests `knowledge/**.md` into Supabase `knowledge_documents` (with Gemini
embeddings) and retrieves verified context for the agent.

```
knowledge/*.md → clean → chunk → embed (Gemini text-embedding-004)
              → knowledge_documents (pgvector) → match_documents() → LLM
```

## Setup

```bash
cd rag
python -m venv .venv && . .venv/Scripts/activate   # Windows Git Bash
#   or: source .venv/bin/activate                   # macOS/Linux
pip install -r requirements.txt
```

Ensure the project-root `.env` has `GEMINI_API_KEY`, `SUPABASE_URL`, and
`SUPABASE_SERVICE_ROLE_KEY`, and that `db/schema.sql` has been run in Supabase.

## Ingest

```bash
python ingest.py --dry-run     # preview chunking, no API/DB calls
python ingest.py               # embed + upsert all knowledge/*.md
python ingest.py --file ../knowledge/destinations/kribi.md   # one file
```

Ingestion is idempotent: re-running replaces prior chunks for each source file.

## Retrieve / test

```bash
python retrieve.py "what can I see in Limbe?"
python retrieve.py --answer "que voir a Kribi ?"     # full guardrailed answer
python retrieve.py -t 0.3 "black sand beach"          # lower threshold
```

## Web corpus (batch `web_2026-09-15`)

Scrapes cited, source-labeled content into reviewable files, then embeds, evaluates
and loads it. Details, licenses and filters: `dataset/web_scrape_2026-09-15/README.md`.

```bash
python scrapers/run_all.py [--only fcdo wikivoyage] [--limit 3]  # -> dataset/web_scrape_2026-09-15/*.jsonl + REPORT.md
python embed_web.py [--dry-run]       # chunk + batch-embed once (cached, gitignored; uses GEMINI_INGEST_API_KEY)
python embed_web.py --only osm --batch-size 20 --pause 35   # token-dense text: stay under per-minute limits
python eval_retrieval.py              # before/after retrieval on fixed EN/FR questions -> EVAL.md (read-only)
python ingest_web.py [--dry-run]      # load into knowledge_documents (after review)
python ../scripts/apply_sql.py db/reindex.sql   # rebuild the HNSW index after loading
```

Sources: MINTOUL (primary), UK FCDO travel advice (primary), OpenStreetMap
(secondary), Wikivoyage EN/FR (third-party, `unverified`), Kribi→West staging CSV.
Rollback: `delete from knowledge_documents where metadata->>'batch' = 'web_2026-09-15';`

## Demo query logs (dashboard, not RAG)

```bash
python load_query_logs.py --dry-run   # validate + profile the CSV
python load_query_logs.py             # create demo_query_logs, truncate + reload
```

Loads the **synthetic** `dataset/whatsapp_visitor_query_logs.csv` into
`demo_query_logs` (DDL in `db/demo_query_logs.sql`) for the MINTOUL dashboard
demo. No embeddings; kept out of `knowledge_documents` and `query_events`.

## Files
- `config.py` — env + Gemini/Supabase clients.
- `embed.py` — Gemini embedding wrapper (768-d, retries).
- `ingest.py` — read/clean/chunk/embed/upsert.
- `retrieve.py` — query embed + `match_documents` RPC + context formatting.
- `load_query_logs.py` — synthetic query-log CSV → `demo_query_logs` (dashboard demo).
- `prompt.py` — **guardrailed system prompt** (single source of truth; copied
  into the n8n LLM node in Day 3) + `answer_query()`.

## Guardrails
Prefer retrieved verified info; never invent prices/contacts/sources; no
emergency-dispatch claims; reply in the user's language; on retrieval miss say
"I couldn't verify that information."
