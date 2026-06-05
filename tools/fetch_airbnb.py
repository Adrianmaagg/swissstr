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
import re
import sys
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")             # lokaler Zwischenspeicher (gitignored)
OUT_FILE = os.path.join(DATA_DIR, "airbnb-competitors.json")  # Serving-Schicht (git, aktueller Snapshot)
TRENDS_FILE = os.path.join(DATA_DIR, "airbnb-trends.json")    # Serving-Schicht: Zeitreihen-Aggregate

# ── Skalierbare Schichten-Ablage ───────────────────────────────────────────────
# ① Roh-Archiv + ② Zeitreihe liegen ausserhalb des Repos (gross, wachsend) — in OneDrive.
# Pfad via .env (SWISSSTR_DATA_DIR) überschreibbar; Default = OneDrive-Projektordner.
ONEDRIVE_DATA = (os.environ.get("SWISSSTR_DATA_DIR")
                 or r"C:\Users\adria\OneDrive\Claude Cowork\03_Projekte_Aktuell\SwissSTR_Daten")
RAW_ARCHIVE = os.path.join(ONEDRIVE_DATA, "raw", "airbnb")        # ① unveränderlich, dated
HISTORY_DIR = os.path.join(ONEDRIVE_DATA, "history", "airbnb")    # ② Zeitreihe, append-only JSONL

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


def _median(vals):
    s = sorted(v for v in vals if v is not None)
    if not s:
        return None
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


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


def _reviews_per_month(rec, reviews_count):
    """Reviews/Monat aus den Review-Datumsangaben (reviews_details) — echtes Velocity-Signal."""
    rd = rec.get("reviews_details")
    dates = []
    if isinstance(rd, list):
        for rv in rd:
            d = rv.get("review_date") if isinstance(rv, dict) else None
            if not d:
                continue
            try:
                dates.append(datetime.fromisoformat(str(d).replace("Z", "+00:00")))
            except ValueError:
                pass
    if reviews_count and dates:
        earliest = min(dates)
        now = datetime.now(earliest.tzinfo) if earliest.tzinfo else datetime.now()
        months = max(1.0, (now - earliest).days / 30.4)
        return round(reviews_count / months, 2)
    return None


def normalize(rec):
    """BD-Airbnb-Record → schlankes SwissSTR-Schema (echte BD-Feldnamen, Stand 2026-06)."""
    name = rec.get("name") or rec.get("listing_name") or rec.get("listing_title") or "Inserat"
    name = str(name)
    m_bed = re.search(r"(\d+)\s*bedroom", name)
    bedrooms = float(m_bed.group(1)) if m_bed else None
    room_type = name.split(" in ")[0].strip() if " in " in name else None  # "Entire rental unit", "Treehouse", …
    reviews_count = _to_float(rec.get("property_number_of_reviews"))
    rpm = _reviews_per_month(rec, reviews_count)
    host = rec.get("host_details") if isinstance(rec.get("host_details"), dict) else {}
    return {
        "id": _first(rec, "property_id", "id"),
        "name": name,
        "url": _first(rec, "url", "final_url"),
        "room_type": room_type,
        "bedrooms": bedrooms,
        "guests": _to_float(rec.get("guests")),
        "price_usd": _to_float(rec.get("total_price")),  # Stay-Total, USD (Currency-Param)
        "rating": _to_float(_first(rec, "ratings", "rating")),
        "reviews_count": int(reviews_count) if reviews_count else None,
        "reviews_per_month": rpm,
        "occupancy_proxy_pct": occupancy_proxy(rpm),
        "host_id": host.get("host_id"),
        "host_name": host.get("name"),
        "is_superhost": bool(rec.get("is_supperhost")),  # BD-Feldname hat den Tippfehler
        "host_listings_count": None,  # wird in write_market aus Host-Häufigkeit im Markt gesetzt
        "is_pro_host": False,         # dito (Superhost ODER mehrere Inserate)
    }


