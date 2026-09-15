"""Shared helpers for the TourisCam AI web scrapers.

Polite HTTP (identifying User-Agent, per-host throttle, retries, on-disk raw
cache), HTML -> text blocks, spam and ID-number filters, region normalization,
and a validated JSONL writer. Records follow the rag_records.jsonl schema plus
the provenance fields required by dataset/touriscam_dataset_final/RAG_POLICY.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BATCH = "web_2026-09-15"
OUT_DIR = ROOT / "dataset" / "web_scrape_2026-09-15"
RAW_DIR = OUT_DIR / "raw"
TODAY = date.today().isoformat()
USER_AGENT = ("TourisCamAI-research/0.1 (Cameroon tourism assistant; "
              "+https://github.com/ESPRITJOKER/TourisKam-AI-)")

VALID_STATUS = {"verified", "benchmark", "estimated", "unverified", "unavailable"}
VALID_AUTHORITY = {"primary", "secondary", "third_party"}
REQUIRED = ("id", "title", "content", "type", "language", "source_id",
            "source_url", "authority_level", "license", "verification_status")
MIN_CHARS = 80

# New source registry entries (continues dataset/touriscam_dataset_final/sources.csv).
SOURCES = {
    "SRC-026": dict(publisher="Wikivoyage (English)", title="Cameroon travel guides",
                    scope="Community travel guide pages for Cameroon",
                    url="https://en.wikivoyage.org/wiki/Cameroon",
                    authority_level="third_party", license="CC BY-SA 4.0"),
    "SRC-027": dict(publisher="Wikivoyage (français)", title="Guides de voyage Cameroun",
                    scope="Pages communautaires de voyage sur le Cameroun",
                    url="https://fr.wikivoyage.org/wiki/Cameroun",
                    authority_level="third_party", license="CC BY-SA 4.0"),
    "SRC-028": dict(publisher="OpenStreetMap contributors", title="Cameroon tourism POIs",
                    scope="Hotels, attractions, museums, heritage and protected areas via Overpass API",
                    url="https://www.openstreetmap.org/relation/192830",
                    authority_level="secondary", license="ODbL 1.0"),
    "SRC-029": dict(publisher="UK FCDO", title="Foreign travel advice: Cameroon",
                    scope="Official UK government safety, entry and health advice",
                    url="https://www.gov.uk/foreign-travel-advice/cameroon",
                    authority_level="primary", license="Open Government Licence v3.0"),
    "SRC-030": dict(publisher="TourisCam AI team", title="Kribi-to-West amenities verification dossier",
                    scope="Hand-checked prices/phones with per-row confidence labels",
                    url="dataset/touriscam_kribi_to_west_staging.csv",
                    authority_level="third_party", license="project-internal"),
    "SRC-031": dict(publisher="MINTOUL", title="mintoul.gov.cm website crawl",
                    scope="Official ministry pages, news, guides and hotel entries (spam filtered)",
                    url="https://mintoul.gov.cm/",
                    authority_level="primary", license="Official public information"),
}


# ---------------------------------------------------------------- HTTP ----
class Fetcher:
    """Throttled, retrying HTTP client with an on-disk cache of raw responses."""

    def __init__(self, min_interval: float = 1.0, timeout: float = 90.0):
        self.client = httpx.Client(headers={"User-Agent": USER_AGENT},
                                   timeout=timeout, follow_redirects=True)
        self.min_interval = min_interval
        self._last: dict[str, float] = {}

    def _throttle(self, host: str) -> None:
        wait = self._last.get(host, 0.0) + self.min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def fetch(self, url: str, *, params: dict | None = None, data: dict | None = None,
              retries: int = 3, use_cache: bool = True) -> str | None:
        """GET (POST when `data` is given) and return the body; None on failure."""
        key = f"{url}?{urlencode(sorted((params or {}).items()))}|{urlencode(sorted((data or {}).items()))}"
        host = urlsplit(url).netloc
        path = RAW_DIR / host / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".txt")
        if use_cache and path.exists():
            return path.read_text(encoding="utf-8")

        err = ""
        for attempt in range(retries):
            self._throttle(host)
            try:
                r = (self.client.post(url, data=data) if data is not None
                     else self.client.get(url, params=params))
            except httpx.HTTPError as e:
                err = f"{type(e).__name__}: {e}"
            else:
                if r.status_code == 200:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(r.text, encoding="utf-8")
                    return r.text
                err = f"HTTP {r.status_code}"
                if r.status_code < 500 and r.status_code != 429:
                    break  # client error: retrying won't help
            if attempt < retries - 1:
                time.sleep((2 ** attempt) * (10 if err == "HTTP 429" else 2))
        print(f"  ! fetch failed ({err}): {url} {params or ''}", file=sys.stderr)
        return None

    def json(self, url: str, **kw):
        text = self.fetch(url, **kw)
        return json.loads(text) if text is not None else None


# ---------------------------------------------------------------- text ----
_WS = re.compile(r"\s+")


def clean_text(s: str | None) -> str:
    return _WS.sub(" ", s or "").strip()


DEFAULT_DROP = (
    "script", "style", "noscript", "form", "nav", "header", "footer", "figure",
    ".mw-editsection", "sup.reference", ".reference", ".mw-references-wrap",
    ".navbox", ".noprint", ".mw-empty-elt", ".thumb", ".mw-cite-backlink",
    ".listing-metadata", ".listing-metadata-items",
    ".listing-marker", "a.mw-kartographer-maplink.mw-kartographer-autostyled",  # map pin numbers
)


def html_to_blocks(html: str, drop: tuple[str, ...] = (), tables: bool = False) -> list[tuple[str, str]]:
    """Flatten HTML into ordered (tag, text) blocks: headings, paragraphs, list items.

    tables=True also emits table rows as "cell | cell" lines and, if nothing else
    matched (e.g. text in bare <div>s), falls back to the whole text as one block.
    """
    soup = BeautifulSoup(html, "html.parser")
    for sel in DEFAULT_DROP + tuple(drop):
        for el in soup.select(sel):
            el.decompose()
    blocks: list[tuple[str, str]] = []
    tags = ["h1", "h2", "h3", "h4", "p", "li", "dt", "dd"] + (["tr"] if tables else [])
    for el in soup.find_all(tags):
        if el.name in ("p", "dt", "dd") and el.find_parent("li"):
            continue  # already included in the enclosing list item's text
        if tables and el.name != "tr" and el.find_parent(["td", "th"]):
            continue  # already included in its table row
        if el.name == "tr":
            text = " | ".join(clean_text(c.get_text(" ", strip=True))
                              for c in el.find_all(["td", "th"]) if c.get_text(strip=True))
        elif el.name == "li":  # own text only; nested lists yield their own items
            text = " ".join(
                ch.get_text(" ", strip=True) if hasattr(ch, "get_text") else str(ch)
                for ch in el.children if getattr(ch, "name", None) not in ("ul", "ol")
            )
        else:
            text = el.get_text(" ", strip=True)
        text = clean_text(text)
        if text:
            blocks.append((el.name, text))
    if tables and not blocks:
        text = clean_text(soup.get_text(" "))
        if text:
            blocks.append(("p", text))
    return blocks


def split_sections(blocks: list[tuple[str, str]], intro: str) -> list[tuple[str, str]]:
    """Group blocks under their h2 heading; h3/h4 stay inline as label lines."""
    out: list[tuple[str, str]] = []
    current, buf = intro, []
    for tag, text in blocks:
        if tag in ("h1", "h2"):
            if buf:
                out.append((current, "\n\n".join(buf)))
            current, buf = text, []
        elif tag in ("h3", "h4"):
            buf.append(f"{text}:")
        else:
            buf.append(text)
    if buf:
        out.append((current, "\n\n".join(buf)))
    return out


def merge_short_sections(sections: list[tuple[str, str]], min_chars: int = 300) -> list[tuple[str, str]]:
    """Fold short sections into their neighbour so no useful fragment is dropped."""
    out: list[tuple[str, str]] = []
    for title, body in sections:
        if out and (len(body) < min_chars or len(out[-1][1]) < min_chars):
            prev_title, prev_body = out[-1]
            out[-1] = (prev_title, f"{prev_body}\n\n{title}:\n\n{body}")
        else:
            out.append((title, body))
    return out


# --------------------------------------------------------------- filters ----
# mintoul.gov.cm carries injected casino / "ESA letter" SEO spam pages.
SPAM_RE = re.compile(
    r"\b(casinos?|casinò|kasinon?|kasyn\w*|slots?|slot machines?|roulette|jackpots?|"
    r"betting|bookmakers?|1win|roobet|free spins|gambl\w*|gokken|spielautomat\w*|"
    r"speelautomat\w*|spelautomat\w*|esa (?:approval )?letters?|emotional support animal|"
    r"jocuri(?:lor)? de noroc|cazino\w*|cazinou\w*|p[ăa]c[ăa]nele)\b",
    re.I,
)


def spam_hits(text: str) -> int:
    return len(SPAM_RE.findall(text or ""))


def is_spam(text: str, min_hits: int = 3) -> bool:
    return spam_hits(text) >= min_hits


# National ID (CNI) numbers must never be stored (RAG_POLICY.md). Keyword-anchored
# and digit-bearing, so phrases like "carte nationale d'identité valide" survive.
ID_RE = re.compile(
    r"(?i)\b(?:n[°o]\.?\s*)?(?:CNI|C\.N\.I\.?|carte nationale d['’]identit[ée]|"
    r"pi[eè]ce d['’]identit[ée]|national id(?:entity)?(?: card)?)"
    r"\s*(?:n[°o]\.?|num[ée]ro|number|no\.?)?\s*[:#-]?\s*[A-Z]{0,3}\d[\d /.-]{5,}\d"
)


def scrub_ids(text: str) -> tuple[str, int]:
    return ID_RE.subn("[ID number removed]", text)


_FR = {"le", "la", "les", "des", "du", "et", "est", "une", "pour", "dans", "sur",
       "avec", "au", "aux", "que", "qui", "vous", "sont", "par", "pas"}
_EN = {"the", "and", "is", "of", "to", "in", "for", "with", "are", "this",
       "that", "from", "at", "you", "by", "it", "be", "or"}


_WORD = re.compile(r"[a-zàâçéèêëîïôûùüÿœ']+")


def stopword_ratio(text: str) -> float:
    """Share of words that are common FR/EN stopwords (~20% in real FR/EN prose)."""
    words = _WORD.findall((text or "").lower())
    return sum(w in _FR or w in _EN for w in words) / len(words) if words else 0.0


def detect_language(text: str) -> str | None:
    words = _WORD.findall((text or "").lower())
    fr = sum(w in _FR for w in words)
    en = sum(w in _EN for w in words)
    if fr + en < 3:
        return None
    return "fr" if fr > en else "en"


# Canonical region names match the existing dataset ("South-West", "Far North"...).
_REGION_OVERRIDES = {
    "coastal cameroon": "Littoral / South-West",
    "northern cameroon": "North / Far North",
    "northwest highlands": "North-West",
    "south cameroon plateau": "Centre / South / East",
}
_REGION_PATTERNS = [  # compound names before their prefixes
    (r"extr[êe]me[- ]nord|far[- ]north", "Far North"),
    (r"nord[- ]ouest|north[- ]?west", "North-West"),
    (r"sud[- ]ouest|south[- ]?west", "South-West"),
    (r"adamaoua|adamawa", "Adamawa"),
    (r"littoral", "Littoral"),
    (r"\bcentre\b|\bcenter\b", "Centre"),
    (r"\best\b|\beast\b", "East"),
    (r"\bnord\b|\bnorth\b", "North"),
    (r"\bouest\b|\bwest\b", "West"),
    (r"\bsud\b|\bsouth\b", "South"),
]


def normalize_region(name: str | None) -> str | None:
    """Map a French/English region label to the dataset's canonical name."""
    if not name:
        return None
    low = name.lower().strip()
    if low in _REGION_OVERRIDES:
        return _REGION_OVERRIDES[low]
    for pat, region in _REGION_PATTERNS:
        if re.search(pat, low):
            return region
    return None


