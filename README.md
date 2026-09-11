# TourisCam AI 🇨🇲

**An autonomous multilingual tourism concierge for Cameroon, operating through WhatsApp.**

TourisCam AI helps tourists discover destinations, check verified/benchmark
prices, find certified guides, and get emergency information — in **French,
English, and Cameroon Pidgin**, by text or voice note. At the institutional
level, it gives MINTOUL anonymous tourism intelligence (popular destinations,
visitor interests, language distribution, demand trends).

> Competition MVP. Internal hard-freeze: **17 September 2026**.

## What makes it different

Not "ChatGPT on WhatsApp." The value is:
**WhatsApp + Cameroon tourism knowledge + verified information + specialized
tourism tools + multilingual interaction + institutional tourism intelligence.**

## Architecture

```
Tourist → WhatsApp → Twilio → n8n webhook → normalize → (voice→transcribe)
       → intent + AI reasoning → tool selection → RAG / DB / tool
       → response → log → Twilio → WhatsApp
                              │
                              └→ Supabase → MINTOUL analytics dashboard
```

| Layer | Choice |
|---|---|
| Messaging | Twilio WhatsApp (Sandbox for demo) |
| Orchestration | n8n Cloud |
| Database + vectors | Supabase Postgres + pgvector |
| LLM + embeddings + audio | Google Gemini (`gemini-2.0-flash`, `text-embedding-004`) |
| Dashboard | Streamlit |
| VCS | Git / GitHub |

## Agent tools

1. **Tourism Knowledge Search** — RAG over the verified knowledge base.
2. **Tariff Guard** — verified/benchmark pricing; never invents a price.
3. **Guide Directory** — certified tourism guides.
4. **Emergency Information** — verified local emergency contacts.

## Repository layout

```
db/          SQL schema, seed data, RPC functions
knowledge/   RAG source documents (see knowledge/README.md for the trust policy)
rag/         ingestion + retrieval scripts (Day 2)
n8n/         exported n8n workflows (Day 3+)
dashboard/   Streamlit MINTOUL dashboard (Day 5)
docs/        architecture, diagrams, competition dossier
scripts/     utilities
```

## Setup

1. Copy `.env.example` → `.env` and fill in credentials.
   Get a free Gemini key at https://aistudio.google.com/app/apikey
2. In the Supabase SQL editor, run `db/schema.sql`, then `db/seed.sql`.
3. (Day 2+) Run RAG ingestion to populate embeddings.
4. (Day 3+) Import the n8n workflow and connect the Twilio WhatsApp Sandbox.

## Security

Secrets live only in `.env` (git-ignored). The Supabase **service role key** is
used only by n8n/scripts and is **never** exposed to any frontend. See
`.env.example` for the full list.

## Status

See [`PROJECT_STATUS.md`](./PROJECT_STATUS.md).

## License

Apache-2.0 — see [`LICENSE`](./LICENSE).
