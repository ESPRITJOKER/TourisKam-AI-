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
                config=types.EmbedContentConfig(task_type=task_type),
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
