#!/usr/bin/env python3
"""
fetch_airbnb.py — Airbnb-Konkurrenz pro Markt via Bright Data → data/airbnb-competitors.json.

Speist das "Konkurrenz-Röntgen" in SwissSTR: pro Markt echte Inserate mit
  - Grössen-Mix (room_type / bedrooms),
  - Reviews/Monat → Auslastungs-Proxy (so erkennt man "immer ausgebucht"),
  - Vollzeit-Anbieter-Erkennung (host_listings_count > 1).

ZWEI MODI — der Token wird NIE im Code/Repo gespeichert:

  (A) Trim eines heruntergeladenen Exports  (KEIN Token nötig):
      In Bright Data "Entdecken nach Standort" laufen lassen, JSON herunterladen,
      nach data/raw/ legen, dann:
          python tools/fetch_airbnb.py --ingest data/raw/<datei>.json --market Aarau

  (B) Automatik via API  (Token aus Umgebung/.env, nie committet):
      In swissstr/.env:   BRIGHTDATA_API_KEY=dein_token
          python tools/fetch_airbnb.py --fetch --market Aarau --urls data/raw/aarau_urls.txt

Beide schreiben dasselbe getrimmte Schema nach data/airbnb-competitors.json (keyed by Markt).

Pricing-Hinweis: Bright-Data-Airbnb-Collector ~$1.50 / 1'000 Datensätze (Inserate).
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
OUT_FILE = os.path.join(DATA_DIR, "airbnb-competitors.json")

DATASET_ID = "gd_ld7ll037kqy322v05"  # Airbnb "Objektinformationen – Erfassung per URL"
SCRAPE_ENDPOINT = (
    "https://api.brightdata.com/datasets/v3/scrape"
    "?dataset_id={ds}&notify=false&include_errors=true"
)

# ── Annahmen für den Auslastungs-Proxy (transparent, justierbar) ──────────────
REVIEW_RATE = 0.55     # Anteil der Gäste, die eine Bewertung hinterlassen (~50–70%)
AVG_STAY_NIGHTS = 3.0  # Ø Aufenthaltsdauer (STR-realistisch)


def _load_dotenv():
    """Liest swissstr/.env (falls vorhanden) in os.environ — ohne externe Abhängigkeit."""
    env_path = os.path.join(ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _first(rec, *keys, default=None):
    """Holt den ersten vorhandenen, nicht-leeren Wert aus mehreren möglichen Feldnamen."""
    for k in keys:
        if k in rec and rec[k] not in (None, "", []):
            return rec[k]
    return default


def _to_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v)
    digits = "".join(ch for ch in s if ch.isdigit() or ch in ".,")
    digits = digits.replace(",", "")
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def occupancy_proxy(reviews_per_month):
    """Reviews/Monat → grobe Auslastungs-Schätzung (0–95%). MOD-Tier, kein BFS."""
    if not reviews_per_month or reviews_per_month <= 0:
        return None
    stays_per_month = reviews_per_month / REVIEW_RATE
    nights_per_month = stays_per_month * AVG_STAY_NIGHTS
    occ = nights_per_month / 30.4 * 100
    return round(min(95.0, max(0.0, occ)), 1)


def normalize(rec):
    """BD-Airbnb-Record → schlankes SwissSTR-Schema (defensiv über Feldnamen)."""
    reviews_count = _to_float(_first(rec, "reviews_count", "number_of_reviews", "reviews"))
    rpm = _to_float(_first(rec, "reviews_per_month"))
    # Falls reviews_per_month fehlt: aus Anzahl + erstem Review schätzen.
    if rpm is None and reviews_count:
        first_review = _first(rec, "first_review", "first_review_date")
        months_active = None
        if first_review:
            try:
                d = datetime.fromisoformat(str(first_review)[:10])
                months_active = max(1.0, (datetime.now() - d).days / 30.4)
            except ValueError:
                months_active = None
        if months_active:
            rpm = round(reviews_count / months_active, 2)
    host_listings = _to_float(_first(
        rec, "host_listings_count", "host_number_of_listings",
        "host_total_listings_count", "host_listings"))
    return {
        "id": _first(rec, "id", "listing_id", "room_id"),
        "name": _first(rec, "name", "title", "listing_name"),
        "url": _first(rec, "url", "listing_url"),
        "room_type": _first(rec, "room_type", "property_type", "category_name"),
        "bedrooms": _to_float(_first(rec, "bedrooms", "beds")),
        "price_chf": _to_float(_first(rec, "price", "price_per_night", "nightly_price")),
        "rating": _to_float(_first(rec, "rating", "ratings", "review_scores_rating")),
        "reviews_count": int(reviews_count) if reviews_count else None,
        "reviews_per_month": rpm,
        "occupancy_proxy_pct": occupancy_proxy(rpm),
        "host_id": _first(rec, "host_id", "host"),
        "host_name": _first(rec, "host_name", "host"),
        "host_listings_count": int(host_listings) if host_listings else None,
        "is_pro_host": bool(host_listings and host_listings > 1),
    }


def write_market(market, records, source):
    os.makedirs(DATA_DIR, exist_ok=True)
    existing = {}
    if os.path.isfile(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as fh:
            try:
                existing = json.load(fh)
            except json.JSONDecodeError:
                existing = {}
    listings = [normalize(r) for r in records if isinstance(r, dict)]
    listings = [l for l in listings if l["id"] or l["url"]]
    pros = sum(1 for l in listings if l["is_pro_host"])
    occs = [l["occupancy_proxy_pct"] for l in listings if l["occupancy_proxy_pct"]]
    existing[market] = {
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": source,
        "count": len(listings),
        "pro_host_count": pros,
        "avg_occupancy_proxy_pct": round(sum(occs) / len(occs), 1) if occs else None,
        "listings": listings,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)
    print(f"[airbnb] {market}: {len(listings)} Inserate, {pros} Profi-Hosts, "
          f"Ø-Auslastungs-Proxy {existing[market]['avg_occupancy_proxy_pct']}% → {OUT_FILE}")


def extract_records(payload):
    """BD-Antwort kann Liste, {'data':[...]}, oder NDJSON-artig sein — robust extrahieren."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results", "records", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return [payload]
    return []


