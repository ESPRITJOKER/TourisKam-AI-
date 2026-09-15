"""TourisCam AI — load the reviewed web chunks into knowledge_documents.

Reads the embedding cache written by rag/embed_web.py (no Gemini calls) and
inserts every chunk with its provenance in `metadata` (batch, source_key,
source_id, authority_level, license, region, location, record_id).

Idempotent per source: rows for the same batch + source_key are deleted first,
in the same transaction. Roll back the whole web batch with:
    delete from knowledge_documents where metadata->>'batch' = 'web_2026-09-15';

Usage:
    python rag/ingest_web.py --dry-run
    python rag/ingest_web.py [--only fcdo mintoul]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from config import ROOT, pg_connect
from embed import to_pgvector

EMB_DIR = ROOT / "dataset" / "web_scrape_2026-09-15" / "embedded"
BATCH = "web_2026-09-15"
SOURCE_KEYS = ["staging", "fcdo", "mintoul", "wikivoyage", "osm"]


def read_chunks(key: str) -> list[dict]:
    path = EMB_DIR / f"{key}.jsonl"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def to_row(c: dict) -> tuple:
    metadata = {
        "batch": c.get("batch") or BATCH,
        "source_key": c["source_key"],
        "source_id": c.get("source_id"),
        "authority_level": c.get("authority_level"),
        "license": c.get("license"),
        "region": c.get("region"),
        "location": c.get("location"),
        "record_id": c["record_id"],
        "retrieved_at": c.get("retrieved_at"),
    }
    return (
        c["title"], c["text"], c["type"], c["record_id"], c["language"], c["chunk_index"],
        to_pgvector(c["embedding"]), c["source_url"], c["verification_status"],
        c.get("last_verified") or c.get("retrieved_at"), json.dumps(metadata, ensure_ascii=False),
    )


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Load cached web chunks into Supabase.")
    ap.add_argument("--only", nargs="+", choices=SOURCE_KEYS)
    ap.add_argument("--dry-run", action="store_true", help="validate the cache only; no DB writes")
    args = ap.parse_args()

    plan: dict[str, list[dict]] = {}
    for key in args.only or SOURCE_KEYS:
        chunks = read_chunks(key)
        missing = [c["chunk_id"] for c in chunks if not c.get("embedding")]
        if missing:
            print(f"  ! {key}: {len(missing)} chunk(s) without embeddings — run rag/embed_web.py", file=sys.stderr)
            return 2
        if chunks:
            plan[key] = chunks
            status = Counter(c["verification_status"] for c in chunks)
            print(f"- {key}: {len(chunks)} chunks {dict(status)}")
        else:
            print(f"- {key}: no cached chunks, skipped")

    if args.dry_run or not plan:
        print("Dry-run: no DB writes." if args.dry_run else "Nothing to load.")
        return 0

    from psycopg2.extras import execute_values

    insert_sql = (
        "insert into knowledge_documents "
        "(title, content, source_type, source_ref, language, chunk_index, "
        " embedding, source, verification_status, last_verified, metadata) values %s"
    )
    template = "(%s,%s,%s,%s,%s,%s, %s::vector, %s,%s,%s, %s::jsonb)"
    conn = pg_connect()
    try:
        for key, chunks in plan.items():
            with conn.cursor() as cur:  # one transaction per source: delete + insert
                cur.execute(
                    "delete from knowledge_documents "
                    "where metadata->>'batch' = %s and metadata->>'source_key' = %s",
                    (BATCH, key),
                )
                deleted = cur.rowcount
                execute_values(cur, insert_sql, [to_row(c) for c in chunks],
                               template=template, page_size=200)
            conn.commit()
            print(f"  [OK] {key}: replaced {deleted} -> inserted {len(chunks)}")
        with conn.cursor() as cur:
            cur.execute("select count(*) from knowledge_documents")
            total = cur.fetchone()[0]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"\nDone. knowledge_documents now has {total} rows. "
          "Next: refresh the ANN index (python scripts/apply_sql.py db/reindex.sql).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