def append_history(market, listings):
    """② Zeitreihe: eine Zeile pro Inserat pro Beobachtung (append-only JSONL in OneDrive).
    Das ist die Basis für 3-Jahres-Trends. Fällt sauber aus, wenn OneDrive-Pfad fehlt."""
    try:
        os.makedirs(HISTORY_DIR, exist_ok=True)
    except OSError as e:
        print(f"[airbnb] WARN: History-Ordner nicht erreichbar ({e}) — Zeitreihe übersprungen.")
        return None
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(HISTORY_DIR, f"{market.lower()}.jsonl")
    # Tages-Guard: schon heute für diesen Markt erfasst? Dann nicht doppelt anhängen.
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            if any(f'"date": "{day}"' in ln for ln in fh):
                print(f"[airbnb] Zeitreihe: {market} heute ({day}) bereits erfasst — uebersprungen.")
                return path
    with open(path, "a", encoding="utf-8") as fh:
        for l in listings:
            fh.write(json.dumps({
                "date": day, "market": market, "property_id": l["id"],
                "price_usd": l["price_usd"], "reviews_count": l["reviews_count"],
                "reviews_per_month": l["reviews_per_month"], "occ_proxy": l["occupancy_proxy_pct"],
                "rating": l["rating"], "bedrooms": l["bedrooms"],
                "room_type": l["room_type"], "is_pro_host": l["is_pro_host"],
            }, ensure_ascii=False) + "\n")
    return path


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
    # Vollzeit-Profi = Superhost ODER derselbe Host mit >1 Inserat in diesem Markt.
    host_freq = {}
    for l in listings:
        if l["host_id"]:
            host_freq[l["host_id"]] = host_freq.get(l["host_id"], 0) + 1
    for l in listings:
        cnt = host_freq.get(l["host_id"], 1) if l["host_id"] else 1
        l["host_listings_count"] = cnt
        l["is_pro_host"] = bool(l["is_superhost"] or cnt > 1)
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
    hist = append_history(market, listings)
    print(f"[airbnb] {market}: {len(listings)} Inserate, {pros} Profi-Hosts, "
          f"Avg-Auslastungs-Proxy {existing[market]['avg_occupancy_proxy_pct']}% -> {OUT_FILE}")
    if hist:
        print(f"[airbnb] Zeitreihe angehaengt -> {hist}")


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


def parse_records(raw):
    """Roh-Text (JSON-Array, {data:[]} oder NDJSON) → Liste von Records."""
    try:
        return extract_records(json.loads(raw))
    except json.JSONDecodeError:
        out = []
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
        return out


def _api_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8")


def poll_snapshot(snapshot_id, token, tries=40, wait=10):
    """Pollt Monitor-Endpoint bis 'ready', lädt dann den Snapshot als JSON."""
    import time
    prog_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
    dl_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
    for i in range(tries):
        try:
            status = json.loads(_api_get(prog_url, token)).get("status", "unknown")
        except Exception as e:
            status = f"poll-fehler ({e})"
        print(f"[airbnb] Snapshot {snapshot_id}: {status} ({i * wait}s)")
        if status == "ready":
            return _api_get(dl_url, token)
        if status in ("failed", "error"):
            sys.exit(f"Snapshot fehlgeschlagen ({status}).")
        time.sleep(wait)
    sys.exit(f"Snapshot {snapshot_id} nicht rechtzeitig fertig — spaeter: "
             f"python tools/fetch_airbnb.py --snapshot {snapshot_id} --market {snapshot_id}")


def find_snapshot_id(records):
    for r in records:
        if isinstance(r, dict) and r.get("snapshot_id") and not r.get("id"):
            return r["snapshot_id"]
    return None


def cmd_ingest(args):
    with open(args.ingest, "r", encoding="utf-8") as fh:
        raw = fh.read()
    records = parse_records(raw)
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
    # BDs Airbnb-Collector braucht Room-URLs MIT Such-Parametern (sonst error_code dead_page).
    from datetime import timedelta
    ci = (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")
    co = (datetime.now() + timedelta(days=49)).strftime("%Y-%m-%d")
    def augment(u):
        if "?" in u:
            return u
        return f"{u}?adults=2&check_in={ci}&check_out={co}&currency=USD&locale=en"
    urls = [augment(u) for u in urls]
    body = json.dumps({"input": [{"url": u, "country": "CH"} for u in urls]}).encode("utf-8")
    req = urllib.request.Request(
        SCRAPE_ENDPOINT.format(ds=DATASET_ID),
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    print(f"[airbnb] Triggere BD-Scrape fuer {len(urls)} URLs ({args.market}) ...")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:1000]
        sys.exit(f"BD-API HTTP {e.code}: {body}")
    # Bezahlte Rohantwort SOFORT sichern (vor dem Parsen), damit nichts verloren geht.
    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, f"airbnb_{args.market.lower()}.raw.txt")
    with open(raw_path, "w", encoding="utf-8") as fh:
        fh.write(raw)
    records = parse_records(raw)
    # Async: BD gibt oft nur eine snapshot_id zurück → pollen + herunterladen.
    snap = find_snapshot_id(records)
    if snap:
        print(f"[airbnb] Async-Job — polle Snapshot {snap} ...")
        raw = poll_snapshot(snap, token)
        with open(raw_path, "w", encoding="utf-8") as fh:
            fh.write(raw)
        records = parse_records(raw)
    errs = sum(1 for r in records if isinstance(r, dict) and r.get("error_code"))
    print(f"[airbnb] Rohantwort -> {raw_path} ({len(records)} Records, {errs} Fehler)")
    write_market(args.market, records, source="BD-API (scrape by URL)")


