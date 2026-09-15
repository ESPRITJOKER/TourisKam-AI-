"""Hand-checked Kribi-to-West amenities CSV -> records.

Source: dataset/touriscam_kribi_to_west_staging.csv. Each row's confidence label
maps to a verification_status; the row's source note is kept verbatim so the
bot can say where a price or phone number came from.
"""
from __future__ import annotations

import csv
from collections import Counter

from common import ROOT, Fetcher

CSV_PATH = ROOT / "dataset" / "touriscam_kribi_to_west_staging.csv"
STATUS = {
    "VERIFIED_PHONE": "benchmark",     # contact confirmed; prices are market ranges
    "VERIFIED_PRICE": "benchmark",
    "VERIFIED_NOTE": "benchmark",
    "UNCONFIRMED_PRICE": "estimated",
    "UNCONFIRMED_ALL": "unverified",
}
TOWN_REGION = [  # substring of the town field -> region
    ("kribi", "South"), ("campo", "South"),
    ("limbe", "South-West"), ("buea", "South-West"),
    ("douala", "Littoral"), ("edéa", "Littoral"), ("melong", "Littoral"),
    ("yaoundé", "Centre"), ("mfou", "Centre"),
    ("foumban", "West"), ("bafoussam", "West"), ("bandjoun", "West"), ("kouoptamo", "West"),
]


def _val(row: dict, key: str) -> str:
    v = (row.get(key) or "").strip()
    return "" if v.upper() == "N/A" else v


def scrape(f: Fetcher, limit: int | None, stats: Counter) -> list[dict]:
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if limit:
        rows = rows[:limit]

    records: list[dict] = []
    for i, r in enumerate(rows, start=1):
        conf = _val(r, "confidence")
        if conf not in STATUS:
            stats[f"dropped: unknown confidence {conf!r}"] += 1
            continue
        name, town = _val(r, "property_name"), _val(r, "town")
        where = f"{town}, {_val(r, 'neighborhood')}" if _val(r, "neighborhood") else town
        note = _val(r, "source_note")
        if note and note[-1] not in ".!?":
            note += "."
        parts = [f"{name} — {_val(r, 'category')}, {where}."]
        if _val(r, "room_or_dish"):
            parts.append(f"{_val(r, 'room_or_dish')} — price (FCFA): {_val(r, 'price_fcfa') or 'not published'}.")
        if _val(r, "breakfast"):
            parts.append(f"Breakfast: {_val(r, 'breakfast')}.")
        if _val(r, "amenities_tags"):
            parts.append(f"Amenities: {_val(r, 'amenities_tags').replace(',', ', ')}.")
        if _val(r, "phone_number"):
            parts.append(f"Phone: {_val(r, 'phone_number')}.")
        parts.append(f"Confidence: {conf}. Source note: {note}")
        parts.append("Prices are indicative and may have changed; verify before travel.")

        low = town.lower()
        records.append({
            "id": f"STG-{i:03d}",
            "title": f"{name} — {_val(r, 'room_or_dish') or _val(r, 'category')}",
            "type": "amenity",
            "content": " ".join(parts),
            "language": "en",
            "location": town,
            "region": next((reg for key, reg in TOWN_REGION if key in low), None),
            "source_id": "SRC-030",
            "source_url": "dataset/touriscam_kribi_to_west_staging.csv",
            "authority_level": "third_party",
            "license": "project-internal",
            "verification_status": STATUS[conf],
        })
    return records
