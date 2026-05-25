"""
Fetch OpenStreetMap POIs around each SwissSTR market via Overpass API.
For each market with lat/lon: count restaurants, bars, cafes, pharmacies,
supermarkets, playgrounds, public transport stops, ski lifts within 1.5 km.

Output: data/osm-pois.json with per-market POI counts and computed scores.

Rate-limited: 1.5 sec between queries to be polite to Overpass.
"""
import json, urllib.request, urllib.parse, sys, io, time, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OVERPASS = "https://overpass-api.de/api/interpreter"
RADIUS_M = 1500          # 1.5 km
SKI_RADIUS_M = 3000      # ski lifts often farther from village center
SLEEP_SECONDS = 1.5

# Load market coords from js/coords.js
coords_js = Path("../js/coords.js").read_text(encoding="utf-8")
COORDS = {}
for m in re.finditer(r'"([^"]+)":\s*\{\s*lat:\s*([\d.]+),\s*lon:\s*([\d.]+)\s*\}', coords_js):
    name, lat, lon = m.group(1), float(m.group(2)), float(m.group(3))
    COORDS[name] = (lat, lon)
print(f"Markets with coordinates: {len(COORDS)}")

def overpass_query(lat, lon):
    """Single multi-tag Overpass query for all POI categories around a point."""
    return f"""
[out:json][timeout:25];
(
  node["amenity"="restaurant"](around:{RADIUS_M},{lat},{lon});
  node["amenity"="bar"](around:{RADIUS_M},{lat},{lon});
  node["amenity"="cafe"](around:{RADIUS_M},{lat},{lon});
  node["amenity"="pharmacy"](around:{RADIUS_M},{lat},{lon});
  node["amenity"="hospital"](around:{RADIUS_M},{lat},{lon});
  node["leisure"="playground"](around:{RADIUS_M},{lat},{lon});
  node["leisure"="park"](around:{RADIUS_M},{lat},{lon});
  node["shop"="supermarket"](around:{RADIUS_M},{lat},{lon});
  node["shop"="bakery"](around:{RADIUS_M},{lat},{lon});
  node["public_transport"="stop_position"](around:{RADIUS_M},{lat},{lon});
  node["railway"="station"](around:{RADIUS_M},{lat},{lon});
  way["aerialway"](around:{SKI_RADIUS_M},{lat},{lon});
  node["tourism"="hotel"](around:{RADIUS_M},{lat},{lon});
  node["tourism"="information"](around:{RADIUS_M},{lat},{lon});
  way["leisure"="swimming_pool"](around:{RADIUS_M},{lat},{lon});
);
out tags;
"""

def count_tags(elements):
    counts = {
        "restaurant": 0, "bar": 0, "cafe": 0,
        "pharmacy": 0, "hospital": 0,
        "playground": 0, "park": 0,
        "supermarket": 0, "bakery": 0,
        "public_transport": 0, "railway_station": 0,
        "aerialway": 0,  # Skilifte
        "hotel": 0, "tourism_info": 0, "swimming_pool": 0,
    }
    for el in elements:
        t = el.get("tags", {})
        if t.get("amenity") == "restaurant": counts["restaurant"] += 1
        elif t.get("amenity") == "bar": counts["bar"] += 1
        elif t.get("amenity") == "cafe": counts["cafe"] += 1
        elif t.get("amenity") == "pharmacy": counts["pharmacy"] += 1
        elif t.get("amenity") == "hospital": counts["hospital"] += 1
        elif t.get("leisure") == "playground": counts["playground"] += 1
        elif t.get("leisure") == "park": counts["park"] += 1
        elif t.get("leisure") == "swimming_pool": counts["swimming_pool"] += 1
        elif t.get("shop") == "supermarket": counts["supermarket"] += 1
        elif t.get("shop") == "bakery": counts["bakery"] += 1
        elif t.get("public_transport") == "stop_position": counts["public_transport"] += 1
        elif t.get("railway") == "station": counts["railway_station"] += 1
        elif "aerialway" in t: counts["aerialway"] += 1
        elif t.get("tourism") == "hotel": counts["hotel"] += 1
        elif t.get("tourism") == "information": counts["tourism_info"] += 1
    return counts

def lifestyle_score(c):
    """0-100 score from POI counts. Capped at saturation thresholds."""
    cap = lambda n, ceiling: min(n / ceiling, 1.0)
    score = (
        cap(c["restaurant"], 30) * 25 +
        cap(c["cafe"] + c["bakery"], 15) * 15 +
        cap(c["bar"], 10) * 10 +
        cap(c["supermarket"], 4) * 10 +
        cap(c["public_transport"] + c["railway_station"] * 3, 8) * 20 +
        cap(c["pharmacy"], 3) * 8 +
        cap(c["park"] + c["playground"], 5) * 12
    )
    return round(score)

