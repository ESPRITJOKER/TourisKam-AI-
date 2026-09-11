"""Shared configuration for TourisCam AI RAG scripts.

Loads environment from the project-root .env and exposes typed getters plus
lazily-constructed Gemini and Supabase clients. Fails loudly with a clear
message when a required secret is missing.
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


def supabase_url() -> str:
    return _require("SUPABASE_URL")


def supabase_service_key() -> str:
    # Service role key — server/scripts only. Never ship to a frontend.
    return _require("SUPABASE_SERVICE_ROLE_KEY")


@lru_cache(maxsize=1)
def gemini_client():
    from google import genai

    return genai.Client(api_key=gemini_api_key())


@lru_cache(maxsize=1)
def supabase_client():
    from supabase import create_client

    return create_client(supabase_url(), supabase_service_key())
