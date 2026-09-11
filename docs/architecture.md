# TourisCam AI — Architecture

## Principle
n8n is the **single** orchestration layer. No parallel FastAPI orchestrator.
FastAPI is introduced only if a concrete need arises that n8n cannot handle.
Choose simple, reliable, demonstrable over technically impressive.

## Runtime flow (text + voice)

```
Tourist
  │  (WhatsApp text or voice note)
  ▼
Twilio WhatsApp Sandbox
  │  webhook (HTTP POST, form-encoded)
  ▼
n8n webhook node
  │
  ├─ Normalize message (sender, body, media URLs)
  ├─ If voice note: fetch audio from Twilio ──► Gemini (audio-in) ──► transcript
  ├─ Detect language (fr / en / pidgin / mixed)
  ├─ Classify intent + select tool
  │
  ├─ Tool: Tourism Search ──► Gemini embed query ──► Supabase match_documents (RAG)
  ├─ Tool: Tariff Guard    ──► Supabase tariffs (verified/benchmark, never invent)
  ├─ Tool: Guide Directory ──► Supabase guides
  ├─ Tool: Emergency Info  ──► Supabase emergency_contacts
  │
  ├─ Generate concise, guardrailed response (Gemini) in user's language
  ├─ Log conversation → tourist_queries  (hashed session id, no raw phone)
  ├─ Emit anonymous analytics → query_events
  ▼
Twilio ──► WhatsApp (reply)

           Supabase (query_events) ──► Streamlit MINTOUL dashboard
```

## Components

| Component | Responsibility |
|---|---|
| **Twilio WhatsApp Sandbox** | Inbound/outbound WhatsApp messages + media. |
| **n8n Cloud** | Orchestration: normalize → transcribe → reason → tool → respond → log. |
| **Google Gemini** | LLM reasoning, query/doc embeddings (768-d), and native audio transcription. |
| **Supabase Postgres** | Reference data, conversation log, analytics. |
| **Supabase pgvector** | Semantic retrieval via `match_documents` RPC. |
| **Streamlit** | Institutional MINTOUL analytics dashboard (reads Supabase). |

## Data model (see `db/schema.sql`)
- Reference: `destinations`, `attractions`, `tariffs`, `guides`, `hotels`, `emergency_contacts`.
- RAG: `knowledge_documents` (embedding `vector(768)`), `match_documents()` RPC.
- Conversation/analytics: `tourist_queries` (hashed session, minimal PII), `query_events` (anonymous).

Every fact-bearing row carries `source`, `verification_status`, `last_verified`.

## Guardrails
- Prefer retrieved **verified** info over model memory.
- Tariff Guard never invents a price — reports verified / benchmark / estimated / unavailable.
- No claim of dispatching emergency services (no dispatch integration exists).
- On retrieval miss: *"I couldn't verify that information."*

## Privacy
- WhatsApp numbers are hashed (with `SESSION_HASH_SALT`) into `session_id`; raw numbers are not stored.
- `query_events` is anonymous — no PII, only approximate/analytical fields.

## Error handling
Every external call (Twilio, Gemini, Supabase) has failure handling. Users get a
graceful fallback (*"I'm having trouble accessing that information right now.
Please try again shortly."*); technical errors are logged separately.

## Security
- Secrets in `.env` only (git-ignored). Service role key: n8n/scripts only, never a frontend.
- Dashboard behind a password gate; RLS to be added before exposing the anon key.
