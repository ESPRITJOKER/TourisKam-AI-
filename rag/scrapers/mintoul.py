"""mintoul.gov.cm (Ministry of Tourism and Leisure) -> one record per official page.

The site carries injected casino / "ESA letter" spam posts and some dead links,
so we crawl from known-good seeds (WordPress REST listings with spam titles
skipped + curated sections), extract only the `.entry-content` body (never the
menus), and drop spam, forms, stubs and pages in other languages. Guide pages
publish national ID numbers; common.finalize() scrubs them.
"""
from __future__ import annotations

import hashlib
import html
import re
from collections import Counter, deque
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from common import (Fetcher, clean_text, detect_language, html_to_blocks, is_spam,
                    normalize_region, stopword_ratio)

BASE = "https://mintoul.gov.cm"
API = f"{BASE}/wp-json/wp/v2"
MAX_PAGES = 250
MAX_DEPTH = 3
SEED_PATHS = [
    "/cameroun-en-decouverte/", "/cameroun-en-decouverte/sites-touristiques/",
    "/venir-au-cameroun/", "/infos-pratiques/", "/regions/", "/visiter/",
    "/tours/ecotourisme/", "/tours/tourisme-balneaires/",
    "/tourisme/sports-tourism/", "/tourisme/tourisme-des-affaires/",
    "/statut-guide/guides-touristiques/", "/statut-guide/guides-touristiques/page/2/",
    "/categorie-loisir/hotels/", "/categorie-loisir/etablissements-de-loisirs/",
]
SKIP_SEGMENTS = {
    "wp-admin", "wp-content", "wp-json", "wp-login.php", "author", "category", "tag",
    "feed", "download", "download-category", "comments", "concours-ia-jmt-2026",
    "tableau-de-bord-de-lutilisateur", "test", "test-map", "sample-page",
    "nous-contacter", "contactus", "a-propos-de-nous", "organigramme",
}
# Injected spam can dodge keyword filters (e.g. Romanian casino copy), so posts and
# generic pages must mention something tourism/Cameroon-related to be kept.
RELEVANT = re.compile(
    r"camer|touris|mintoul|parc|park|lob[ée]k[ée]|faune|wildlife|patrimoine|heritage|"
    r"cultur|loisir|h[ôo]tel|visa|voyage|travel|ambassade|embassy", re.I)
PLACEHOLDER_TITLES = {"sample page", "hello world!", "test", "test map"}
FILE_EXT = re.compile(r"\.(pdf|jpe?g|png|gif|webp|svg|zip|docx?|xlsx?|pptx?|mp4|mp3)$", re.I)
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF☀-➿️]")