def cmd_ingest(args):
    with open(args.ingest, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    records = extract_records(payload)
    if not records:
        sys.exit("Keine Records im Export gefunden — Dateiformat prüfen.")
    write_market(args.market, records, source=f"BD-Export ({os.path.basename(args.ingest)})")


def cmd_fetch(args):
    _load_dotenv()
    token = os.environ.get("BRIGHTDATA_API_KEY")
    if not token:
        sys.exit("BRIGHTDATA_API_KEY fehlt. In swissstr/.env setzen (nie committen).")
    if not args.urls or not os.path.isfile(args.urls):
        sys.exit("--urls <datei mit je einer Airbnb-Room-URL pro Zeile> nötig für --fetch.")
    with open(args.urls, "r", encoding="utf-8") as fh:
        urls = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not urls:
        sys.exit("URL-Liste leer.")
    body = json.dumps({"input": [{"url": u, "country": "CH"} for u in urls]}).encode("utf-8")
    req = urllib.request.Request(
        SCRAPE_ENDPOINT.format(ds=DATASET_ID),
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    print(f"[airbnb] Triggere BD-Scrape für {len(urls)} URLs ({args.market}) …")
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, f"airbnb_{args.market.lower()}.json")
    with open(raw_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"[airbnb] Rohantwort → {raw_path}")
    records = extract_records(payload)
    write_market(args.market, records, source="BD-API (scrape by URL)")


def main():
    ap = argparse.ArgumentParser(description="Airbnb-Konkurrenz → SwissSTR Konkurrenz-Röntgen")
    ap.add_argument("--market", required=True, help="Marktname (z.B. Aarau) — Key in der JSON")
    ap.add_argument("--ingest", help="Pfad zu heruntergeladenem BD-Export (kein Token nötig)")
    ap.add_argument("--fetch", action="store_true", help="Per BD-API holen (Token aus .env)")
    ap.add_argument("--urls", help="Datei mit Airbnb-Room-URLs (eine pro Zeile) für --fetch")
    args = ap.parse_args()
    if args.ingest:
        cmd_ingest(args)
    elif args.fetch:
        cmd_fetch(args)
    else:
        ap.error("Entweder --ingest <datei> oder --fetch angeben.")


if __name__ == "__main__":
    main()
