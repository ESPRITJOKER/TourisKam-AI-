"""UK FCDO foreign travel advice for Cameroon -> one record per subsection.

Official UK government advice (Open Government Licence v3.0), read from the
GOV.UK content API. It reflects the UK government's view of risk, so titles
name the publisher explicitly.
"""
from __future__ import annotations

from collections import Counter

from common import (Fetcher, clean_text, html_to_blocks, merge_short_sections,
                    normalize_region, split_sections)

API = "https://www.gov.uk/api/content/foreign-travel-advice/cameroon"
WEB = "https://www.gov.uk/foreign-travel-advice/cameroon"


def scrape(f: Fetcher, limit: int | None, stats: Counter) -> list[dict]:
    data = f.json(API)
    if not data:
        raise RuntimeError("GOV.UK content API unavailable")
    updated = (data.get("public_updated_at") or "")[:10] or None
    parts = data.get("details", {}).get("parts", [])
    if limit:
        parts = parts[:limit]

    records: list[dict] = []
    for part in parts:
        body = part.get("body") or ""
        if isinstance(body, list):  # newer API shape: [{content_type, content}]
            body = "".join(x.get("content", "") for x in body if x.get("content_type") == "text/html")
        part_title = clean_text(part.get("title"))
        sections = merge_short_sections(split_sections(html_to_blocks(body), part_title))
        for n, (section, text) in enumerate(sections):
            label = part_title if section == part_title else f"{part_title} — {section}"
            records.append({
                "id": f"FCDO-{part.get('slug')}-{n:02d}",
                "title": f"UK travel advice (FCDO): {label}",
                "type": "travel_advice",
                "content": text,
                "language": "en",
                "location": "Cameroon",
                "region": normalize_region(section) if part.get("slug") == "regional-risks" else None,
                "source_id": "SRC-029",
                "source_url": f"{WEB}/{part.get('slug')}",
                "authority_level": "primary",
                "license": "Open Government Licence v3.0",
                "verification_status": "verified",
                "last_verified": updated,
            })
    stats["parts"] = len(parts)
    return records
