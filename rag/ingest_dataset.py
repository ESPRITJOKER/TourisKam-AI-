"""TourisCam AI — ingest the curated dataset package into knowledge_documents.

Reads the consolidated RAG JSONL from dataset/touriscam_dataset_final/, merges
the two JSONL files (rich `rag_records.jsonl` as base + the 6 extra records from
`touriscam_rag_final.jsonl`), enriches each record with source metadata from
`sources.csv`, embeds the content with Gemini, and upserts into
`knowledge_documents`.

No schema change needed: dataset fields map onto existing columns; extra
provenance (source_id, authority_level, location, region) is stored in the
`metadata` JSONB per the dataset's RAG_POLICY.md.

Usage:
    python rag/ingest_dataset.py --dry-run
    python rag/ingest_dataset.py
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from config import ROOT, pg_connect
from embed import embed_text, to_pgvector

DATASET_DIR = ROOT / "dataset" / "touriscam_dataset_final"
RICH = DATASET_DIR / "rag_records.jsonl"
FINAL = DATASET_DIR / "touriscam_rag_final.jsonl"
SOURCES = DATASET_DIR / "sources.csv"
PACKAGE_DATE = "2026-09-11"  # dataset package curation date (README_FINAL.md)

VALID_STATUS = {"verified", "benchmark", "estimated", "unverified", "unavailable"}
# Normalize a couple of type spellings so source_type is consistent.
TYPE_MAP = {"practical": "practical_information", "event": "event"}


def load_sources() -> dict:
    out: dict[str, dict] = {}
    with open(SOURCES, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            out[row["source_id"]] = row
    return out


def load_records() -> list[dict]:
    """Merge the two JSONL files: rich base + extras from final."""
    def read(p: Path) -> list[dict]:
        return [json.loads(ln) for ln in open(p, encoding="utf-8") if ln.strip()]

    rich = read(RICH)
    by_id = {r["id"]: r for r in rich}
    for r in read(FINAL):
        if r["id"] not in by_id:
            by_id[r["id"]] = r  # keep leaner record only if not already present
    return list(by_id.values())


def normalize(rec: dict, sources: dict) -> dict:
    src = sources.get(rec.get("source_id"), {})
    status = str(rec.get("verification_status", "unverified")).lower()
    if status not in VALID_STATUS:
        status = "unverified"
    rtype = TYPE_MAP.get(rec.get("type"), rec.get("type") or "general")
    source_url = rec.get("source_url") or src.get("url")
    return {
        "title": rec.get("title") or rec["id"],
        "content": (rec.get("content") or "").strip(),
        "source_type": rtype,
        "source_ref": rec["id"],
        "language": rec.get("language", "en"),
        "source": source_url,
        "verification_status": status,
        "last_verified": PACKAGE_DATE,
        "metadata": {
            "dataset": "touriscam_dataset_final",
            "source_id": rec.get("source_id"),
            "authority_level": src.get("authority_level"),
            "publisher": src.get("publisher"),
            "location": rec.get("location"),
            "region": rec.get("region"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest curated dataset into Supabase.")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse + merge only; no embeddings or DB writes")
    args = ap.parse_args()

    sources = load_sources()
    records = [normalize(r, sources) for r in load_records()]
    records = [r for r in records if r["content"]]  # skip empty content

    # quick profile
    from collections import Counter
    types = Counter(r["source_type"] for r in records)
    print(f"Loaded {len(records)} dataset records: {dict(types)}")
    missing_url = [r["source_ref"] for r in records if not r["source"]]
    if missing_url:
        print(f"  ! {len(missing_url)} record(s) missing source_url: "
              f"{missing_url[:8]}{'...' if len(missing_url) > 8 else ''}")

    if args.dry_run:
        print("Dry-run: no embeddings or DB writes.")
        return 0

    insert_sql = (
        "insert into knowledge_documents "
        "(title, content, source_type, source_ref, language, chunk_index, "
        " embedding, source, verification_status, last_verified, metadata) "
        "values (%s,%s,%s,%s,%s,%s, %s::vector, %s,%s,%s, %s::jsonb)"
    )
    conn = pg_connect()
    try:
        ids = [r["source_ref"] for r in records]
        with conn.cursor() as cur:
            cur.execute(
                "delete from knowledge_documents where source_ref = any(%s)", (ids,)
            )
        conn.commit()

        n = 0
        for r in records:
            try:
                emb = embed_text(r["content"], task_type="RETRIEVAL_DOCUMENT")
            except Exception as e:  # noqa: BLE001
                conn.rollback()
                print(f"  ! embed failed for {r['source_ref']}: {e}", file=sys.stderr)
                return 2
            with conn.cursor() as cur:
                cur.execute(insert_sql, (
                    r["title"], r["content"], r["source_type"], r["source_ref"],
                    r["language"], 0, to_pgvector(emb), r["source"],
                    r["verification_status"], r["last_verified"],
                    json.dumps(r["metadata"]),
                ))
            conn.commit()
            n += 1
            if n % 20 == 0:
                print(f"  ... embedded {n}/{len(records)}")
        print(f"\nDone: {n} dataset record(s) ingested into knowledge_documents.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
