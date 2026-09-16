"""TourisCam AI — load real tariff rows for the Tariff Guard.

Sources (no invented prices):
  - MINTOUL official indicative transport fares:
    dataset/touriscam_dataset_final/practical_information.csv (Transport rows)
  - Hand-checked entry/room/meal prices with per-row confidence:
    dataset/touriscam_kribi_to_west_staging.csv

Each row keeps the source wording in `description` (so the bot quotes the
original price text), a confidence-based `verification_status`, and a
`search_text` keyword string used by the n8n pricing lookup. Numeric min/max
are only filled when the price is a plain number or "a-b" range.

Idempotent: one transaction applies db/tariffs_v2.sql, removes the Day-1
placeholder rows and previously loaded rows (by source_ref), then inserts.

Usage:
    python rag/load_tariffs.py --dry-run
    python rag/load_tariffs.py
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata

from config import ROOT, pg_connect

sys.path.insert(0, str(ROOT / "rag" / "scrapers"))
from staging import STATUS as STAGING_STATUS  # noqa: E402  (confidence -> status map)

PRACTICAL_CSV = ROOT / "dataset" / "touriscam_dataset_final" / "practical_information.csv"
STAGING_CSV = ROOT / "dataset" / "touriscam_kribi_to_west_staging.csv"
DDL_PATH = ROOT / "db" / "tariffs_v2.sql"
MINTOUL_TRANSPORT_URL = "https://mintoul.gov.cm/infos-pratiques/transport-interne/"
PACKAGE_DATE = "2026-09-11"  # touriscam_dataset_final curation date
PLACEHOLDER_SOURCE = "Field benchmark — SURVEY PENDING"  # db/seed.sql rows

COLUMNS = ("category", "origin", "destination", "transport_type", "description", "min_price",
           "max_price", "currency", "unit", "time_of_day", "source", "verification_status",
           "last_verified", "notes", "search_text", "source_ref")

SYNONYMS = {
    "taxi": "taxi cab", "airport": "airport aeroport", "night": "night nuit soir",
    "day": "day jour journee", "city": "city ville", "toll": "toll peage road route",
    "accommodation": "hotel room chambre nuit lodging hebergement",
    "attraction": "entry entree ticket billet fee frais visit visite",
    "food": "meal repas restaurant food manger plat",
}


def keywords(*parts: str) -> str:
    text = " ".join(p for p in parts if p)
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    words = re.sub(r"[^a-z0-9-]+", " ", text).split()
    return " ".join(dict.fromkeys(words))  # de-duplicate, keep order


def first_number(text: str) -> float | None:
    m = re.search(r"\d[\d,\s]*", text)
    return float(re.sub(r"[,\s]", "", m.group(0))) if m else None


def mintoul_rows() -> list[tuple]:
    rows = []
    with open(PRACTICAL_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["category"] != "Transport":
                continue
            topic = r["topic"].lower()
            price = first_number(r["value"])
            if price is None:
                raise ValueError(f"{r['id']}: no price in {r['value']!r}")
            is_taxi = "taxi" in topic
            time_of_day = "night" if "night" in topic else "day" if "daytime" in topic else "any"
            tags = [SYNONYMS["taxi"]] if is_taxi else [SYNONYMS["toll"]]
            if "airport" in topic:
                tags.append(SYNONYMS["airport"])
            if "city" in topic:
                tags.append(SYNONYMS["city"])
            if time_of_day != "any":
                tags.append(SYNONYMS[time_of_day])
            rows.append((
                "transport", None, None, "taxi" if is_taxi else "road toll",
                f"{r['topic']}: {r['details'].rstrip('.')}",  # SQL appends ". Unit: ..."
                price, None if "minimum" in topic else price, "XAF",
                "per trip" if is_taxi else r["value"].split("XAF", 1)[-1].strip() or None,
                time_of_day, f"MINTOUL — Transport interne ({MINTOUL_TRANSPORT_URL})",
                "benchmark", PACKAGE_DATE,
                "Official MINTOUL indicative fare — actual fares vary; agree the price before the trip.",
                keywords(r["topic"], r["value"], *tags), r["id"],
            ))
    return rows


def staging_category(label: str) -> str:
    low = label.lower()
    if any(k in low for k in ("hotel", "gîte", "gite", "resort", "lodge")):
        return "accommodation"
    if any(k in low for k in ("restaurant", "dining", "food", "fish")):
        return "food"
    return "attraction"


def staging_rows() -> list[tuple]:
    rows = []
    with open(STAGING_CSV, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=1):
            conf = r["confidence"].strip()
            if conf not in STAGING_STATUS:
                raise ValueError(f"STG-{i:03d}: unknown confidence {conf!r}")
            price = r["price_fcfa"].strip()
            rng = re.fullmatch(r"~?\s*(\d+)\s*-\s*(\d+)", price)
            one = re.fullmatch(r"~?\s*(\d+)", price)
            lo, hi = ((float(rng[1]), float(rng[2])) if rng
                      else (float(one[1]), float(one[1])) if one else (None, None))
            category = staging_category(r["category"])
            rows.append((
                category, None, None, None,
                f"{r['property_name']}, {r['town']} — {r['room_or_dish']}: {price} FCFA",
                lo, hi, "XAF", r["room_or_dish"] or None, "any",
                "TourisCam verification dossier (dataset/touriscam_kribi_to_west_staging.csv)",
                STAGING_STATUS[conf], None,
                f"Confidence {conf}. {r['source_note']}",
                keywords(r["property_name"], r["town"], r["neighborhood"], r["category"],
                         r["room_or_dish"], SYNONYMS[category]),
                f"STG-{i:03d}",
            ))
    return rows


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Load Tariff Guard rows into Supabase.")
    ap.add_argument("--dry-run", action="store_true", help="parse + print only; no DB writes")
    args = ap.parse_args()

    rows = mintoul_rows() + staging_rows()
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row[11]] = by_status.get(row[11], 0) + 1
    print(f"Prepared {len(rows)} tariff rows ({len(mintoul_rows())} MINTOUL, "
          f"{len(rows) - len(mintoul_rows())} staging) | status: {by_status}")
    for row in rows[:6] + rows[-2:]:
        print(f"  [{row[15]}] {row[0]:13} {row[9]:5} min={row[5]} max={row[6]} | {row[4][:70]}")
    if args.dry_run:
        print("Dry-run: no DB writes.")
        return 0

    from psycopg2.extras import execute_values

    conn = pg_connect()
    try:
        with conn.cursor() as cur:  # single transaction
            cur.execute(DDL_PATH.read_text(encoding="utf-8"))
            cur.execute("delete from tariffs where source = %s", (PLACEHOLDER_SOURCE,))
            placeholders = cur.rowcount
            cur.execute("delete from tariffs where source_ref like 'PR-%%' or source_ref like 'STG-%%'")
            replaced = cur.rowcount
            execute_values(cur, f"insert into tariffs ({', '.join(COLUMNS)}) values %s", rows)
            cur.execute("select count(*) from tariffs")
            total = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"\nDone: removed {placeholders} placeholder + {replaced} previous rows; tariffs now has {total} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
