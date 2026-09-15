-- =====================================================================
-- TourisCam AI — Supabase / PostgreSQL schema
-- Run this in the Supabase SQL editor (or via psql with SUPABASE_DB_URL).
-- Idempotent-ish: safe to re-run during development.
-- =====================================================================

-- ---------- Extensions ----------
create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "vector";      -- pgvector for embeddings

-- ---------- Shared enums / helpers ----------
-- Verification status is the trust label surfaced to tourists.
do $$ begin
  create type verification_status as enum
    ('verified', 'benchmark', 'estimated', 'unverified', 'unavailable');
exception when duplicate_object then null; end $$;

do $$ begin
  create type tariff_category as enum
    ('transport', 'accommodation', 'attraction', 'service', 'food', 'other');
exception when duplicate_object then null; end $$;

do $$ begin
  create type emergency_category as enum
    ('medical', 'police', 'fire', 'tourist_assistance', 'embassy', 'other');
exception when duplicate_object then null; end $$;

-- Auto-update updated_at on row change.
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- =====================================================================
-- CORE REFERENCE DATA
-- =====================================================================

-- ---------- destinations ----------
create table if not exists destinations (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  slug                text not null unique,
  region              text not null,
  city                text,
  description         text,
  latitude            double precision,
  longitude           double precision,
  tags                text[] default '{}',
  source              text,
  verification_status verification_status not null default 'unverified',
  last_verified       date,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index if not exists idx_destinations_region on destinations(region);
create index if not exists idx_destinations_city on destinations(city);
drop trigger if exists trg_destinations_updated on destinations;
create trigger trg_destinations_updated before update on destinations
  for each row execute function set_updated_at();

-- ---------- attractions ----------
create table if not exists attractions (
  id                  uuid primary key default gen_random_uuid(),
  destination_id      uuid references destinations(id) on delete set null,
  name                text not null,
  category            text,                      -- e.g. beach, museum, waterfall, market
  description         text,
  opening_hours       jsonb,                     -- {"mon":"08:00-17:00", ...}
  entry_fee_min       numeric(12,2),
  entry_fee_max       numeric(12,2),
  currency            text not null default 'XAF',
  address             text,
  latitude            double precision,
  longitude           double precision,
  source              text,
  verification_status verification_status not null default 'unverified',
  last_verified       date,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index if not exists idx_attractions_destination on attractions(destination_id);
create index if not exists idx_attractions_category on attractions(category);
drop trigger if exists trg_attractions_updated on attractions;
create trigger trg_attractions_updated before update on attractions
  for each row execute function set_updated_at();

-- ---------- tariffs (Tariff Guard) ----------
create table if not exists tariffs (
  id                  uuid primary key default gen_random_uuid(),
  category            tariff_category not null,
  origin              text,                       -- e.g. "Douala Airport"
  destination         text,                       -- e.g. "Bonanjo"
  transport_type      text,                       -- taxi, moto, bus, VTC, shuttle...
  description         text,
  min_price           numeric(12,2),
  max_price           numeric(12,2),
  currency            text not null default 'XAF',
  unit                text,                       -- per trip, per km, per night, per person
  time_of_day         text not null default 'any' check (time_of_day in ('day','night','any')),
  source              text,
  verification_status verification_status not null default 'benchmark',
  last_verified       date,
  notes               text,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  -- prices must be coherent when both present
  constraint chk_tariff_price_range
    check (min_price is null or max_price is null or min_price <= max_price)
);
create index if not exists idx_tariffs_category on tariffs(category);
create index if not exists idx_tariffs_route on tariffs(origin, destination);
drop trigger if exists trg_tariffs_updated on tariffs;
create trigger trg_tariffs_updated before update on tariffs
  for each row execute function set_updated_at();

-- ---------- guides (Guide Directory) ----------
create table if not exists guides (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  region              text,
  city                text,
  languages           text[] default '{}',        -- ['fr','en','pidgin']
  specialties         text[] default '{}',        -- ['ecotourism','culture','hiking']
  phone               text,
  whatsapp            text,
  email               text,
  license_number      text,
  certification_status text,                       -- e.g. "MINTOUL-certified"
  active              boolean not null default true,
  source              text,
  verification_status verification_status not null default 'unverified',
  last_verified       date,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index if not exists idx_guides_region on guides(region);
create index if not exists idx_guides_languages on guides using gin(languages);
create index if not exists idx_guides_specialties on guides using gin(specialties);
drop trigger if exists trg_guides_updated on guides;
create trigger trg_guides_updated before update on guides
  for each row execute function set_updated_at();

-- ---------- hotels ----------
create table if not exists hotels (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  city                text,
  region              text,
  category            text,                       -- e.g. "3-star", "guesthouse"
  price_min           numeric(12,2),
  price_max           numeric(12,2),
  currency            text not null default 'XAF',
  address             text,
  phone               text,
  description         text,
  latitude            double precision,
  longitude           double precision,
  source              text,
  verification_status verification_status not null default 'unverified',
  last_verified       date,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index if not exists idx_hotels_city on hotels(city);
drop trigger if exists trg_hotels_updated on hotels;
create trigger trg_hotels_updated before update on hotels
  for each row execute function set_updated_at();

-- ---------- emergency_contacts ----------
create table if not exists emergency_contacts (
  id                  uuid primary key default gen_random_uuid(),
  category            emergency_category not null,
  name                text not null,
  city                text,
  region              text,
  phone               text,
  alt_phone           text,
  address             text,
  notes               text,
  source              text,
  verification_status verification_status not null default 'unverified',
  last_verified       date,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index if not exists idx_emergency_city on emergency_contacts(city);
create index if not exists idx_emergency_category on emergency_contacts(category);
drop trigger if exists trg_emergency_updated on emergency_contacts;
create trigger trg_emergency_updated before update on emergency_contacts
  for each row execute function set_updated_at();

-- =====================================================================
-- RAG
-- =====================================================================

-- Gemini text-embedding-004 => 768 dimensions.
create table if not exists knowledge_documents (
  id                  uuid primary key default gen_random_uuid(),
  title               text,
  content             text not null,
  source_type         text,                       -- destination|attraction|regulation|general
  source_ref          text,                       -- filename or record id it came from
  language            text default 'en',          -- en|fr|pidgin
  chunk_index         integer default 0,
  embedding           vector(768),
  metadata            jsonb default '{}',
  source              text,
  verification_status verification_status not null default 'unverified',
  last_verified       date,
  created_at          timestamptz not null default now()
);
-- ANN index for cosine similarity. HNSW needs no training data, so it is safe
-- to create on an empty table (see db/reindex.sql to rebuild an existing index).
create index if not exists idx_knowledge_embedding
  on knowledge_documents using hnsw (embedding vector_cosine_ops) with (m = 16, ef_construction = 64);
create index if not exists idx_knowledge_source_type on knowledge_documents(source_type);

-- RAG retrieval RPC: returns top matches above a similarity threshold.
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
$$;

-- =====================================================================
-- CONVERSATION LOG + ANONYMOUS ANALYTICS
-- =====================================================================

-- Minimal conversation record. session_id is a HASH of the WhatsApp number
-- (see SESSION_HASH_SALT) — never store the raw phone number here.
create table if not exists tourist_queries (
  id                  uuid primary key default gen_random_uuid(),
  session_id          text not null,              -- hashed contact, not PII
  channel             text not null default 'whatsapp',
  raw_message         text,
  normalized_message  text,
  language_detected   text,                       -- fr|en|pidgin|mixed|unknown
  intent              text,
  is_voice            boolean not null default false,
  created_at          timestamptz not null default now()
);
create index if not exists idx_queries_session on tourist_queries(session_id);
create index if not exists idx_queries_created on tourist_queries(created_at);

-- Anonymous analytics event powering the MINTOUL dashboard.
create table if not exists query_events (
  id                  uuid primary key default gen_random_uuid(),
  query_id            uuid references tourist_queries(id) on delete set null,
  occurred_at         timestamptz not null default now(),
  destination         text,
  intent              text,
  language            text,
  query_category      text,                       -- pricing|attractions|hotels|guides|transport|emergency|other
  tool_used           text,                       -- tourism_search|tariff_guard|guide_directory|emergency_info|none
  response_status     text,                       -- ok|not_found|error|fallback
  region_approx       text,
  complaint_flag      boolean not null default false,
  created_at          timestamptz not null default now()
);
create index if not exists idx_events_occurred on query_events(occurred_at);
create index if not exists idx_events_intent on query_events(intent);
create index if not exists idx_events_destination on query_events(destination);
create index if not exists idx_events_category on query_events(query_category);

-- =====================================================================
-- NOTES
-- Row Level Security (RLS): enable RLS and add policies before exposing
-- the anon key to any public client. n8n/scripts use the service role key
-- and bypass RLS. RLS policies are added in db/policies.sql (Day 2+).
-- =====================================================================
