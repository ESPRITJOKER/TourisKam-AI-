-- =====================================================================
-- match_documents v2 — authority tie-break + per-record diversity
-- Apply AFTER loading the web batch: python scripts/apply_sql.py db/match_documents_v2.sql
--
-- Same signature and return columns as db/schema.sql, so the live n8n
-- "Retrieve Documents" node keeps working unchanged.
--
-- Why: with ~1,450 rows, community Wikivoyage chunks (unverified) out-score
-- official MINTOUL/UNESCO facts by small margins, and one long section can fill
-- all top-5 slots (e.g. five "Kribi — Voir" chunks). This version:
--   1. keeps the raw-similarity threshold,
--   2. keeps at most 2 chunks per source record (source_ref),
--   3. orders by similarity + boost: +0.04 primary/verified, +0.02 secondary/benchmark.
-- Mirrors rerank() in rag/eval_retrieval.py — keep the two in sync.
-- Exact scan (no ANN index use) is fast at this corpus size (well under 50k rows).
-- =====================================================================

create or replace function match_documents(
  query_embedding vector(768),
  match_count int default 5,
  similarity_threshold float default 0.5
)
returns table (
  id uuid,
  title text,
  content text,
  source text,
  source_type text,
  verification_status verification_status,
  similarity float
)
language sql stable as $$
  with scored as (
    select
      kd.id, kd.title, kd.content, kd.source, kd.source_type, kd.verification_status,
      1 - (kd.embedding <=> query_embedding) as similarity,
      coalesce(kd.source_ref, kd.id::text) as record_ref,
      case
        when kd.metadata->>'authority_level' = 'primary' or kd.verification_status = 'verified' then 0.04
        when kd.metadata->>'authority_level' = 'secondary' or kd.verification_status = 'benchmark' then 0.02
        else 0.0
      end as boost
    from knowledge_documents kd
    where kd.embedding is not null
      and 1 - (kd.embedding <=> query_embedding) >= similarity_threshold
  ),
  per_record as (
    select *, row_number() over (partition by record_ref order by similarity desc) as rn
    from scored
  )
  select id, title, content, source, source_type, verification_status, similarity
  from per_record
  where rn <= 2
  order by similarity + boost desc
  limit match_count;
$$;
