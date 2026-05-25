#!/usr/bin/env python3
"""
fetch_communes.py — holt alle Schweizer Gemeinden mit Koordinaten + Einwohnerzahl
von Wikidata via SPARQL und schreibt data/communes.json.

Aktualität: Wikidata wird kontinuierlich gepflegt. Skript läuft monatlich
via .github/workflows/refresh-data.yml. Bei API-Abriss bleibt die letzte
erfolgreiche Snapshot-Datei intakt, _health.json zeigt den Status.

Risiko-Profil (für Adrian's Risiko-Filter):
- Wikidata SPARQL-Endpoint ist seit >10 Jahren stabil
- Rate-Limit: 60 req/min — ein Query reicht für alle CH-Gemeinden
- Schema-Stabilität: P31 (instance of), P625 (coordinate), P1082 (population) sind
  Wikidata-Kern-Properties, sehr unwahrscheinlich entfernt zu werden
- Fallback: bei Fehler wird die alte communes.json behalten + _health.json updated
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data"))
OUT_FILE = os.path.join(DATA_DIR, "communes.json")
HEALTH_FILE = os.path.join(DATA_DIR, "_health.json")
USER_AGENT = "SwissSTR-Intelligence/0.9 (https://github.com/Adrianmaagg/swissstr) Python/urllib"

# SPARQL: alle Schweizer Gemeinden (Q70208 = Schweizer Gemeinde) mit Koords + Pop + Kanton
SPARQL = """
SELECT DISTINCT ?commune ?communeLabel ?bfs ?population ?coord ?cantonLabel WHERE {
  ?commune wdt:P31/wdt:P279* wd:Q70208 .
  OPTIONAL { ?commune wdt:P771 ?bfs . }
  OPTIONAL { ?commune wdt:P1082 ?population . FILTER NOT EXISTS { ?commune p:P1082/pq:P582 ?endDate . } }
  OPTIONAL { ?commune wdt:P625 ?coord . }
  OPTIONAL { ?commune wdt:P131 ?canton . ?canton wdt:P31 wd:Q23058 . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,it,en" . }
}
"""

def fetch_wikidata():
    url = WIKIDATA_ENDPOINT + "?" + urllib.parse.urlencode({"query": SPARQL, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

def parse_coord(point_str):
    """Wikidata Point: 'Point(lon lat)' → (lat, lon)"""
    if not point_str or not point_str.startswith("Point("):
        return None
    try:
        parts = point_str[6:-1].split()
        return (float(parts[1]), float(parts[0]))
    except (ValueError, IndexError):
        return None

def transform(sparql_results):
    """SPARQL-Output → flat dict pro Gemeinde."""
    communes = {}
    for row in sparql_results["results"]["bindings"]:
        name = row.get("communeLabel", {}).get("value", "")
        if not name or name.startswith("Q"):  # Skip unlabeled items
            continue
        bfs = row.get("bfs", {}).get("value")
        pop = row.get("population", {}).get("value")
        coord = parse_coord(row.get("coord", {}).get("value"))
        canton = row.get("cantonLabel", {}).get("value")
        if not coord:
            continue
        # Use BFS-number as primary key if available, else name
        key = name
        existing = communes.get(key)
        new_record = {
            "name": name,
            "bfs_code": int(bfs) if bfs and bfs.isdigit() else None,
            "population": int(pop) if pop and pop.isdigit() else None,
            "lat": coord[0],
            "lon": coord[1],
            "canton": canton,
        }
        # Keep record with the most info (BFS code preferred, then population)
        if not existing or (new_record["bfs_code"] and not existing["bfs_code"]):
            communes[key] = new_record
    return communes

def write_outputs(communes):
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "_meta": {
            "source": "Wikidata SPARQL (Q70208 = Schweizer Gemeinde)",
            "source_url": WIKIDATA_ENDPOINT,
            "license": "Wikidata: CC0",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(communes),
            "note": "Alle Schweizer Gemeinden mit Koordinaten. Verwendet vom Frontend zur automatischen Vorort-Detection. Bei API-Abriss bleibt die letzte erfolgreiche Snapshot-Datei.",
        },
        "communes": communes,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(communes)} communes to {OUT_FILE}")

def update_health(status: str, error: str = None):
    """Update data/_health.json — communes-Quelle."""
    if not os.path.exists(HEALTH_FILE):
        print("WARN: _health.json missing, skipping health update")
        return
    with open(HEALTH_FILE, "r", encoding="utf-8") as f:
        health = json.load(f)
    health.setdefault("sources", {})
    entry = health["sources"].setdefault("communes_wikidata", {
        "name": "CH-Gemeindeverzeichnis (Wikidata)",
        "url": WIKIDATA_ENDPOINT,
        "snapshot_file": "data/communes.json",
        "expected_frequency": "monthly",
        "note": "Wikidata wird kontinuierlich gepflegt. Refresh monatlich. Genutzt für Smart Suburban Detection (autoSuburbsFor).",
    })
    now = datetime.now(timezone.utc).isoformat()
    entry["last_attempt"] = now
    if status == "ok":
        entry["last_success"] = now
        entry["status"] = "ok"
        entry.pop("error", None)
    else:
        entry["status"] = "error"
        if error:
            entry["error"] = error
    health["generated_at"] = now
    with open(HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump(health, f, ensure_ascii=False, indent=2)

def main():
    try:
        print("Fetching CH communes from Wikidata...")
        t0 = time.time()
        results = fetch_wikidata()
        communes = transform(results)
        if len(communes) < 1500:
            raise RuntimeError(f"Sanity check failed: only {len(communes)} communes (expected >2000)")
        write_outputs(communes)
        update_health("ok")
        print(f"OK — {len(communes)} communes in {time.time()-t0:.1f}s")
        return 0
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        update_health("error", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
