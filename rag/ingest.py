"""TourisCam AI — knowledge ingestion.

Reads every markdown file under knowledge/**, parses its frontmatter for
provenance, cleans + chunks the body, embeds each chunk with Gemini, and
upserts into Supabase `knowledge_documents`.

Idempotent: for each source file we delete prior rows with the same
source_ref before inserting fresh chunks, so re-running is safe.

Usage:
    python rag/ingest.py            # ingest all knowledge/*.md
    python rag/ingest.py --dry-run  # parse + chunk only, no embeds/db writes
    python rag/ingest.py --file knowledge/destinations/limbe.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

import frontmatter

from config import KNOWLEDGE_DIR, pg_connect
from embed import embed_text, to_pgvector

# --- chunking parameters ---
# Docs are short; chunk on paragraph boundaries, packing up to ~MAX_CHARS
# per chunk with a small overlap for context continuity.
MAX_CHARS = 1200
OVERLAP_CHARS = 150

VALID_STATUS = {"verified", "benchmark", "estimated", "unverified", "unavailable"}


def clean(text: str) -> str:
    lines = [ln.rstrip() for ln in text.strip().splitlines()]
    # collapse 3+ blank lines to a single blank line
    out: List[str] = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip()


def chunk(text: str) -> List[str]:
    """Pack paragraphs into ~MAX_CHARS chunks with char overlap."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf = ""
    for p in paras:
        if not buf:
            buf = p
        elif len(buf) + 2 + len(p) <= MAX_CHARS:
            buf = f"{buf}\n\n{p}"
        else:
            chunks.append(buf)
            tail = buf[-OVERLAP_CHARS:] if OVERLAP_CHARS else ""
            buf = f"{tail}\n\n{p}".strip() if tail else p
    if buf:
        chunks.append(buf)
    # Hard-split any oversized single paragraph.
    final: List[str] = []
    for c in chunks:
        if len(c) <= MAX_CHARS * 1.5:
            final.append(c)
        else:
            for i in range(0, len(c), MAX_CHARS):
                final.append(c[i:i + MAX_CHARS])
    return final


def iter_files(single: Path | None) -> Iterable[Path]:
    if single:
        yield single
        return
    yield from sorted(KNOWLEDGE_DIR.rglob("*.md"))


def parse_doc(path: Path) -> dict | None:
    """Parse one markdown file into a normalized record, or None to skip."""
    post = frontmatter.load(path)
    body = clean(post.content)
    # Skip index/policy files (README) and empty bodies.
    if path.name.lower() == "readme.md" or not body:
        return None

    meta = post.metadata or {}
    status = str(meta.get("verification_status", "unverified")).lower()
    if status not in VALID_STATUS:
        print(f"  ! {path.name}: unknown verification_status '{status}', "
              f"defaulting to 'unverified'")
        status = "unverified"

    source_ref = str(meta.get("source_ref") or path.stem)
    return {
        "title": meta.get("title") or path.stem,
        "source_type": meta.get("source_type") or path.parent.name,
        "source_ref": source_ref,
        "language": (meta.get("language") or "en"),
        "source": meta.get("source"),
        "verification_status": status,
        "last_verified": meta.get("last_verified") or None,
        "body": body,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest knowledge into Supabase.")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse + chunk only; no embeddings or DB writes")
    ap.add_argument("--file", type=str, default=None,
                    help="ingest a single markdown file")
    args = ap.parse_args()

    single = Path(args.file).resolve() if args.file else None
    if single and not single.exists():
        print(f"File not found: {single}", file=sys.stderr)
        return 1

    conn = None if args.dry_run else pg_connect()

    insert_sql = (
        "insert into knowledge_documents "
        "(title, content, source_type, source_ref, language, chunk_index, "
        " embedding, source, verification_status, last_verified, metadata) "
        "values (%s,%s,%s,%s,%s,%s, %s::vector, %s,%s,%s, %s::jsonb)"
    )

    total_files = 0
    total_chunks = 0
    try:
        for path in iter_files(single):
            rec = parse_doc(path)
            if rec is None:
                continue
            total_files += 1
            chunks = chunk(rec["body"])
            rel = path.relative_to(KNOWLEDGE_DIR)
            print(f"• {rel} — {len(chunks)} chunk(s) "
                  f"[{rec['verification_status']}]")

            if args.dry_run:
                total_chunks += len(chunks)
                continue

            with conn.cursor() as cur:
                # Idempotency: clear prior rows for this source_ref + type.
                cur.execute(
                    "delete from knowledge_documents "
                    "where source_ref = %s and source_type = %s",
                    (rec["source_ref"], rec["source_type"]),
                )
                for idx, ch in enumerate(chunks):
                    try:
                        emb = embed_text(ch, task_type="RETRIEVAL_DOCUMENT")
                    except Exception as e:  # noqa: BLE001
                        conn.rollback()
                        print(f"  ! embed failed for chunk {idx} of {rel}: {e}",
                              file=sys.stderr)
                        return 2
                    cur.execute(insert_sql, (
                        rec["title"], ch, rec["source_type"], rec["source_ref"],
                        rec["language"], idx, to_pgvector(emb), rec["source"],
                        rec["verification_status"], rec["last_verified"],
                        json.dumps({"path": str(rel)}),
                    ))
            conn.commit()
            total_chunks += len(chunks)
    finally:
        if conn is not None:
            conn.close()

    print(f"\nDone: {total_files} file(s), {total_chunks} chunk(s) "
          f"{'parsed (dry-run)' if args.dry_run else 'ingested'}.")
    if not args.dry_run and total_chunks:
        print("Tip: for larger datasets, refresh the ivfflat index "
              "(see db/reindex.sql) to improve recall.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