# --------------------------------------------------------------- records ----
def validate(rec: dict) -> str | None:
    """Return a drop reason, or None if the record is acceptable."""
    for k in REQUIRED:
        if not rec.get(k):
            return f"missing {k}"
    if rec["verification_status"] not in VALID_STATUS:
        return "bad verification_status"
    if rec["authority_level"] not in VALID_AUTHORITY:
        return "bad authority_level"
    if rec["language"] not in ("en", "fr"):
        return "bad language"
    if len(rec["content"]) < MIN_CHARS:
        return "too short"
    return None  # spam filtering is source-specific (mintoul.py): hotels legitimately list casinos


def finalize(source_key: str, records: list[dict], stats: Counter) -> list[dict]:
    """Scrub ID numbers, validate, de-duplicate, and write OUT_DIR/<source_key>.jsonl."""
    out: list[dict] = []
    seen_ids: set[str] = set()
    seen_content: set[str] = set()
    for rec in records:
        rec["content"], n = scrub_ids(rec.get("content") or "")
        if n:
            stats["scrubbed: ID numbers"] += n
        rec.setdefault("retrieved_at", TODAY)
        rec["source_key"] = source_key
        rec["batch"] = BATCH
        reason = validate(rec)
        if reason:
            stats[f"dropped: {reason}"] += 1
            continue
        digest = hashlib.sha1(clean_text(rec["content"]).lower().encode("utf-8")).hexdigest()
        if rec["id"] in seen_ids or digest in seen_content:
            stats["dropped: duplicate"] += 1
            continue
        seen_ids.add(rec["id"])
        seen_content.add(digest)
        out.append(rec)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / f"{source_key}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    stats["kept"] = len(out)
    return out
