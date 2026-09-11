-- =====================================================================
-- TourisCam AI — Seed data (initial scope: Douala, Yaoundé, Limbe, Kribi, West)
--
-- HONESTY POLICY (see knowledge/README.md):
--   * verification_status reflects the ACTUAL trust level, not aspiration.
--   * 'verified'   = well-established public fact (existence/description of
--                    famous places). Formal citation still to be attached.
--   * 'benchmark'  = typical market range, NOT an official tariff.
--   * 'unverified' = placeholder that MUST be confirmed before the demo.
--   * We do NOT invent phone numbers or official prices. Placeholders are
--     left NULL or clearly marked 'unverified'.
-- Re-run safe: uses ON CONFLICT on slug where applicable.
-- =====================================================================

-- ---------- destinations ----------
insert into destinations (name, slug, region, city, description, latitude, longitude, tags, source, verification_status, last_verified)
values
  ('Douala', 'douala', 'Littoral', 'Douala',
   'Economic capital and largest city of Cameroon; main international gateway (Douala International Airport) and seaport.',
   4.0511, 9.7679, array['city','gateway','business'],
   'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('Yaoundé', 'yaounde', 'Centre', 'Yaoundé',
   'Political capital of Cameroon, set across seven hills; home to national museums and government institutions.',
   3.8480, 11.5021, array['city','capital','culture'],
   'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('Limbe', 'limbe', 'South-West', 'Limbe',
   'Coastal town known for volcanic black-sand beaches, the Limbe Wildlife Centre and the Limbe Botanic Garden, at the foot of Mount Cameroon.',
   4.0186, 9.2147, array['beach','wildlife','nature'],
   'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('Kribi', 'kribi', 'South', 'Kribi',
   'Seaside resort town famous for white-sand beaches and the nearby Lobé Falls, where a river cascades directly into the Atlantic Ocean.',
   2.9370, 9.9096, array['beach','waterfall','resort'],
   'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('Foumban', 'foumban', 'West', 'Foumban',
   'Historic seat of the Bamoun kingdom in the West Region; renowned for the Royal Palace, its museum, and traditional arts and crafts.',
   5.7255, 10.9017, array['heritage','culture','crafts'],
   'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('Bafoussam', 'bafoussam', 'West', 'Bafoussam',
   'Largest city of the West Region and gateway to the Bamiléké highlands, traditional chiefdoms and coffee-growing areas.',
   5.4768, 10.4176, array['city','highlands','culture'],
   'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('Dschang', 'dschang', 'West', 'Dschang',
   'Highland town in the West Region known for its cool climate, the Museum of Civilisations and surrounding scenic landscapes.',
   5.4468, 10.0537, array['highlands','museum','climate'],
   'Public record — formal citation pending', 'verified', '2026-09-11')
on conflict (slug) do update set
  description = excluded.description,
  updated_at = now();

-- ---------- attractions ----------
insert into attractions (destination_id, name, category, description, address, source, verification_status, last_verified)
select d.id, v.name, v.category, v.description, v.address, v.source, v.verification_status::verification_status, v.last_verified::date
from (values
  ('limbe',   'Limbe Wildlife Centre', 'wildlife',
   'Sanctuary caring for primates and other rescued wildlife, focused on conservation and education.',
   'Limbe, South-West Region', 'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('limbe',   'Limbe Botanic Garden', 'nature',
   'One of the oldest botanic gardens in Africa (founded in the colonial era), featuring tropical plant collections.',
   'Limbe, South-West Region', 'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('kribi',   'Lobé Falls (Chutes de la Lobé)', 'waterfall',
   'Rare coastal waterfall where the Lobé River drops directly into the Atlantic Ocean, near Kribi.',
   'South of Kribi, South Region', 'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('foumban', 'Royal Palace of Foumban & Museum', 'heritage',
   'Palace of the Sultan of the Bamoun; its museum holds royal artefacts, thrones and traditional art.',
   'Foumban, West Region', 'Public record — formal citation pending', 'verified', '2026-09-11'),
  ('yaounde', 'National Museum of Yaoundé', 'museum',
   'National museum presenting Cameroonian art, history and cultural heritage, housed in a former presidential palace.',
   'Yaoundé, Centre Region', 'Public record — formal citation pending', 'verified', '2026-09-11')
) as v(dest_slug, name, category, description, address, source, verification_status, last_verified)
join destinations d on d.slug = v.dest_slug;

-- ---------- tariffs (BENCHMARK only — not official) ----------
-- NOTE: These are placeholder benchmark ranges to exercise Tariff Guard.
-- They MUST be replaced with surveyed values before the demo. Marked accordingly.
insert into tariffs (category, origin, destination, transport_type, description, min_price, max_price, currency, unit, time_of_day, source, verification_status, last_verified, notes)
values
  ('transport', 'Douala International Airport', 'Bonanjo', 'taxi',
   'Typical private taxi fare, airport to Bonanjo (Douala city centre).',
   null, null, 'XAF', 'per trip', 'any',
   'Field benchmark — SURVEY PENDING', 'unverified', null,
   'Placeholder row: price range intentionally NULL until surveyed. Tariff Guard must report as unavailable, not invent a value.'),
  ('transport', 'Kribi town', 'Lobé Falls', 'taxi',
   'Short taxi/moto trip from Kribi centre toward the Lobé Falls area.',
   null, null, 'XAF', 'per trip', 'any',
   'Field benchmark — SURVEY PENDING', 'unverified', null,
   'Placeholder row: awaiting surveyed benchmark.');

-- ---------- guides (EXAMPLE placeholders — not real people) ----------
-- No real names/contacts are invented. These are clearly flagged as
-- unverified template rows and MUST be replaced with certified guides.
insert into guides (name, region, city, languages, specialties, phone, whatsapp, certification_status, active, source, verification_status, last_verified)
values
  ('[PLACEHOLDER] Certified Guide — West', 'West', 'Foumban',
   array['fr','en'], array['heritage','culture'], null, null,
   'MINTOUL certification status: TO CONFIRM', true,
   'Placeholder', 'unverified', null),
  ('[PLACEHOLDER] Certified Guide — South-West', 'South-West', 'Limbe',
   array['en','pidgin'], array['ecotourism','wildlife'], null, null,
   'MINTOUL certification status: TO CONFIRM', true,
   'Placeholder', 'unverified', null);

-- ---------- emergency_contacts (UNVERIFIED — confirm before demo) ----------
-- National emergency numbers vary and must be confirmed with an official
-- source before the demo. Left unverified deliberately.
insert into emergency_contacts (category, name, city, region, phone, notes, source, verification_status, last_verified)
values
  ('police', 'Police (national) — CONFIRM NUMBER', null, null, null,
   'National police emergency line to be confirmed with an official source before demo.',
   'Official source pending', 'unverified', null),
  ('fire', 'Fire brigade — CONFIRM NUMBER', null, null, null,
   'Fire/rescue emergency line to be confirmed before demo.',
   'Official source pending', 'unverified', null),
  ('medical', 'Medical emergency / SAMU — CONFIRM NUMBER', null, null, null,
   'Medical emergency line to be confirmed before demo.',
   'Official source pending', 'unverified', null);

-- ---------- knowledge_documents ----------
-- NOTE: knowledge_documents is populated by the RAG ingestion script
-- (python rag/ingest.py), which reads knowledge/**.md, chunks, and embeds each
-- chunk. We intentionally do NOT insert rows here: rows without embeddings can
-- never be retrieved by match_documents() and would be dead data.
