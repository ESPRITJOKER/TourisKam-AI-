TOURISCAM AI — FINAL DATASET PACKAGE
Date: 2026-09-11

This is the final curated dataset package for the current competition MVP/RAG build.
It is source-controlled and intentionally conservative: it does not fabricate missing
tourism facts.

Included:
- source registry
- UNESCO heritage layer
- attractions/site layer
- MINTOUL 2026 hotel layer
- historical hotel references separated from current-source hotels
- practical travel/entry/transport layer
- festival/event layer
- public MINTOUL guide directory records
- official documents inventory for deeper PDF ingestion
- consolidated RAG JSONL
- RAG policy and answer guardrails

Important:
This is NOT a live booking database. Hotel tariffs/availability, opening hours,
transport prices and entry requirements can change. TourisCam must label them
appropriately and verify current information when the workflow supports verification.

Sensitive data:
CNI/national ID numbers from MINTOUL's public guide pages were intentionally excluded.
Only professional directory information needed for tourism discovery is retained.

Next engineering step:
Claude Code should ingest this package into Supabase/Postgres + pgvector,
preserve source metadata, create embeddings, and expose retrieval to n8n.
