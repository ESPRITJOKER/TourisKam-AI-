# Web scrape batch `web_2026-09-15`

Expands the TourisCam AI RAG knowledge base beyond the curated
`touriscam_dataset_final/` package, following its `RAG_POLICY.md` source
hierarchy. Every record is extracted text from a real, cited page — nothing is
generated or translated, and no Pidgin content is created.

## Files

| File | What |
|---|---|
| `<source>.jsonl` | Reviewable records (rag_records.jsonl schema + `language`, `authority_level`, `license`, `source_key`, `batch`, `retrieved_at`) |
| `sources_web.csv` | Source registry SRC-026…SRC-031 (continues `touriscam_dataset_final/sources.csv`) |
| `REPORT.md` | Counts, drops/filters, region coverage, samples |
| `EVAL.md` | Before/after retrieval comparison on fixed EN/FR questions |
| `stats.json` | Per-source scraper statistics |
| `raw/`, `embedded/` | HTTP response cache and embedding cache — **gitignored**, regenerable |

Regenerate: `python rag/scrapers/run_all.py` → `python rag/embed_web.py` →
`python rag/eval_retrieval.py` → (after review) `python rag/ingest_web.py` →
`python scripts/apply_sql.py db/reindex.sql db/match_documents_v2.sql` (HNSW index +
authority-aware retrieval that keeps official facts from being crowded out).

## Sources, labels and licenses

| Source | Authority → status | License / attribution |
|---|---|---|
| **MINTOUL** mintoul.gov.cm (SRC-031) | primary → `verified`; guides & hotels `unverified` (listed ≠ currently available) | Official public information, Ministère du Tourisme et des Loisirs |
| **UK FCDO** travel advice (SRC-029) | primary → `verified`, `last_verified` = GOV.UK update date | Contains public sector information licensed under the Open Government Licence v3.0 |
| **Wikivoyage** EN (SRC-026) / FR (SRC-027) | third_party → `unverified` | Text from Wikivoyage contributors, CC BY-SA 4.0; each record links the exact revision (`oldid`) |
| **OpenStreetMap** POIs (SRC-028) | secondary → `unverified` | © OpenStreetMap contributors, ODbL 1.0 |
| **Kribi→West staging CSV** (SRC-030) | third_party → per-row confidence: VERIFIED_* `benchmark`, UNCONFIRMED_PRICE `estimated`, UNCONFIRMED_ALL `unverified` | Project-internal verification dossier |

CC BY-SA and ODbL require attribution wherever this content is shown or
redistributed; derived text chunks stay under the same licenses.

## Safety filters applied

- **Injected spam on mintoul.gov.cm:** most WordPress posts are casino / "ESA letter"
  SEO spam. Spam-titled entries are never fetched; page bodies with spam terms or
  (for posts) a non-FR/EN language are dropped.
- **National ID numbers:** MINTOUL guide pages publish CNI numbers; they are replaced
  with `[ID number removed]` before saving (RAG_POLICY.md). Professional contact
  details are kept as published by MINTOUL.
- Only the page body (`.entry-content`, parsed Wikivoyage sections, GOV.UK parts) is
  kept — never menus/navigation. Records under 80 characters and exact duplicates
  are dropped.

## Excluded on purpose

- TripAdvisor, Booking, Google Maps, Petit Futé — terms forbid scraping; prices go stale.
- UNESCO whc.unesco.org — `robots.txt` sets `ai-train=no` and disallows AI crawlers;
  the 20 UNESCO records already in the curated dataset remain.

## Known issues found while scraping

- Several MINTOUL URLs cited in `touriscam_dataset_final/sources.csv` now return
  404: `/tours/tourisme-balneaires/`, `/tourisme/sports-tourism/`,
  `/tourisme/tourisme-des-affaires/`, and `/site/…` profiles (e.g. `/site/mont-cameroun/`).
