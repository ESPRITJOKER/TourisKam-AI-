"""TourisCam AI — semantic retrieval over the knowledge base.

Embeds a user query with Gemini (RETRIEVAL_QUERY) and calls the Supabase
`match_documents` RPC to fetch the most relevant verified chunks.

Usage (manual test):
    python rag/retrieve.py "what can I see in Limbe?"
    python rag/retrieve.py --answer "que voir a Kribi ?"
"""
from __future__ import annotations

import argparse
import sys
from typing import List, TypedDict

from config import pg_connect
from embed import embed_text, to_pgvector


class Match(TypedDict):
    id: str
    title: str
    content: str
    source: str
    source_type: str
    verification_status: str
    similarity: float


def retrieve(query: str, *, match_count: int = 5,
             similarity_threshold: float = 0.5) -> List[Match]:
    """Return the top matching knowledge chunks for `query`.

    Returns [] when nothing clears the threshold — the caller must then tell
    the user the information could not be verified (never hallucinate).
    """
    query = (query or "").strip()
    if not query:
        return []
    try:
        emb = embed_text(query, task_type="RETRIEVAL_QUERY")
    except Exception as e:  # noqa: BLE001
        print(f"[retrieve] embedding error: {e}", file=sys.stderr)
        return []

    try:
        conn = pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, title, content, source, source_type, "
                    "       verification_status, similarity "
                    "from match_documents(%s::vector, %s, %s)",
                    (to_pgvector(emb), match_count, similarity_threshold),
                )
                cols = [c.name for c in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            return rows
        finally:
            conn.close()
    except Exception as e:  # noqa: BLE001
        print(f"[retrieve] match_documents error: {e}", file=sys.stderr)
        return []


def format_context(matches: List[Match]) -> str:
    """Render matches into a compact, citeable context block for the LLM."""
    if not matches:
        return "(no matching verified information found)"
    lines = []
    for i, m in enumerate(matches, 1):
        lines.append(
            f"[{i}] ({m['verification_status']}; source: {m.get('source') or 'n/a'}) "
            f"{m['title']}: {m['content']}"
        )
    return "\n".join(lines)


def _main() -> int:
    ap = argparse.ArgumentParser(description="Retrieve knowledge chunks.")
    ap.add_argument("query", help="user query")
    ap.add_argument("--answer", action="store_true",
                    help="also generate a guardrailed answer with Gemini")
    ap.add_argument("-k", type=int, default=5, help="match_count")
    ap.add_argument("-t", type=float, default=0.5, help="similarity_threshold")
    args = ap.parse_args()

    matches = retrieve(args.query, match_count=args.k, similarity_threshold=args.t)
    print(f"\n{len(matches)} match(es):\n")
    for m in matches:
        print(f"  {m['similarity']:.3f}  [{m['verification_status']}]  {m['title']}")

    if args.answer:
        from prompt import answer_query  # local import to avoid cycle at module load
        print("\n--- ANSWER ---\n")
        print(answer_query(args.query, matches))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
