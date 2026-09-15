-- Rebuild the pgvector ANN index after ingesting a larger dataset.
-- Apply: python scripts/apply_sql.py db/reindex.sql
--
-- HNSW (pgvector >= 0.5; Supabase runs 0.8.2) keeps high recall with no
-- training step. The previous ivfflat index (lists = 100) was built on 118 rows
-- and is queried with the default ivfflat.probes = 1, so once the planner
-- starts using it on a larger table it would silently miss most neighbours.
drop index if exists idx_knowledge_embedding;
create index idx_knowledge_embedding
  on knowledge_documents using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

analyze knowledge_documents;
