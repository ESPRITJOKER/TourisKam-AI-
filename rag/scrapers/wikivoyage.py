"""Wikivoyage (EN + FR) Cameroon travel guides -> one record per page section.

Community-written (CC BY-SA 4.0), so every record is labeled third_party /
unverified and cites the exact page revision (oldid) for attribution.
"""
from __future__ import annotations

from collections import Counter, deque
from urllib.parse import quote

from common import Fetcher, html_to_blocks, merge_short_sections, normalize_region, split_sections

SITES = [  # (language, host, root category, source_id)
    ("en", "en.wikivoyage.org", "Category:Cameroon", "SRC-026"),
    ("fr", "fr.wikivoyage.org", "Catégorie:Cameroun", "SRC-027"),
]
INTRO = {"en": "Overview", "fr": "Présentation"}
SKIP_SECTIONS = {
    "references", "external links", "notes", "see also",
    "références", "notes et références", "liens externes", "voir aussi", "bibliographie",
}


def walk_category(f: Fetcher, api: str, root: str) -> dict[str, str | None]:
    """Breadth-first category walk -> {page title: region inferred from categories}."""
    pages: dict[str, str | None] = {}
    seen: set[str] = set()
    queue = deque([(root, None)])
    while queue:
        cat, parent_region = queue.popleft()
        if cat in seen:
            continue
        seen.add(cat)
        region = normalize_region(cat.split(":", 1)[-1]) or parent_region
        params = {"action": "query", "list": "categorymembers", "cmtitle": cat,
                  "cmlimit": 500, "format": "json"}
        while True:
            data = f.json(api, params=params)
            if not data:
                break
            for m in data.get("query", {}).get("categorymembers", []):
                if m["ns"] == 14:
                    queue.append((m["title"], region))
                elif m["ns"] == 0 and not pages.get(m["title"]):
                    pages[m["title"]] = region
            if "continue" not in data:
                break
            params = {**params, **data["continue"]}
    return pages


def scrape(f: Fetcher, limit: int | None, stats: Counter) -> list[dict]:
    records: list[dict] = []
    for lang, host, root, source_id in SITES:
        api = f"https://{host}/w/api.php"
        pages = walk_category(f, api, root)
        titles = sorted(pages)[:limit] if limit else sorted(pages)
        stats[f"pages: {host}"] = len(titles)
        for title in titles:
            data = f.json(api, params={"action": "parse", "page": title, "prop": "text|revid",
                                       "format": "json", "formatversion": 2, "redirects": 1,
                                       "disableeditsection": 1})
            if not data or "parse" not in data:
                stats["dropped: parse failed"] += 1
                continue
            p = data["parse"]
            url = (f"https://{host}/w/index.php?title="
                   f"{quote(p['title'].replace(' ', '_'))}&oldid={p['revid']}")
            sections = [(s, b) for s, b in split_sections(html_to_blocks(p["text"]), INTRO[lang])
                        if s.lower() not in SKIP_SECTIONS]
            for n, (section, body) in enumerate(merge_short_sections(sections)):
                records.append({
                    "id": f"WV-{lang.upper()}-{p['pageid']}-{n:02d}",
                    "title": f"{p['title']} — {section}",
                    "type": "travel_guide",
                    "content": body,
                    "language": lang,
                    "location": p["title"],
                    "region": pages[title],
                    "source_id": source_id,
                    "source_url": url,
                    "authority_level": "third_party",
                    "license": "CC BY-SA 4.0",
                    "verification_status": "unverified",
                })
    return records
