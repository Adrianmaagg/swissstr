#!/usr/bin/env python3
"""
fetch_leerstand.py — holt die Leerwohnungsziffer (%) pro Schweizer Gemeinde vom
Bundesamt für Statistik (BFS) und schreibt data/leerstand.json.

Quelle: BFS — Leerwohnungszählung, Dataflow CH1.LWZ:DF_LWZ_1 auf der SDMX-Plattform
  stats.swiss (disseminate.stats.swiss). Stichtag 1. Juni, jährlich.
  Doku: https://www.bfs.admin.ch/asset/de/DF_LWZ_1

Abfrage-Strategie: NICHT der 767-MB-Volldump, sondern eine gefilterte SDMX-Slice:
  Key ._T._T.PC.A = alle Regionen · Total-Zimmerzahl · Total-Leerwohnungstyp ·
  MEASURE=PC (Leerwohnungsziffer in %) · FREQ=A (jährlich). ~530 KB, ~2 s.
  Danach Filter auf DIFF_REGION_REF=POLG (politische Gemeinde) + neuestes Jahr.

Verwendung im Tool: Leerwohnungsziffer als Proxy für MIETVERHANDLUNGS-HEBEL (§9-Inferenz):
  hohe Leerstandsquote → Vermieter füllt gern → mehr Verhandlungsspielraum für Rent-to-Rent;
  tiefe Quote (Resorts/Städte) → angespannt, wenig Hebel. Proxy, nicht Tatsache (🟡 MOD).

Aktualität: BFS publiziert jährlich (~Q3). Refresh monatlich via refresh-data.yml.
  Bei Fehler bleibt die letzte Snapshot-Datei intakt, _health.json zeigt den Status.

Risiko-Profil:
- disseminate.stats.swiss ist die offizielle BFS-SDMX-REST-API (stabil, dokumentiert)
- Format SDMX-CSV (stdlib csv, keine Extra-Deps)
- Slice-Key fest; bricht sichtbar, wenn Dataflow-Struktur sich ändert (Sanity-Check)
- Fallback: bei Fehler alte leerstand.json behalten + _health.json error
"""

import csv
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

# Gefilterte SDMX-Slice: alle Regionen, Total-Zimmer, Total-Typ, Leerwohnungsziffer %, jährlich
DATA_URL = ("https://disseminate.stats.swiss/rest/data/CH1.LWZ,DF_LWZ_1,1.0.0/"
            "._T._T.PC.A/?startPeriod=2023&format=csv")
SOURCE_URL = "https://www.bfs.admin.ch/asset/de/DF_LWZ_1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data"))
OUT_FILE = os.path.join(DATA_DIR, "leerstand.json")
HEALTH_FILE = os.path.join(DATA_DIR, "_health.json")
USER_AGENT = "SwissSTR-Intelligence/0.9 (https://github.com/Adrianmaagg/swissstr) Python/urllib"


def fetch_csv():
    req = urllib.request.Request(DATA_URL, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.sdmx.data+csv",
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read().decode("utf-8", "replace")


def parse(text):
    """SDMX-CSV → {bfs: {pct, year}} nur für politische Gemeinden (POLG), neuestes Jahr."""
    reader = csv.DictReader(io.StringIO(text))
    best = {}  # bfs → (year, pct)
    for row in reader:
        if row.get("DIFF_REGION_REF") != "POLG":
            continue  # nur politische Gemeinden (nicht Kanton/Grossregion)
        bfs = row.get("GR_KT_GDE", "").strip()
        val = row.get("OBS_VALUE", "").strip()
        yr = row.get("TIME_PERIOD", "").strip()
        if not bfs or not val or not yr.isdigit():
            continue
        try:
            pct = round(float(val), 2)
            year = int(yr)
        except ValueError:
            continue
        prev = best.get(bfs)
        if prev is None or year > prev[0]:
            best[bfs] = (year, pct)
    communes = {bfs: {"pct": pct} for bfs, (year, pct) in best.items()}
    latest_year = max((y for y, _ in best.values()), default=None)
    return latest_year, communes


def build_payload(year, communes):
    return {
        "_meta": {
            "source": "BFS Leerwohnungszählung (CH1.LWZ:DF_LWZ_1, Leerwohnungsziffer in %)",
            "source_url": SOURCE_URL,
            "year": year,
            "license": "BFS / opendata.swiss — frei nutzbar",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(communes),
            "unit": "Leerwohnungsziffer in % (leer stehende / Gesamtbestand, Stichtag 1.6.)",
            "note": (
                "Leerwohnungsziffer pro politische Gemeinde, neuestes Jahr. Proxy für "
                "Mietverhandlungs-Hebel: hohe Quote → mehr Verhandlungsspielraum für "
                "Rent-to-Rent; tiefe Quote (Resorts/Städte) → angespannt. 🟡 MOD-Proxy."
            ),
        },
        "communes": communes,
    }


def update_health(status, year=None, count=None, error=None):
    if not os.path.exists(HEALTH_FILE):
        print("WARN: _health.json missing, skipping health update")
        return
    with open(HEALTH_FILE, "r", encoding="utf-8") as f:
        health = json.load(f)
    health.setdefault("sources", {})
    entry = health["sources"].setdefault("bfs_leerstand", {
        "name": "BFS Leerwohnungsziffer (Gemeinde)",
        "url": SOURCE_URL,
        "snapshot_file": "data/leerstand.json",
        "expected_frequency": "yearly",
        "note": "BFS Leerwohnungszählung (SDMX). Proxy für Mietverhandlungs-Hebel pro Markt.",
    })
    now = datetime.now(timezone.utc).isoformat()
    entry["last_attempt"] = now
    if status == "ok":
        entry["last_success"] = now
        entry["status"] = "ok"
        entry["period_covered"] = str(year)
        entry["covered_communes"] = count
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
        print("Fetching BFS Leerwohnungsziffer (SDMX slice)...")
        t0 = time.time()
        text = fetch_csv()
        year, communes = parse(text)
        payload = build_payload(year, communes)
        n = len(communes)
        if n < 1500:
            raise RuntimeError(f"Sanity check failed: only {n} communes (expected ~2000+)")
        if not year or year < 2020:
            raise RuntimeError(f"Sanity check failed: implausible year {year}")
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        update_health("ok", year=year, count=n)
        print(f"OK — {n} communes, year {year} in {time.time()-t0:.1f}s")
        return 0
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        update_health("error", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
