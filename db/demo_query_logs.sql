-- =====================================================================
-- TourisCam AI — SYNTHETIC demo query logs for the MINTOUL dashboard
-- Source: dataset/whatsapp_visitor_query_logs.csv (see query_logs_README.md)
-- Loaded by rag/load_query_logs.py (runs this file, then truncate + reload).
-- Kept separate from query_events so simulated rows never mix with real
-- bot traffic. Drop this table once real usage data exists.
-- =====================================================================

create table if not exists demo_query_logs (
  query_id              text primary key,             -- QRY-000001
  occurred_at           timestamptz not null,          -- CSV local time, Africa/Douala (UTC+1)
  session_id            text not null,
  visitor_id            text not null,                 -- anonymized, no real PII
  channel               text not null check (channel in ('text','voice_note')),
  language              text not null check (language in ('fr','en','pidgin')),  -- same vocab as query_events
  visitor_type          text not null check (visitor_type in ('domestic','foreign')),
  visitor_origin        text,                          -- region if domestic, country if foreign
  query_type            text not null check (query_type in
                          ('pricing','opening_hours','directions','cultural_info',
                           'booking_interest','transport_fare','emergency_sos','general_chat')),
  site_referenced       text,                          -- null for general_chat
  region_referenced     text,
  sentiment             text not null check (sentiment in ('positive','neutral','negative')),
  response_time_seconds numeric(5,2),
  resolved              boolean not null,
  is_emergency          boolean not null,
  is_synthetic          boolean not null default true,
  loaded_at             timestamptz not null default now()
);
create index if not exists idx_demo_logs_occurred on demo_query_logs(occurred_at);
create index if not exists idx_demo_logs_region on demo_query_logs(region_referenced);
create index if not exists idx_demo_logs_site on demo_query_logs(site_referenced);
create index if not exists idx_demo_logs_query_type on demo_query_logs(query_type);

-- RLS on, no anon policy yet: only service role / direct Postgres can read.
-- The Day 5 dashboard adds a read policy (db/policies.sql).
alter table demo_query_logs enable row level security;