def normalize_url(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.netloc not in ("mintoul.gov.cm", "www.mintoul.gov.cm"):
        return None
    path = parts.path or "/"
    if not path.endswith("/") and not FILE_EXT.search(path):
        path += "/"
    return f"{BASE}{path}"


def allowed(url: str | None, skip: set[str]) -> bool:
    if not url or url in skip or FILE_EXT.search(url):
        return False
    first = urlsplit(url).path.strip("/").split("/")[0]
    return first not in SKIP_SEGMENTS


def classify(url: str) -> tuple[str, str]:
    """-> (record type, verification_status) from the URL section."""
    first = urlsplit(url).path.strip("/").split("/")[0]
    if first in ("guides-touristiques", "statut-guide", "guides-animateurs"):
        return "guide", "unverified"        # directory entry, not current availability
    if first in ("hotels", "loisirs", "categorie-loisir", "14ieme-conference-ministerielle-yde-mars"):
        return "hotel", "unverified"        # listed ≠ currently open/available
    if first in ("infos-pratiques", "venir-au-cameroun"):
        return "practical_information", "verified"
    if first in ("tours", "tourisme", "destination", "regions", "visiter", "site", "ecotourisme"):
        return "attraction", "verified"
    if first == "cameroun-en-decouverte":
        return "destination", "verified"
    return "official_page", "verified"


def rest_links(f: Fetcher, rest_base: str, stats: Counter, skip: set[str]) -> list[str]:
    """Links from a WordPress REST listing; spam-titled entries go to `skip`."""
    links, page = [], 1
    while True:
        data = f.json(f"{API}/{rest_base}", params={"per_page": 100, "page": page, "_fields": "link,title"})
        if not data:
            break
        for item in data:
            url = normalize_url(item["link"])
            title = html.unescape(item["title"]["rendered"])
            if is_spam(title, min_hits=1):
                stats["skipped: spam title"] += 1
                if url:
                    skip.add(url)
            elif url:
                links.append(url)
        if len(data) < 100:
            break
        page += 1
    return links


def scrape(f: Fetcher, limit: int | None, stats: Counter) -> list[dict]:
    skip: set[str] = set()
    seeds = [BASE + p for p in SEED_PATHS]
    for rest_base in ("pages", "guides", "hotels", "loisirs"):
        seeds += rest_links(f, rest_base, stats, skip)
    post_urls = set(rest_links(f, "posts", stats, skip))  # news posts: spam-prone, stricter checks
    seeds += sorted(post_urls)

    queue = deque((u, 0) for u in seeds)
    seen: set[str] = set()
    records: list[dict] = []
    max_pages = limit or MAX_PAGES
    while queue and len(seen) < max_pages:
        url, depth = queue.popleft()
        if url in seen or not allowed(url, skip):
            continue
        seen.add(url)
        page = f.fetch(url, retries=2)
        if page is None:
            stats["dropped: fetch failed / 404"] += 1
            continue
        soup = BeautifulSoup(page, "html.parser")
        page_title = clean_text(soup.title.get_text()) if soup.title else ""
        if "Page non trouvée" in page_title:
            stats["dropped: 404 page"] += 1
            continue

        if depth < MAX_DEPTH:
            for a in (soup.select_one("main") or soup).select("a[href]"):
                nxt = normalize_url(urljoin(url, a["href"]))
                if nxt and nxt not in seen:
                    queue.append((nxt, depth + 1))

        body = soup.select_one(".entry-content")
        if body is None:
            stats["dropped: no content container"] += 1
            continue
        text = EMOJI.sub("", "\n\n".join(t for _, t in html_to_blocks(str(body), tables=True)))
        text = re.sub(r"[ \t]{2,}", " ", text).strip()
        if is_spam(text):
            stats["dropped: spam"] += 1
            continue
        # Short official pages (embassy addresses, lists) have too few stopwords to
        # detect; the site is French, so default to fr — except for spam-prone posts.
        lang = detect_language(text) or (None if url in post_urls else "fr")
        if url in post_urls and stopword_ratio(text) < 0.08:
            lang = None  # e.g. Romanian casino copy that shares a few FR stopwords ("la")
        if lang is None:
            stats["dropped: post language not fr/en"] += 1
            continue

        rtype, status = classify(url)
        path = urlsplit(url).path
        title = page_title.split(" – ")[0].strip() or path
        if title.lower() in PLACEHOLDER_TITLES:
            stats["dropped: placeholder page"] += 1
            continue
        if url in post_urls and not RELEVANT.search(f"{title}\n{text}"):
            stats["dropped: off-topic (no tourism/Cameroon terms)"] += 1
            continue
        modified = soup.select_one('meta[property="article:modified_time"]')
        slug = path.strip("/").split("/")
        records.append({
            "id": "MTL-" + hashlib.sha1(path.encode("utf-8")).hexdigest()[:10],
            "title": title,
            "type": rtype,
            "content": text,
            "language": lang,
            "location": None,
            "region": normalize_region(slug[-1].replace("-", " ")) if slug[0] == "destination" else None,
            "source_id": "SRC-031",
            "source_url": url,
            "authority_level": "primary",
            "license": "Official public information",
            "verification_status": status,
            "last_verified": modified["content"][:10] if modified and modified.get("content") else None,
        })
    stats["pages crawled"] = len(seen)
    return records
