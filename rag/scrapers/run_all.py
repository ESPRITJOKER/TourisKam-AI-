"""Run the TourisCam web scrapers -> reviewable JSONL files + REPORT.md.

Writes dataset/web_scrape_2026-09-15/<source>.jsonl (no database writes), plus
sources_web.csv (source registry) and REPORT.md (counts, drops, samples) built
from every JSONL present, so re-running one source keeps the others.

Usage:
    python rag/scrapers/run_all.py                          # all sources
    python rag/scrapers/run_all.py --only fcdo wikivoyage --limit 2
"""
from __future__ import annotations

import argparse
import csv
import importlib
import json
import math
import sys
import time
import traceback
from collections import Counter
from datetime import datetime

from common import BATCH, OUT_DIR, SOURCES, Fetcher, finalize

SOURCE_KEYS = ["staging", "fcdo", "wikivoyage", "osm", "mintoul"]  # slow MINTOUL crawl last
CHUNK_CHARS = 1050  # rough average chunk length produced by rag/ingest.py chunk()
STATS_PATH = OUT_DIR / "stats.json"


def load_jsonl(key: str) -> list[dict]:
    path = OUT_DIR / f"{key}.jsonl"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_sources_csv() -> None:
    cols = ["source_id", "publisher", "title", "scope", "url", "authority_level", "license"]
    with open(OUT_DIR / "sources_web.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for sid, meta in SOURCES.items():
            w.writerow({"source_id": sid, **meta})


def est_chunks(records: list[dict]) -> int:
    return sum(max(1, math.ceil(len(r["content"]) / CHUNK_CHARS)) for r in records)


def write_report(all_stats: dict) -> None:
    lines = [f"# Web scrape report — batch `{BATCH}`", "",
             f"_Generated {datetime.now():%Y-%m-%d %H:%M}. Files only — nothing loaded into Supabase._", "",
             "| Source | Records | Chars | Est. chunks | Languages | Verification | Authority |",
             "|---|---:|---:|---:|---|---|---|"]
    totals = Counter()
    per_source = {k: load_jsonl(k) for k in SOURCE_KEYS}
    for key, recs in per_source.items():
        if not recs:
            continue
        chars, chunks = sum(len(r["content"]) for r in recs), est_chunks(recs)
        totals.update(records=len(recs), chars=chars, chunks=chunks)
        fmt = lambda field: ", ".join(f"{v} {n}" for v, n in Counter(r.get(field) for r in recs).most_common())
        lines.append(f"| {key} | {len(recs)} | {chars:,} | {chunks} | {fmt('language')} | "
                     f"{fmt('verification_status')} | {fmt('authority_level')} |")
    lines.append(f"| **total** | **{totals['records']}** | **{totals['chars']:,}** | "
                 f"**{totals['chunks']}** | | | |")

    lines += ["", "## Filters and drops per source", ""]
    for key in SOURCE_KEYS:
        if key in all_stats:
            s = {k: v for k, v in all_stats[key].items() if k not in ("run_at",)}
            lines.append(f"- **{key}**: " + ", ".join(f"{k}={v}" for k, v in s.items()))

    lines += ["", "## Region coverage (all sources)", ""]
    regions = Counter(r.get("region") or "(none)" for recs in per_source.values() for r in recs)
    lines.append(", ".join(f"{reg}: {n}" for reg, n in regions.most_common()))

    lines += ["", "## Samples", ""]
    for key, recs in per_source.items():
        for r in recs[:1] + recs[len(recs) // 2:len(recs) // 2 + 1] if recs else []:
            lines += [f"**[{key}] {r['title']}** — `{r['verification_status']}` / `{r['authority_level']}` "
                      f"— <{r['source_url']}>", "",
                      "> " + r["content"][:400].replace("\n", " ") + ("…" if len(r["content"]) > 400 else ""), ""]
    (OUT_DIR / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Scrape web sources into reviewable JSONL.")
    ap.add_argument("--only", nargs="+", choices=SOURCE_KEYS, help="run only these sources")
    ap.add_argument("--limit", type=int, default=None, help="max pages/items per source (testing)")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        stream.reconfigure(encoding="utf-8", errors="replace")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_stats = json.loads(STATS_PATH.read_text(encoding="utf-8")) if STATS_PATH.exists() else {}
    fetcher = Fetcher()
    failed = []
    for key in args.only or SOURCE_KEYS:
        print(f"\n== {key} ==")
        stats: Counter = Counter()
        t0 = time.monotonic()
        try:
            records = importlib.import_module(key).scrape(fetcher, args.limit, stats)
        except Exception:  # noqa: BLE001 - keep other sources running
            traceback.print_exc()
            failed.append(key)
            continue
        kept = finalize(key, records, stats)
        all_stats[key] = {**dict(stats), "limit": args.limit,
                          "seconds": round(time.monotonic() - t0),
                          "run_at": datetime.now().isoformat(timespec="seconds")}
        print(f"  kept {len(kept)} record(s), ~{est_chunks(kept)} chunks | {dict(stats)}")

    STATS_PATH.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False), encoding="utf-8")
    write_sources_csv()
    write_report(all_stats)
    print(f"\nWrote {OUT_DIR / 'REPORT.md'}")
    if failed:
        print(f"FAILED sources: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
