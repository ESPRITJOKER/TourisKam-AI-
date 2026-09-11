"""Apply one or more .sql files to the Supabase Postgres database.

Uses the same connection config as the RAG scripts (rag/config.py).
Runs each file as a single multi-statement batch, autocommit on.

Usage:
    python scripts/apply_sql.py db/schema.sql db/seed.sql
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make rag/ importable regardless of CWD.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "rag"))

from config import pg_connect  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: python scripts/apply_sql.py <file.sql> [<file.sql> ...]",
              file=sys.stderr)
        return 1

    conn = pg_connect()
    conn.autocommit = True
    try:
        for arg in argv:
            path = Path(arg)
            if not path.is_absolute():
                path = ROOT / arg
            if not path.exists():
                print(f"  ! not found: {path}", file=sys.stderr)
                return 2
            sql = path.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
            print(f"  [OK] applied {path.relative_to(ROOT)}")
    finally:
        conn.close()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
