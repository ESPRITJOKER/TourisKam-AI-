"""OpenStreetMap tourism POIs for Cameroon -> region x category digest records.

Supporting geographic data (ODbL 1.0, (c) OpenStreetMap contributors): names,
types, nearest town, coordinates and any tagged website/phone/hours. Regions
are assigned locally by point-in-polygon against the OSM region boundaries
(ISO3166-2 "CM-*"), which avoids slow per-region Overpass area queries.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict

from common import Fetcher, normalize_region

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
_CM = 'area["ISO3166-1"="CM"][admin_level=2]->.cm;'
Q_POIS = ('[out:json][timeout:240];' + _CM + '('
          'nwr(area.cm)["tourism"~"^(attraction|museum|viewpoint|hotel|guest_house|hostel|motel|zoo|theme_park|camp_site|gallery|artwork)$"];'
          'nwr(area.cm)["historic"];'
          'nwr(area.cm)["leisure"="nature_reserve"];'
          'nwr(area.cm)["boundary"="national_park"];'
          ');out center tags;')
Q_REGIONS = '[out:json][timeout:240];rel["ISO3166-2"~"^CM-"]["admin_level"="4"];out geom;'
Q_PLACES = '[out:json][timeout:120];' + _CM + 'node(area.cm)["place"~"^(city|town)$"];out;'

CATEGORY = {
    "hotel": "Accommodation", "guest_house": "Accommodation", "hostel": "Accommodation",
    "motel": "Accommodation", "camp_site": "Accommodation",
    "attraction": "Attractions and viewpoints", "viewpoint": "Attractions and viewpoints",
    "theme_park": "Attractions and viewpoints", "zoo": "Attractions and viewpoints",
    "artwork": "Attractions and viewpoints",
    "museum": "Museums and galleries", "gallery": "Museums and galleries",
    "historic": "Heritage and monuments",
    "national_park": "Parks and nature reserves", "nature_reserve": "Parks and nature reserves",
}
PACK_CHARS = 1000      # one record ~= one embedding chunk
TOWN_RADIUS_KM = 30
BAND = 0.1             # latitude band (degrees) for the point-in-polygon index


def overpass(query: str) -> dict:
    """Run a query with endpoint fallback; re-fetch if a cached body isn't valid JSON."""
    f = Fetcher(min_interval=5.0, timeout=300.0)
    for ep in ENDPOINTS:
        for use_cache in (True, False):
            text = f.fetch(ep, data={"data": query}, retries=2, use_cache=use_cache)
            try:
                data = json.loads(text) if text else None
            except ValueError:
                data = None
            if data and "elements" in data:
                return data
    raise RuntimeError("Overpass API unavailable on all endpoints")


def build_region_index(rels: list[dict]) -> list[tuple[str, int, tuple, dict]]:
    """-> [(region name, relation id, bbox, {lat band: [segments]})]."""
    index = []
    for rel in rels:
        tags = rel.get("tags", {})
        name = normalize_region(tags.get("name:en") or tags.get("name"))
        if not name:
            continue
        bands: dict[int, list] = defaultdict(list)
        lats, lons = [], []
        for m in rel.get("members", []):
            geom = m.get("geometry") if m.get("type") == "way" else None
            for a, b in zip(geom or [], (geom or [])[1:]):
                seg = (a["lat"], a["lon"], b["lat"], b["lon"])
                lo, hi = sorted((a["lat"], b["lat"]))
                for band in range(math.floor(lo / BAND), math.floor(hi / BAND) + 1):
                    bands[band].append(seg)
                lats += [a["lat"], b["lat"]]
                lons += [a["lon"], b["lon"]]
        if lats:
            index.append((name, rel["id"], (min(lats), max(lats), min(lons), max(lons)), bands))
    return index


def region_of(lat: float, lon: float, index) -> tuple[str | None, int | None]:
    for name, rel_id, (s, n, w, e), bands in index:
        if not (s <= lat <= n and w <= lon <= e):
            continue
        inside = False  # even-odd ray casting over every boundary segment (handles multipolygons)
        for y1, x1, y2, x2 in bands.get(math.floor(lat / BAND), ()):
            if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside:
            return name, rel_id
    return None, None


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p = math.pi / 180
    a = (0.5 - math.cos((lat2 - lat1) * p) / 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2)
    return 12742 * math.asin(math.sqrt(a))


