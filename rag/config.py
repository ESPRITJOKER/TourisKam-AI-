"""Shared configuration for TourisCam AI RAG scripts.

Loads environment from the project-root .env and exposes typed getters plus
a Gemini client and a direct PostgreSQL (Supabase) connection factory.

We connect to Supabase over a direct Postgres connection (psycopg2) rather than
the REST client: it's the right tool for server-side ingestion/queries and it
uses the DB connection string only (no service-role key needed in scripts).
Secrets live only in .env — never commit them.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Project root is the parent of this file's directory (rag/ -> repo root).
ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"

load_dotenv(ROOT / ".env")

# --- Models / constants ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
EMBEDDING_DIM = 768  # text-embedding-004 default; must match db/schema.sql vector(768)


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return val


def gemini_api_key() -> str:
    return _require("GEMINI_API_KEY")


@lru_cache(maxsize=1)
def gemini_client():
    from google import genai

    return genai.Client(api_key=gemini_api_key())


def _db_kwargs() -> dict:
    """Build psycopg2 connection kwargs.

    Prefer a full DSN (SUPABASE_DB_URL) if given; otherwise assemble from
    discrete parts. Discrete parts avoid URL-encoding pitfalls when the DB
    password contains characters like % or *.
    """
    dsn = os.getenv("SUPABASE_DB_URL")
    if dsn:
        return {"dsn": dsn}
    return {
        "host": _require("SUPABASE_DB_HOST"),
        "port": os.getenv("SUPABASE_DB_PORT", "5432"),
        "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": _require("SUPABASE_DB_USER"),
        "password": _require("SUPABASE_DB_PASSWORD"),
        "sslmode": os.getenv("SUPABASE_DB_SSLMODE", "require"),  # Supabase requires SSL
        "connect_timeout": int(os.getenv("SUPABASE_DB_TIMEOUT", "15")),
    }


def pg_connect():
    """Open a new psycopg2 connection to Supabase Postgres."""
    import psycopg2

    kw = _db_kwargs()
    if "dsn" in kw:
        return psycopg2.connect(kw["dsn"])
    return psycopg2.connect(**kw)
