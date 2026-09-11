-- Refresh the pgvector ANN index after ingesting a larger dataset.
-- For a small demo corpus this is optional (exact scan is fast and accurate).
-- Run in the Supabase SQL editor after `python rag/ingest.py`.

-- Rebuild ivfflat with a lists value ~ sqrt(rows). Adjust as the corpus grows.
drop index if exists idx_knowledge_embedding;
create index idx_knowledge_embedding
  on knowledge_documents using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

analyze knowledge_documents;
