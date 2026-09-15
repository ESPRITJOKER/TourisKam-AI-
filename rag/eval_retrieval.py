"""TourisCam AI — compare retrieval before/after adding the scraped web corpus.

Embeds a fixed set of EN/FR tourist questions, then ranks by exact cosine
similarity over (a) the current knowledge_documents rows, (b) those rows plus the
cached web chunks from rag/embed_web.py, and (c) the same merged corpus with the
rerank from db/match_documents_v2.sql (authority boost + max 2 chunks per
record). Writes a side-by-side report so we can see whether the new sources help
or crowd out official facts. Read-only: nothing is written to the database.

Usage:
    python rag/eval_retrieval.py [-k 5]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime

from config import ROOT, gemini_ingest_client, pg_connect
from embed import embed_texts

WEB_DIR = ROOT / "dataset" / "web_scrape_2026-09-15"
EMB_DIR = WEB_DIR / "embedded"
THRESHOLD = 0.5          # match_documents() default in db/schema.sql
MAX_PER_RECORD = 2       # keep in sync with db/match_documents_v2.sql

QUESTIONS = [
    "What can I see in Limbe?",
    "Que voir à Kribi ?",
    "Do I need a visa to visit Cameroon?",
    "Is it safe to travel to the North-West region?",
    "Which hotels are in Bafoussam?",
    "Parle-moi du lac Nyos",
    "How do I climb Mount Cameroon?",
    "Combien coûte l'entrée au Musée maritime de Douala ?",
    "What is there to do in Rhumsiki?",
    "How do I get from Douala to Yaoundé?",
    "Visiter la chefferie de Bandjoun",
    "Where can I see gorillas in Cameroon?",
    "What festivals happen in Foumban?",
    "Quel est le prix d'un taxi à Douala ?",
    "What should I know about the Far North region?",
]


def boost(doc: dict) -> float:
    """Authority tie-break — keep in sync with db/match_documents_v2.sql."""
    if doc["authority"] == "primary" or doc["status"] == "verified":
        return 0.04
    if doc["authority"] == "secondary" or doc["status"] == "benchmark":
        return 0.02
    return 0.0


def official(doc: dict) -> bool:
    return doc["authority"] == "primary" or doc["status"] == "verified"


def unit(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def load_current() -> list[dict]:
    conn = pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("set transaction read only")
            cur.execute(
                "select title, source_type, verification_status, "
                "coalesce(metadata->>'authority_level', ''), coalesce(source_ref, id::text), "
                "embedding::text from knowledge_documents where embedding is not null"
            )
            rows = cur.fetchall()
        conn.rollback()
    finally:
        conn.close()
    return [{"title": t, "status": vs, "authority": al, "ref": ref, "new": False,
             "label": f"{st}/{vs}{'/' + al if al else ''}", "vec": unit(json.loads(e))}
            for t, st, vs, al, ref, e in rows]


def load_web() -> list[dict]:
    docs = []
    for path in sorted(EMB_DIR.glob("*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                if not c.get("embedding"):  # chunk not embedded yet (e.g. quota stop)
                    continue
                docs.append({"title": c["title"], "status": c["verification_status"],
                             "authority": c["authority_level"], "ref": c["record_id"], "new": True,
                             "label": f"{c['source_key']}/{c['verification_status']}/{c['authority_level']}",
                             "vec": unit(c["embedding"])})
    return docs


def scored(q: list[float], docs: list[dict]) -> list[tuple[float, dict]]:
    out = [(sum(a * b for a, b in zip(q, d["vec"])), d) for d in docs]
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def rerank(ranked: list[tuple[float, dict]], k: int) -> list[tuple[float, dict]]:
    """Threshold on raw similarity, cap chunks per record, then order by similarity + boost."""
    per_record: dict[str, int] = {}
    kept = []
    for sim, d in ranked:
        if sim < THRESHOLD:
            break
        if per_record.get(d["ref"], 0) >= MAX_PER_RECORD:
            continue
        per_record[d["ref"]] = per_record.get(d["ref"], 0) + 1
        kept.append((sim, d))
    kept.sort(key=lambda x: x[0] + boost(x[1]), reverse=True)
    return kept[:k]


def cell(sim: float, d: dict) -> str:
    return f"{sim:.3f} {'★ ' if d['new'] else ''}{d['title'][:45]} `{d['label']}`"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Before/after retrieval comparison (read-only).")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()
    k = args.k

    current, web = load_current(), load_web()
    if not web:
        print("No cached web embeddings — run rag/embed_web.py first.", file=sys.stderr)
        return 1
    merged = current + web
    queries = [unit(v) for v in embed_texts(QUESTIONS, task_type="RETRIEVAL_QUERY",
                                            client=gemini_ingest_client())]

    stats = {name: {"official": 0, "records": 0, "new": 0, "top1_up": 0}
             for name in ("before", "after", "rerank")}
    body: list[str] = []
    for question, q in zip(QUESTIONS, queries):
        before = scored(q, current)[:k]
        ranked = scored(q, merged)
        runs = {"before": before, "after": ranked[:k], "rerank": rerank(ranked, k)}
        for name, res in runs.items():
            s = stats[name]
            s["official"] += sum(official(d) for _, d in res)
            s["records"] += len({d["ref"] for _, d in res})
            s["new"] += sum(d["new"] for _, d in res)
            s["top1_up"] += bool(res) and res[0][0] > before[0][0] + 1e-9
        body += [f"## {question}", "", "| # | Before | After | After + rerank |", "|---|---|---|---|"]
        for i in range(k):
            cols = [cell(*runs[n][i]) if i < len(runs[n]) else "—" for n in ("before", "after", "rerank")]
            body.append(f"| {i + 1} | " + " | ".join(cols) + " |")
        body.append("")

    n, total = len(QUESTIONS), len(QUESTIONS) * k
    summary = ["## Summary", "",
               f"| Metric (top-{k}, {n} questions) | Before | After | After + rerank |",
               "|---|---:|---:|---:|"]
    summary.append(f"| Official results (primary or verified) | {stats['before']['official']}/{total} | "
                   f"{stats['after']['official']}/{total} | {stats['rerank']['official']}/{total} |")
    summary.append(f"| Distinct records | {stats['before']['records']} | {stats['after']['records']} | "
                   f"{stats['rerank']['records']} |")
    summary.append(f"| From new web chunks | 0/{total} | {stats['after']['new']}/{total} | "
                   f"{stats['rerank']['new']}/{total} |")
    summary.append(f"| Top-1 similarity above before | — | {stats['after']['top1_up']}/{n} | "
                   f"{stats['rerank']['top1_up']}/{n} |")
    summary += ["", f"_Rerank = raw similarity ≥ {THRESHOLD}, max {MAX_PER_RECORD} chunks per record, "
                "ordered by similarity + authority boost (+0.04 primary/verified, +0.02 secondary/benchmark)._", ""]

    lines = ["# Retrieval eval — before vs after web corpus", "",
             f"_Generated {datetime.now():%Y-%m-%d %H:%M}. Exact cosine. Current rows: {len(current)}; "
             f"with web: {len(merged)} (+{len(web)} chunks). ★ = new web chunk._", ""] + summary + body
    out = WEB_DIR / "EVAL.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(summary))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
