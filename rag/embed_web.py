"""TourisCam AI — chunk + embed the scraped web records once, for review and load.

Reads dataset/web_scrape_2026-09-15/<source>.jsonl, chunks each record with the
same chunker as rag/ingest.py, prefixes every chunk with its record title (so
later chunks keep their context), embeds in batches, and writes
dataset/web_scrape_2026-09-15/embedded/<source>.jsonl (gitignored).
Chunks whose text is already in the cache are not re-embedded.

No database writes: the cache feeds rag/eval_retrieval.py (review) and
rag/ingest_web.py (load).

Usage:
    python rag/embed_web.py --dry-run
    python rag/embed_web.py [--only wikivoyage osm]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time

from config import ROOT, gemini_ingest_client
from embed import embed_texts
from ingest import chunk, clean

WEB_DIR = ROOT / "dataset" / "web_scrape_2026-09-15"
EMB_DIR = WEB_DIR / "embedded"
SOURCE_KEYS = ["staging", "fcdo", "mintoul", "wikivoyage", "osm"]
META_FIELDS = ("title", "type", "language", "location", "region", "source_id", "source_url",
               "authority_level", "license", "verification_status", "last_verified",
               "retrieved_at", "source_key", "batch")


def read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# Free-tier Gemini allows 1,000 embed requests/day per model and counts every
# chunk in a batch as one request; the live bot shares that quota. Batches save
# round-trips, not quota — check the remaining budget before large runs.
BATCH_SIZE = 100


def write_cache(key: str, chunks: list[dict], cache: dict) -> None:
    """Rewrite the cache file; chunks not yet embedded are stored with embedding=null."""
    with open(EMB_DIR / f"{key}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(json.dumps({**c, "embedding": cache.get(c["text_sha1"])}, ensure_ascii=False) + "\n")


def build_chunks(rec: dict) -> list[dict]:
    pieces = chunk(clean(rec["content"]))
    out = []
    for i, piece in enumerate(pieces):
        text = f"{rec['title']}\n\n{piece}"
        out.append({
            "chunk_id": f"{rec['id']}#{i}",
            "record_id": rec["id"],
            "chunk_index": i,
            "text": text,
            "text_sha1": hashlib.sha1(text.encode("utf-8")).hexdigest(),
            **{k: rec.get(k) for k in META_FIELDS},
        })
    return out


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Chunk + embed scraped web records (cached).")
    ap.add_argument("--only", nargs="+", choices=SOURCE_KEYS)
    ap.add_argument("--dry-run", action="store_true", help="chunk only; no embedding calls")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                    help="chunks per request (lower it for token-dense text such as OSM)")
    ap.add_argument("--pause", type=float, default=0.0,
                    help="seconds to wait between requests (stay under per-minute token limits)")
    args = ap.parse_args()

    EMB_DIR.mkdir(parents=True, exist_ok=True)
    grand = 0
    for key in args.only or SOURCE_KEYS:
        records = read_jsonl(WEB_DIR / f"{key}.jsonl")
        if not records:
            print(f"- {key}: no records, skipped")
            continue
        chunks = [c for rec in records for c in build_chunks(rec)]
        cache = {c["text_sha1"]: c["embedding"] for c in read_jsonl(EMB_DIR / f"{key}.jsonl")
                 if c.get("embedding")}
        todo = [c for c in chunks if c["text_sha1"] not in cache]
        print(f"- {key}: {len(records)} records -> {len(chunks)} chunks "
              f"({len(chunks) - len(todo)} cached, {len(todo)} to embed)")
        grand += len(chunks)
        if args.dry_run:
            continue

        failure = None
        for start in range(0, len(todo), args.batch_size):
            batch = todo[start:start + args.batch_size]
            if start and args.pause:
                time.sleep(args.pause)
            try:
                vectors = embed_texts([c["text"] for c in batch], task_type="RETRIEVAL_DOCUMENT",
                                      client=gemini_ingest_client())  # never the bot's key
            except RuntimeError as e:  # e.g. daily quota exhausted
                failure = e
                break
            cache.update({c["text_sha1"]: v for c, v in zip(batch, vectors)})
            write_cache(key, chunks, cache)  # keep paid-for vectors if a later batch fails
        write_cache(key, chunks, cache)
        if failure:
            done = sum(c["text_sha1"] in cache for c in chunks)
            msg = str(failure)
            quota = msg.find("Quota exceeded")  # names the exact metric + limit when present
            detail = msg[quota:quota + 200] if quota >= 0 else msg[:200]
            print(f"  ! {key}: stopped at {done}/{len(chunks)} chunks embedded: {detail}",
                  file=sys.stderr)
            print("  Re-run later — cached chunks are not re-embedded.", file=sys.stderr)
            return 3
    print(f"\n{'Dry-run: ' if args.dry_run else ''}{grand} chunk(s) total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