def family_score(c):
    cap = lambda n, ceiling: min(n / ceiling, 1.0)
    score = (
        cap(c["playground"], 4) * 30 +
        cap(c["supermarket"], 3) * 18 +
        cap(c["bakery"], 4) * 8 +
        cap(c["pharmacy"], 2) * 12 +
        cap(c["public_transport"] + c["railway_station"] * 3, 6) * 18 +
        cap(c["restaurant"], 20) * 8 +
        cap(c["park"], 4) * 6
    )
    return round(score)

def alpine_score(c):
    """How alpine is this place? Ski lifts + tourism markers."""
    cap = lambda n, ceiling: min(n / ceiling, 1.0)
    return round(cap(c["aerialway"], 10) * 60 + cap(c["hotel"], 30) * 25 + cap(c["tourism_info"], 3) * 15)

# Resume support — load existing snapshot and only fetch missing markets
existing_path = Path("../data/osm-pois.json")
result = {}
if existing_path.exists():
    try:
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        result = existing.get("markets", {})
        print(f"Resume mode: {len(result)} markets already cached")
    except Exception as e:
        print(f"Couldn't read existing snapshot: {e}")

todo = [(name, c) for name, c in COORDS.items() if name not in result]
errors = []
total = len(todo)
print(f"Fetching POIs for {total} missing markets (cached: {len(result)} of {len(COORDS)})")
print(f"Estimated time: ~{total * SLEEP_SECONDS / 60:.1f} min (plus Overpass server time)")

def save_progress():
    out = {
        "_meta": {
            "source": "OpenStreetMap via Overpass API",
            "source_url": "https://overpass-api.de/",
            "license": "© OpenStreetMap contributors, ODbL",
            "radius_meters": RADIUS_M,
            "ski_radius_meters": SKI_RADIUS_M,
            "covered_markets": len(result),
            "errors": len(errors),
            "fetched_at": time.strftime("%Y-%m-%d"),
            "note": "POI-Counts im jeweiligen Radius um die Markt-Koordinaten. Scores 0-100 sind Heuristiken.",
        },
        "markets": result,
    }
    existing_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

for i, (name, (lat, lon)) in enumerate(todo, 1):
    print(f"  [{i}/{total}] {name:30} ({lat:.3f}, {lon:.3f})", end=" ", flush=True)
    attempt = 0
    while attempt < 3:
        attempt += 1
        try:
            body = urllib.parse.urlencode({"data": overpass_query(lat, lon)}).encode()
            req = urllib.request.Request(OVERPASS, data=body, method="POST",
                headers={"User-Agent": "SwissSTR/0.8 (https://github.com/Adrianmaagg/swissstr)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read())
            counts = count_tags(data.get("elements", []))
            scores = {
                "lifestyle_score": lifestyle_score(counts),
                "family_score": family_score(counts),
                "alpine_score": alpine_score(counts),
            }
            result[name] = {"counts": counts, **scores}
            total_pois = sum(counts.values())
            print(f"→ {total_pois} POIs · life {scores['lifestyle_score']} · fam {scores['family_score']} · alp {scores['alpine_score']}")
            break
        except urllib.error.HTTPError as e:
            if e.code == 504 and attempt < 3:
                wait = 10 * attempt
                print(f"!! 504 — retry {attempt}/3 in {wait}s")
                time.sleep(wait)
                continue
            print(f"!! HTTP {e.code}")
            errors.append((name, f"HTTP {e.code}"))
            break
        except Exception as e:
            print(f"!! {e}")
            errors.append((name, str(e)))
            break
    time.sleep(SLEEP_SECONDS)
    # Save every 10 markets so progress survives crashes
    if i % 10 == 0:
        save_progress()
        print(f"  ... saved progress: {len(result)} markets in snapshot")

save_progress()
print(f"\nSaved data/osm-pois.json — {len(result)} markets, {len(errors)} errors")

# Quick sanity
print("\n=== Top 5 Lifestyle ===")
for n, d in sorted(result.items(), key=lambda x: -x[1]["lifestyle_score"])[:5]:
    print(f"  {d['lifestyle_score']:3} {n:25} (restaurants {d['counts']['restaurant']:3}, supermarkets {d['counts']['supermarket']})")
print("\n=== Top 5 Family ===")
for n, d in sorted(result.items(), key=lambda x: -x[1]["family_score"])[:5]:
    print(f"  {d['family_score']:3} {n:25} (playgrounds {d['counts']['playground']:2}, supermarkets {d['counts']['supermarket']})")
print("\n=== Top 5 Alpine ===")
for n, d in sorted(result.items(), key=lambda x: -x[1]["alpine_score"])[:5]:
    print(f"  {d['alpine_score']:3} {n:25} (skilifts {d['counts']['aerialway']:2}, hotels {d['counts']['hotel']})")
