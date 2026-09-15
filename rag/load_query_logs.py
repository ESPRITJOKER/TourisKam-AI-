"""TourisCam AI — load the synthetic WhatsApp query logs into demo_query_logs.

Reads dataset/whatsapp_visitor_query_logs.csv (6,200 simulated interactions for
the MINTOUL dashboard demo), validates every row, and bulk-loads it into the
`demo_query_logs` table defined in db/demo_query_logs.sql.

This is analytics data, NOT RAG knowledge: no embeddings, nothing written to
knowledge_documents. Kept apart from query_events so synthetic rows never mix
with real bot traffic.

Idempotent: each run ensures the table exists, truncates it, and reloads.

Usage:
    python rag/load_query_logs.py --dry-run
    python rag/load_query_logs.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from config import ROOT, pg_connect

CSV_PATH = ROOT / "dataset" / "whatsapp_visitor_query_logs.csv"
DDL_PATH = ROOT / "db" / "demo_query_logs.sql"

# Cameroon is WAT (UTC+1) year-round, no DST — a fixed offset avoids needing
# the tzdata package on Windows.
WAT = timezone(timedelta(hours=1))

LANGUAGE_MAP = {"French": "fr", "English": "en", "Pidgin": "pidgin"}
BOOL_MAP = {"True": True, "False": False}
ALLOWED = {
    "channel": {"text", "voice_note"},
    "visitor_type": {"domestic", "foreign"},
    "query_type": {"pricing", "opening_hours", "directions", "cultural_info",
                   "booking_interest", "transport_fare", "emergency_sos",
                   "general_chat"},
    "sentiment": {"positive", "neutral", "negative"},
}
COLUMNS = ("query_id", "occurred_at", "session_id", "visitor_id", "channel",
           "language", "visitor_type", "visitor_origin", "query_type",
           "site_referenced", "region_referenced", "sentiment",
           "response_time_seconds", "resolved", "is_emergency")


def parse_row(line_no: int, r: dict) -> tuple:
    """Validate + convert one CSV row; raise ValueError with the line number."""
    def fail(msg: str):
        raise ValueError(f"line {line_no} ({r.get('query_id')}): {msg}")

    for col, allowed in ALLOWED.items():
        if r[col] not in allowed:
            fail(f"unexpected {col}={r[col]!r}")
    if r["language"] not in LANGUAGE_MAP:
        fail(f"unexpected language={r['language']!r}")
    for col in ("resolved", "is_emergency"):
        if r[col] not in BOOL_MAP:
            fail(f"unexpected {col}={r[col]!r}")
    if not r["query_id"] or not r["session_id"] or not r["visitor_id"]:
        fail("missing id")
    try:
        occurred = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M").replace(tzinfo=WAT)
        rt = float(r["response_time_seconds"])
    except ValueError as e:
        fail(str(e))

    return (
        r["query_id"], occurred, r["session_id"], r["visitor_id"], r["channel"],
        LANGUAGE_MAP[r["language"]], r["visitor_type"], r["visitor_origin"] or None,
        r["query_type"], r["site_referenced"] or None, r["region_referenced"] or None,
        r["sentiment"], rt, BOOL_MAP[r["resolved"]], BOOL_MAP[r["is_emergency"]],
    )


def load_rows() -> list[tuple]:
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = (set(COLUMNS) - {"occurred_at"}) | {"timestamp"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {sorted(missing)}")
        rows = [parse_row(i, r) for i, r in enumerate(reader, start=2)]
    ids = Counter(r[0] for r in rows)
    dups = [k for k, n in ids.items() if n > 1]
    if dups:
        raise ValueError(f"{len(dups)} duplicate query_id(s): {dups[:5]}")
    return rows


def profile(rows: list[tuple]) -> None:
    col = {name: i for i, name in enumerate(COLUMNS)}
    print(f"Loaded {len(rows)} rows from {CSV_PATH.name}")
    print(f"  occurred_at: {min(r[1] for r in rows)} -> {max(r[1] for r in rows)}")
    for name in ("language", "channel", "visitor_type", "query_type", "sentiment"):
        print(f"  {name}: {dict(Counter(r[col[name]] for r in rows))}")
    print(f"  is_emergency: {sum(r[col['is_emergency']] for r in rows)}"
          f" | unresolved: {sum(not r[col['resolved']] for r in rows)}"
          f" | distinct sites: {len({r[col['site_referenced']] for r in rows} - {None})}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Load synthetic query logs into Supabase.")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse + validate only; no DB writes")
    args = ap.parse_args()

    try:
        rows = load_rows()
    except ValueError as e:
        print(f"  ! validation failed: {e}", file=sys.stderr)
        return 2
    profile(rows)

    if args.dry_run:
        print("Dry-run: no DB writes.")
        return 0

    from psycopg2.extras import execute_values

    insert_sql = f"insert into demo_query_logs ({', '.join(COLUMNS)}) values %s"
    conn = pg_connect()
    try:
        with conn.cursor() as cur:  # single transaction: DDL + truncate + reload
            cur.execute(DDL_PATH.read_text(encoding="utf-8"))
            cur.execute("truncate demo_query_logs")
            execute_values(cur, insert_sql, rows, page_size=1000)
            cur.execute("select count(*) from demo_query_logs")
            n = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"\nDone: {n} row(s) in demo_query_logs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
