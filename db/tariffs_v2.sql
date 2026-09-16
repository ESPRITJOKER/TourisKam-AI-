-- =====================================================================
-- Tariff Guard v2 — searchable tariff rows for the n8n pricing lookup.
-- Apply: python scripts/apply_sql.py db/tariffs_v2.sql  (idempotent)
-- Rows are loaded by rag/load_tariffs.py.
-- =====================================================================

-- Lowercase, accent-stripped keywords (incl. FR/EN synonyms such as
-- "airport aeroport", "entry entree ticket") matched with LIKE by the
-- "Build Retrieval Query" node. The table is small (tens of rows), so a
-- sequential scan is fine and no trigram extension is needed.
alter table tariffs add column if not exists search_text text;

-- Stable id of the dataset row a tariff came from (PR-00x = MINTOUL practical
-- info, STG-0xx = staging dossier) so reloads replace rather than duplicate.
alter table tariffs add column if not exists source_ref text;
create unique index if not exists idx_tariffs_source_ref
  on tariffs(source_ref) where source_ref is not null;
