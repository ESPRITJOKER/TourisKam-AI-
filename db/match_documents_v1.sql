-- Rollback: match_documents exactly as it was live before v2 (dumped 2026-09-15).
-- Apply: python scripts/apply_sql.py db/match_documents_v1.sql

CREATE OR REPLACE FUNCTION public.match_documents(query_embedding vector, match_count integer DEFAULT 5, similarity_threshold double precision DEFAULT 0.5)
 RETURNS TABLE(id uuid, title text, content text, source text, source_type text, verification_status verification_status, similarity double precision)
 LANGUAGE sql
 STABLE
AS $function$
  select
    kd.id,
    kd.title,
    kd.content,
    kd.source,
    kd.source_type,
    kd.verification_status,
    1 - (kd.embedding <=> query_embedding) as similarity
  from knowledge_documents kd
  where kd.embedding is not null
    and 1 - (kd.embedding <=> query_embedding) >= similarity_threshold
  order by kd.embedding <=> query_embedding
  limit match_count;
$function$;