def aggregate_trends():
    """② Zeitreihe → ④ Aggregate (SOTA-Metriken: Occ · ADR · RevPAR · Supply · Profi-Anteil
    pro Markt pro Beobachtungstag + MoM-Deltas). Schreibt data/airbnb-trends.json."""
    out = {}
    if not os.path.isdir(HISTORY_DIR):
        return out
    for fn in os.listdir(HISTORY_DIR):
        if not fn.endswith(".jsonl"):
            continue
        rows = []
        with open(os.path.join(HISTORY_DIR, fn), "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln:
                    try:
                        rows.append(json.loads(ln))
                    except json.JSONDecodeError:
                        pass
        if not rows:
            continue
        market = rows[0].get("market") or fn[:-6]
        by_date = {}
        for r in rows:
            by_date.setdefault(r.get("date"), []).append(r)
        series = []
        for date in sorted(k for k in by_date if k):
            recs = by_date[date]
            occs = [r["occ_proxy"] for r in recs if r.get("occ_proxy") is not None]
            occ = round(sum(occs) / len(occs), 1) if occs else None          # Markt-Ø (= Röntgen)
            supply = len({r.get("property_id") for r in recs if r.get("property_id")})
            pros = sum(1 for r in recs if r.get("is_pro_host"))
            # ADR/RevPAR bewusst NULL: BD liefert ein Aufenthalts-Total (kein Nacht-ADR) + oft leer
            # → ehrlich „ausstehend" statt falscher RevPAR. Folge-Schritt: sauberer CHF-Nacht-Preis.
            series.append({"date": date, "occ": occ, "adr_chf": None, "revpar_chf": None,
                           "supply": supply, "pro_share": round(pros / len(recs) * 100) if recs else None})
        latest = series[-1]
        trend = {}
        if len(series) >= 2:
            prev = series[-2]
            if latest["occ"] is not None and prev["occ"] is not None:
                trend["occ_delta_pp"] = round(latest["occ"] - prev["occ"], 1)
            trend["supply_delta"] = latest["supply"] - prev["supply"]
        out[market] = {"latest": latest, "series": series, "trend": trend, "points": len(series)}
    return out


def cmd_aggregate(args):
    trends = aggregate_trends()
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRENDS_FILE, "w", encoding="utf-8") as fh:
        json.dump(trends, fh, ensure_ascii=False, indent=2)
    pts = {m: t["points"] for m, t in trends.items()}
    print(f"[airbnb] Trends aggregiert: {len(trends)} Maerkte -> {TRENDS_FILE} | Datenpunkte: {pts}")


def cmd_snapshot(args):
    _load_dotenv()
    token = os.environ.get("BRIGHTDATA_API_KEY")
    if not token:
        sys.exit("BRIGHTDATA_API_KEY fehlt (.env).")
    raw = poll_snapshot(args.snapshot, token)
    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, f"airbnb_{args.market.lower()}.raw.txt")
    with open(raw_path, "w", encoding="utf-8") as fh:
        fh.write(raw)
    records = parse_records(raw)
    errs = sum(1 for r in records if isinstance(r, dict) and r.get("error_code"))
    print(f"[airbnb] Snapshot -> {raw_path} ({len(records)} Records, {errs} Fehler)")
    write_market(args.market, records, source=f"BD-Snapshot {args.snapshot}")


def main():
    ap = argparse.ArgumentParser(description="Airbnb-Konkurrenz -> SwissSTR Konkurrenz-Roentgen")
    ap.add_argument("--market", help="Marktname (z.B. Aarau) — Key in der JSON (Pflicht ausser bei --aggregate)")
    ap.add_argument("--ingest", help="Pfad zu heruntergeladenem BD-Export (kein Token nötig)")
    ap.add_argument("--fetch", action="store_true", help="Per BD-API holen (Token aus .env)")
    ap.add_argument("--urls", help="Datei mit Airbnb-Room-URLs (eine pro Zeile) für --fetch")
    ap.add_argument("--snapshot", help="Bestehende Snapshot-ID herunterladen (kein neuer Scrape)")
    ap.add_argument("--aggregate", action="store_true", help="Zeitreihe -> data/airbnb-trends.json aggregieren")
    args = ap.parse_args()
    if args.aggregate:
        cmd_aggregate(args)
        return
    if not args.market:
        ap.error("--market ist Pflicht (ausser bei --aggregate).")
    if args.ingest:
        cmd_ingest(args)
    elif args.snapshot:
        cmd_snapshot(args)
    elif args.fetch:
        cmd_fetch(args)
    else:
        ap.error("--ingest <datei>, --fetch, --snapshot <id> oder --aggregate angeben.")


if __name__ == "__main__":
    main()