def describe(t: dict, lat: float, lon: float, town: str | None, osm_ref: str) -> str:
    kind = t.get("tourism") or ("historic site" if t.get("historic") else
                                (t.get("boundary") or t.get("leisure") or "")).replace("_", " ")
    if t.get("historic") and t["historic"] != "yes":
        kind = f"historic {t['historic'].replace('_', ' ')}"
    bits = [kind] + ([f"{t['stars']} stars"] if t.get("stars") else [])
    line = f"- {t['name']} ({', '.join(b for b in bits if b)}) — {town or 'town not tagged'}; {lat:.4f}, {lon:.4f}"
    for key, label in (("website", "website"), ("contact:website", "website"), ("phone", "phone"),
                       ("contact:phone", "phone"), ("opening_hours", "hours")):
        if t.get(key):
            line += f"; {label}: {t[key]}"
    return line + f" [osm {osm_ref}]"


def scrape(f: Fetcher, limit: int | None, stats: Counter) -> list[dict]:
    index = build_region_index(overpass(Q_REGIONS)["elements"])
    stats["regions indexed"] = len(index)
    places = [(p["tags"]["name"], p["lat"], p["lon"]) for p in overpass(Q_PLACES)["elements"]
              if p.get("tags", {}).get("name") and "lat" in p]
    stats["towns"] = len(places)

    groups: dict[tuple, list[tuple[str, str]]] = defaultdict(list)  # (region, rel, category) -> [(town, line)]
    for el in overpass(Q_POIS)["elements"]:
        t = el.get("tags", {})
        lat, lon = (el["lat"], el["lon"]) if "lat" in el else (el.get("center", {}).get("lat"), el.get("center", {}).get("lon"))
        kind = t.get("tourism") or ("historic" if t.get("historic") else t.get("boundary") or t.get("leisure"))
        if not t.get("name") or lat is None or kind not in CATEGORY:
            stats["skipped: unnamed / unlocated / other"] += 1
            continue
        region, rel_id = region_of(lat, lon, index)
        town = t.get("addr:city")
        if not town and places:
            dist, name = min((km(lat, lon, plat, plon), pname) for pname, plat, plon in places)
            town = name if dist <= TOWN_RADIUS_KM else None
        groups[(region, rel_id, CATEGORY[kind])].append((town or "~", describe(t, lat, lon, town, f"{el['type']}/{el['id']}")))
        stats["pois"] += 1

    records: list[dict] = []
    for (region, rel_id, category), items in sorted(groups.items(), key=lambda kv: (kv[0][0] or "~", kv[0][2])):
        items.sort()
        packs, buf, size = [], [], 0
        for town, line in items:
            if buf and size + len(line) > PACK_CHARS:
                packs.append(buf)
                buf, size = [], 0
            buf.append((town, line))
            size += len(line) + 1
        if buf:
            packs.append(buf)
        where = f"{region} region" if region else "Cameroon (region not determined)"
        for n, pack in enumerate(packs):
            towns = sorted({tw for tw, _ in pack if tw != "~"})
            town_list = ", ".join(towns[:6]) + ("…" if len(towns) > 6 else "")
            records.append({
                "id": f"OSM-{(region or 'unknown').replace(' ', '').replace('/', '')}-"
                      f"{category.split()[0].lower()}-{n:02d}",
                "title": f"{category} in {where}" + (f": {town_list}" if town_list else "") + " (OpenStreetMap)",
                "type": "poi_list",
                "content": (f"{category} in {where}, Cameroon, as mapped on OpenStreetMap "
                            "(community data; may be incomplete or outdated):\n"
                            + "\n".join(line for _, line in pack)),
                "language": "en",
                "location": town_list or None,
                "region": region,
                "source_id": "SRC-028",
                "source_url": (f"https://www.openstreetmap.org/relation/{rel_id}" if rel_id
                               else "https://www.openstreetmap.org/relation/192830"),
                "authority_level": "secondary",
                "license": "ODbL 1.0",
                "verification_status": "unverified",
            })
    return records[:limit] if limit else records
