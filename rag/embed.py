"""Embedding helper — wraps Gemini text-embedding-004.

Used by both ingestion (embed documents) and retrieval (embed queries).
"""
from __future__ import annotations

import time
from typing import List

from config import EMBEDDING_DIM, GEMINI_EMBEDDING_MODEL, gemini_client


def to_pgvector(values: List[float]) -> str:
    """Format an embedding as a pgvector text literal, e.g. '[0.1,0.2,...]'.

    Bind this with an explicit `%s::vector` cast in SQL.
    """
    return "[" + ",".join(repr(float(v)) for v in values) + "]"


def embed_text(text: str, *, task_type: str = "RETRIEVAL_DOCUMENT",
               retries: int = 3) -> List[float]:
    """Return a 768-d embedding for `text`.

    task_type: use RETRIEVAL_DOCUMENT when embedding knowledge chunks,
    RETRIEVAL_QUERY when embedding a user query (improves match quality).
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot embed empty text.")

    client = gemini_client()
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            from google.genai import types

            resp = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=text,
                # gemini-embedding-001 defaults to 3072 dims but supports
                # Matryoshka truncation; request 768 to match vector(768).
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIM,
                ),
            )
            values = resp.embeddings[0].values
            if len(values) != EMBEDDING_DIM:
                raise RuntimeError(
                    f"Embedding dim {len(values)} != expected {EMBEDDING_DIM}. "
                    f"Check GEMINI_EMBEDDING_MODEL and db schema vector() size."
                )
            return list(values)
        except Exception as e:  # noqa: BLE001 - surface after retries
            last_err = e
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))  # simple backoff
    raise RuntimeError(f"Embedding failed after {retries} attempts: {last_err}")


def embed_texts(texts: List[str], *, task_type: str = "RETRIEVAL_DOCUMENT",
                batch_size: int = 100, retries: int = 4, client=None) -> List[List[float]]:
    """Return 768-d embeddings for many texts, one API request per `batch_size`.

    Note: the free-tier daily quota counts every text, not every request.
    Bulk jobs should pass `client=config.gemini_ingest_client()` so they never
    consume the live bot's quota. Rate-limit errors back off longer than
    transient ones; a daily-quota error stops immediately.
    """
    from google.genai import types

    client = client or gemini_client()
    out: List[List[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = [(t or "").strip() for t in texts[start:start + batch_size]]
        if not all(batch):
            raise ValueError(f"Cannot embed empty text (batch starting at {start}).")
        for attempt in range(retries):
            try:
                resp = client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=EMBEDDING_DIM,
                    ),
                )
                vectors = [list(e.values) for e in resp.embeddings]
                if len(vectors) != len(batch) or any(len(v) != EMBEDDING_DIM for v in vectors):
                    raise RuntimeError("Embedding count/dimension mismatch in batch response.")
                out.extend(vectors)
                break
            except Exception as e:  # noqa: BLE001 - surface after retries
                if "PerDay" in str(e):  # daily quota (counts every item): retrying can't succeed
                    raise RuntimeError(f"Daily embedding quota exhausted at item {start}: {e}") from e
                if attempt == retries - 1:
                    raise RuntimeError(f"Batch embedding failed at item {start}: {e}") from e
                rate_limited = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                time.sleep(30 * (attempt + 1) if rate_limited else 2 * (attempt + 1))
    return out
