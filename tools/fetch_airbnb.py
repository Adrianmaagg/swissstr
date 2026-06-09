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
import hashlib
import json
import math
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")             # lokaler Zwischenspeicher (gitignored)
OUT_FILE = os.path.join(DATA_DIR, "airbnb-competitors.json")  # Serving-Schicht (git, aktueller Snapshot)
TRENDS_FILE = os.path.join(DATA_DIR, "airbnb-trends.json")    # Serving-Schicht: Zeitreihen-Aggregate
INSIGHTS_FILE = os.path.join(DATA_DIR, "airbnb-insights.json")  # Serving-Schicht: Review-ABSA

# ══════════════════════════ SCRAPER CONTRACT (docs/scraper-contract.md) ══════════════════════════
# Kein Snapshot ohne Signatur. Kein Vergleich ohne gleiche Parameter. Kein Trust ohne reproduzierbaren Scrape.
# Alles ADDITIV + rueckwaertskompatibel: bestehende JSON-Keys bleiben, Contract-Felder kommen dazu.
CONTRACT_VERSION = "1.0"
CENTERS_FILE = os.path.join(DATA_DIR, "market-centers.json")
RUNS_FILE = os.path.join(DATA_DIR, "airbnb-scrape-runs.json")  # append-only Run-Log (Signaturen, fuer Platform-Drift)
DEFAULT_RADIUS_KM = 8


def load_market_centers():
    try:
        with open(CENTERS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def market_center(market, centers=None):
    centers = centers if centers is not None else load_market_centers()
    c = centers.get(market)
    return c if (isinstance(c, dict) and c.get("lat") is not None) else None


def haversine_km(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return None
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(min(1, math.sqrt(a))), 2)


def precise_query(market, centers=None):
    """Praezise Query gegen Namenskollision: 'Grenchen, Solothurn, Switzerland'."""
    c = market_center(market, centers)
    canton = (c or {}).get("canton")
    return f"{market}, {canton}, Switzerland" if canton else f"{market}, Switzerland"


def _median_num(xs):
    xs = sorted(v for v in xs if v is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else round((xs[n // 2 - 1] + xs[n // 2]) / 2, 2)


def enrich_geo(listings, center, radius_km):
    """ADDITIV pro Listing: distance_to_market_center_km + in_market_radius. Loescht NICHTS.
    Gibt (in_market_share, median_distance_km, max_distance_km) zurueck."""
    if not center:
        for l in listings:
            l.setdefault("distance_to_market_center_km", None)
            l.setdefault("in_market_radius", None)
        return (None, None, None)
    dists = []
    for l in listings:
        d = haversine_km(center.get("lat"), center.get("lng"), l.get("lat"), l.get("long"))
        l["distance_to_market_center_km"] = d
        l["in_market_radius"] = (d is not None and d <= radius_km)
        if d is not None:
            dists.append(d)
    if not dists:
        return (None, None, None)
    inside = sum(1 for d in dists if d <= radius_km)
    return (round(inside / len(dists) * 100), _median_num(dists), round(max(dists), 1))


def build_snapshot_signature(market, run_meta, listings):
    """Stabile Signatur je Scrape-Lauf — Basis fuer compareScrapeSignatures / Platform-Drift."""
    ids = sorted(str(l.get("id")) for l in listings if l.get("id"))
    id_hash = hashlib.sha1("|".join(ids).encode("utf-8")).hexdigest()[:16] if ids else None
    prices = [l.get("normalized_nightly_price") if l.get("normalized_nightly_price") is not None else l.get("price_usd")
              for l in listings]
    prices = [p for p in prices if p]
    ent = [l for l in listings if l.get("is_entire") is True]
    cal = [l for l in listings if l.get("occ_method") == "calendar"]
    rev = [l for l in listings if l.get("occ_method") == "reviews"]
    pm = {}
    for l in listings:
        pm[l.get("price_mode") or "unknown"] = pm.get(l.get("price_mode") or "unknown", 0) + 1
    dists = [l.get("distance_to_market_center_km") for l in listings if l.get("distance_to_market_center_km") is not None]
    inside = sum(1 for d in dists if d <= run_meta.get("requested_radius_km", DEFAULT_RADIUS_KM)) if dists else 0
    adr_sorted = sorted(prices)
    def _q(p):
        return adr_sorted[int(p * (len(adr_sorted) - 1))] if adr_sorted else None
    n = len(listings) or 1
    return {
        "market": market,
        "timestamp": run_meta.get("timestamp"),
        "query": run_meta.get("query"),
        "check_in": run_meta.get("check_in"), "check_out": run_meta.get("check_out"),
        "stay_length": run_meta.get("stay_length"),
        "currency": run_meta.get("currency"),
        "room_type": run_meta.get("room_type"),
        "geo_filter_mode": run_meta.get("geo_filter_mode"),
        "requested_radius_km": run_meta.get("requested_radius_km"),
        "result_count": len(listings),
        "listing_ids": ids,
        "listing_ids_hash": id_hash,
        "median_distance_km": _median_num(dists),
        "in_market_share": round(inside / len(dists) * 100) if dists else None,
        "adr_median": _median_num(prices),
        "adr_iqr": (round(_q(0.75) - _q(0.25), 2) if len(adr_sorted) >= 4 else None),
        "entire_home_share": round(len(ent) / n * 100),
        "calendar_share": round(len(cal) / n * 100),
        "review_share": round(len(rev) / n * 100),
        "price_mode_share": {k: round(v / n * 100) for k, v in pm.items()},
        "contract_version": CONTRACT_VERSION,
    }


def build_run_metadata(market, query, scraper_mode, source_mode, check_in, check_out,
                       stay_length, currency, center, radius_km, geo_filter_mode, guests=2, room_type="entire_home"):
    return {
        "run_id": hashlib.sha1(f"{market}|{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market": market, "canonical_market_name": market, "query": query,
        "scraper_mode": scraper_mode, "source_mode": source_mode,
        "check_in": check_in, "check_out": check_out, "stay_length": stay_length,
        "guests": guests, "bedrooms": None, "room_type": room_type, "property_type": None,
        "currency": currency, "locale": "en", "country": "CH",
        "market_center": ({"lat": center.get("lat"), "lng": center.get("lng")} if center else None),
        "requested_radius_km": radius_km, "map_bounds": None, "geo_filter_mode": geo_filter_mode,
        "contract_version": CONTRACT_VERSION,
    }


def append_scrape_run(run_meta, signature):
    """Append-only Run-Log (additiv, beruehrt bestehende JSONs nicht)."""
    runs = []
    if os.path.isfile(RUNS_FILE):
        try:
            runs = json.load(open(RUNS_FILE, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            runs = []
    if not isinstance(runs, list):
        runs = []
    runs.append({"run": run_meta, "signature": signature})
    runs = runs[-500:]  # bounded
    try:
        with open(RUNS_FILE, "w", encoding="utf-8") as fh:
            json.dump(runs, fh, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[airbnb] WARN Run-Log: {e}")


def price_contract(price_raw, price_mode, currency, stay_length):
    """Einheitliche Preis-Normalisierung (F): raw + mode + normalized_nightly_price."""
    if price_raw is None:
        return {"price_raw": None, "price_currency": currency, "price_mode": "unknown",
                "normalized_nightly_price": None}
    if price_mode == "stay_total" and stay_length:
        norm = round(price_raw / stay_length, 2)
    elif price_mode == "nightly":
        norm = round(price_raw, 2)
    else:
        norm = None
    return {"price_raw": round(price_raw, 2), "price_currency": currency,
            "price_mode": price_mode, "normalized_nightly_price": norm}
# ════════════════════════ /SCRAPER CONTRACT ════════════════════════

# ── Aspect-Based Sentiment (DE+EN-Lexikon) — transparent, kein LLM. Richtung, nicht Praezision. ──
ASPECTS = {
    "Lage":          ["lage", "location", "zentral", "central", "ruhig", "quiet", "bahnhof", "station",
                      "zentrum", "altstadt", "walk", "gehdistanz", "erreichbar", "nahe", "near", "see", "lake", "view", "aussicht"],
    "Sauberkeit":    ["sauber", "clean", "cleanliness", "spotless", "dreckig", "dirty", "schmutz", "gepflegt", "hygien"],
    "Preis/Wert":    ["preis", "price", "value", "wert", "guenstig", "günstig", "cheap", "teuer", "expensive", "worth", "preis-leistung"],
    "Host/Komm.":    ["host", "gastgeber", "kommunikation", "communication", "responsive", "friendly", "freundlich",
                      "hilfsbereit", "helpful", "antwort", "responsive", "unkompliziert", "welcoming", "herzlich"],
    "Ausstattung":   ["kueche", "küche", "kitchen", "wifi", "wlan", "ausstattung", "equipped", "amenities", "bett", "bed",
                      "dusche", "shower", "bad", "bathroom", "waschmaschine", "washer", "parkplatz", "parking", "klimaanlage", "balkon", "ausgestattet"],
    "Laerm":         ["laut", "noise", "noisy", "laerm", "lärm", "hellhoerig", "hellhörig", "ruhestoer", "strasse", "street noise"],
    "Check-in":      ["check-in", "checkin", "check in", "schluessel", "schlüssel", "key", "self check", "einchecken", "self-check", "ankunft", "keybox", "smart lock", "smartlock"],
}
POS_CUES = ["super", "great", "perfekt", "perfect", "schoen", "schön", "beautiful", "wunderschoen", "wunderschön",
            "top", "empfehl", "recommend", "wonderful", "amazing", "comfortable", "gemuetlich", "gemütlich", "ideal",
            "loved", "liebe", "toll", "excellent", "ausgezeichnet", "fantastic", "fantastisch", "angenehm", "traum",
            "hervorragend", "lovely", "magisch", "highly", "sehr gut", "sehr schoen", "spotless", "freundlich", "sauber"]
NEG_CUES = ["leider", "unfortunately", "problem", "dirty", "dreckig", "laut", "noisy", "broken", "kaputt", "klein",
            "small", "cold", "kalt", "uncomfortable", "enttaeusch", "enttäusch", "schlecht", "bad ", "nicht sauber",
            "fehlt", "fehlte", "missing", "lacking", "kein ", "no hot water", "smell", "geruch", "mangel", "nervig"]


def _sentiment(text_lower):
    pos = sum(text_lower.count(c) for c in POS_CUES)
    neg = sum(text_lower.count(c) for c in NEG_CUES)
    if neg > pos:
        return "neg"
    if pos > 0:
        return "pos"
    return "neu"


def analyze_market_reviews(records):
    """ABSA ueber alle Review-Texte eines Marktes -> Aspekt-Statistik + Beispiele."""
    stats = {a: {"pos": 0, "neg": 0, "examples": []} for a in ASPECTS}
    total = 0
    for r in records:
        if not isinstance(r, dict):
            continue
        for rv in (r.get("reviews_details") or []):
            text = (rv.get("review") or "").strip() if isinstance(rv, dict) else ""
            if not text or len(text) < 8:
                continue
            total += 1
            tl = text.lower()
            senti = _sentiment(tl)
            for asp, lex in ASPECTS.items():
                if any(kw in tl for kw in lex):
                    if senti == "pos":
                        stats[asp]["pos"] += 1
                    elif senti == "neg":
                        stats[asp]["neg"] += 1
                    if senti != "neu" and len(stats[asp]["examples"]) < 2:
                        stats[asp]["examples"].append({"s": senti, "t": text[:160]})
    # Klare Trennung: loben = deutlich positiv (pos > 2x neg); bemaengeln = spuerbar negativ
    # (neg >= 40% von pos). So landet ein Aspekt nicht gleichzeitig in beiden Listen.
    loben = sorted([a for a, s in stats.items() if s["pos"] >= 3 and s["pos"] > s["neg"] * 2],
                   key=lambda a: -stats[a]["pos"])[:3]
    maengel = sorted([a for a, s in stats.items() if s["neg"] >= 2 and s["neg"] >= s["pos"] * 0.4],
                     key=lambda a: -stats[a]["neg"])[:3]
    return {
        "reviews_analyzed": total,
        "aspects": {a: {"pos": s["pos"], "neg": s["neg"]} for a, s in stats.items()},
        "loben": loben,
        "bemaengeln": maengel,
        "examples": {a: stats[a]["examples"] for a in ASPECTS if stats[a]["examples"]},
    }

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

# ── Preis/Währung ─────────────────────────────────────────────────────────────
STAY_NIGHTS = 7        # Scrape-Fenster = heute+42 .. +49 Tage (siehe augment) → 7 Nächte
# USD→CHF: dokumentierter Kurs (🟡 MOD), Stand 2026-06-05 ≈ 0.79 (tradingeconomics.com).
# Über env SWISSSTR_USD_CHF überschreibbar, sobald ein Live-FX-Feed da ist.
USD_CHF = float(os.environ.get("SWISSSTR_USD_CHF", "0.79"))


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


def _future_avail(available_dates, horizon_days=365):
    """Freie Zukunfts-Tage (ISO-Strings), getrimmt auf die naechsten `horizon_days` — für die
    Zeitreihe (Tag-zu-Tag-Diff → Buchungs-Erkennung, Lead-Time)."""
    if not isinstance(available_dates, list):
        return []
    today = datetime.now().date()
    horizon = today + timedelta(days=horizon_days)
    out = []
    for s in available_dates:
        try:
            d = datetime.fromisoformat(str(s)[:10]).date()
            if today <= d <= horizon:
                out.append(d.isoformat())
        except (ValueError, TypeError):
            pass
    return sorted(out)


def calendar_occupancy(available_dates, window=90):
    """Kalender-Belegung = SOTA-Occupancy (AirDNA „Booking Pace"): Anteil der naechsten `window`
    Tage, die NICHT verfuegbar sind (gebucht ODER vom Host blockiert → Obergrenze). 0–95%.
    Viel belastbarer als der Review-Proxy."""
    if not isinstance(available_dates, list):
        return None
    today = datetime.now().date()
    horizon = today + timedelta(days=window)
    free = 0
    for s in available_dates:
        try:
            d = datetime.fromisoformat(str(s)[:10]).date()
            if today <= d <= horizon:
                free += 1
        except (ValueError, TypeError):
            pass
    return round(max(0.0, min(95.0, (1 - free / window) * 100)), 1)


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


# R2R braucht die GANZE Einheit (kein Privat-/Geteilt-/Hotelzimmer). Airbnb labelt
# Nicht-Entire explizit im Titel ("Room in …", "Private room …", "Shared room", "Hotel room").
# Das Signal sitzt im ROHFELD listing_name/title — NICHT im abgeleiteten room_type:
# "Rental unit in Zug" steht im `name` fuer Entire UND Room (mehrdeutig). Dreiwertig:
#   True = ganze Einheit · False = Zimmer/geteilt · None = kein erkennbarer Marker (unbekannt).
_ROOM_MARKER = re.compile(r"^\s*(private room|shared room|hotel room|room)\b", re.I)


def is_entire(title):
    t = (str(title) if title is not None else "").strip()
    if not t:
        return None
    if t.lower().startswith("entire"):
        return True
    if _ROOM_MARKER.match(t):
        return False
    return True  # erkannter Property-Typ ohne Room-Marker (Farm stay, Treehouse, …) = ganze Einheit


def normalize(rec):
    """BD-Airbnb-Record → schlankes SwissSTR-Schema (echte BD-Feldnamen, Stand 2026-06)."""
    name = rec.get("name") or rec.get("listing_name") or rec.get("listing_title") or "Inserat"
    name = str(name)
    # Entire-vs-Room aus dem Rohtitel mit Prefix (listing_name/title), nicht aus `name`.
    is_ent = is_entire(rec.get("listing_name") or rec.get("listing_title") or rec.get("name"))
    m_bed = re.search(r"(\d+)\s*bedroom", name)
    bedrooms = float(m_bed.group(1)) if m_bed else None
    room_type = name.split(" in ")[0].strip() if " in " in name else None  # "Entire rental unit", "Treehouse", …
    reviews_count = _to_float(rec.get("property_number_of_reviews"))
    rpm = _reviews_per_month(rec, reviews_count)
    occ_cal = calendar_occupancy(rec.get("available_dates"))   # SOTA: echte Kalender-Belegung
    occ_rev = occupancy_proxy(rpm)                              # Fallback: Review-Velocity
    occ = occ_cal if occ_cal is not None else occ_rev
    occ_method = "calendar" if occ_cal is not None else ("reviews" if occ_rev is not None else None)
    # Verfügbarkeits-Summary (fürs Serving / die App): nächster freier Tag + freie Tage in 7/30 T.
    avail = _future_avail(rec.get("available_dates"))
    _today = datetime.now().date()
    _d7 = (_today + timedelta(days=7)).isoformat()
    _d30 = (_today + timedelta(days=30)).isoformat()
    next_free = avail[0] if avail else None
    free_7d = sum(1 for d in avail if d <= _d7)
    free_30d = sum(1 for d in avail if d <= _d30)
    host = rec.get("host_details") if isinstance(rec.get("host_details"), dict) else {}
    # Nacht-Preis (USD): BDs `price` ist die Nacht-Rate; sonst aus Stay-Total / Fenster-Nächte.
    _praw = _to_float(rec.get("price"))
    if _praw is not None:
        _pmode, _rawval, nightly = "nightly", _praw, round(_praw, 2)
    else:
        tot = _to_float(rec.get("total_price"))
        _pmode, _rawval = ("stay_total", tot) if tot else ("unknown", None)
        nightly = round(tot / STAY_NIGHTS, 2) if tot else None
    _pc = price_contract(_rawval, _pmode, "USD", STAY_NIGHTS)
    return {
        "id": _first(rec, "property_id", "id"),
        "name": name,
        "url": _first(rec, "url", "final_url"),
        "room_type": room_type,
        "is_entire": is_ent,
        "bedrooms": bedrooms,
        "guests": _to_float(rec.get("guests")),
        "price_usd": nightly,  # Nacht-Preis USD (Fenster +42..+49 T); CHF/RevPAR erst im aggregate
        "rating": _to_float(_first(rec, "ratings", "rating")),
        "reviews_count": int(reviews_count) if reviews_count else None,
        "reviews_per_month": rpm,
        "occupancy_proxy_pct": occ,
        "occ_method": occ_method,
        "occ_calendar_pct": occ_cal,
        "occ_reviews_pct": occ_rev,
        "host_id": host.get("host_id"),
        "host_name": host.get("name"),
        "lat": _to_float(rec.get("lat")),
        "long": _to_float(rec.get("long")),
        "location": rec.get("location"),   # listing-eigen (NICHT such-/zoom-abhängig)
        "is_superhost": bool(rec.get("is_supperhost")),  # BD-Feldname hat den Tippfehler
        "host_listings_count": None,  # wird in write_market aus Host-Häufigkeit im Markt gesetzt
        "is_pro_host": False,         # dito (Superhost ODER mehrere Inserate)
        "next_free": next_free,
        "free_7d": free_7d,
        "free_30d": free_30d,
        # ── Scraper Contract (additiv) ──
        "price_raw": _pc["price_raw"], "price_currency": _pc["price_currency"],
        "price_mode": _pc["price_mode"], "normalized_nightly_price": _pc["normalized_nightly_price"],
        "available_nights": len(avail), "unavailable_nights": None,
        "calendar_window_days": (90 if avail else None),
        "calendar_snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "_avail_dates": avail,        # transient: nur für die Zeitreihe (vor Serving gestrippt)
    }


# Sub-Lokalitäten → kanonische Gemeinde (Airbnb-location ist Inserat-eigen, aber teils Quartier-Ebene).
SUBLOCALITY = {
    "Emmenbrücke": "Emmen", "Emmenbruecke": "Emmen", "Aarau Rohr": "Aarau", "Rohr": "Aarau",
    "Kastanienbaum": "Horw", "Obernau": "Kriens", "Littau": "Luzern", "Reussbühl": "Luzern",
}


def attribute_market(listing, fallback):
    """Echte Gemeinde des Inserats — aus der listing-eigenen `location` (nicht such-/zoom-abhängig).
    So fällt ein Inserat in SEINE Gemeinde, egal wie Airbnb die Karte beim Suchen zoomt."""
    loc = (listing.get("location") or "").strip()
    town = loc.split(",")[0].strip() if loc else ""
    town = SUBLOCALITY.get(town, town)
    return town or fallback


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
            avail = l.get("_avail_dates") or []
            fh.write(json.dumps({
                "date": day, "market": market, "property_id": l["id"],
                "price_usd": l["price_usd"], "reviews_count": l["reviews_count"],
                "reviews_per_month": l["reviews_per_month"], "occ_proxy": l["occupancy_proxy_pct"],
                "rating": l["rating"], "bedrooms": l["bedrooms"],
                "room_type": l["room_type"], "is_entire": l.get("is_entire"),
                "is_pro_host": l["is_pro_host"],
                "is_superhost": l["is_superhost"],
                "avail_count": len(avail), "avail_dates": avail,  # freie Zukunfts-Tage → Buchungs-Diff
            }, ensure_ascii=False) + "\n")
    return path


def write_market(market, records, source):
    """Normalisiert + ordnet jedes Inserat seiner ECHTEN Gemeinde zu (Geo-Bucketing) und schreibt
    pro Gemeinde nach competitors.json + Zeitreihe. `market` = nur Fallback-Label / Discovery-Hinweis.
    Neutralisiert Airbnbs Karten-Zoom-Bleed (Luzern-Suche → Emmen-Inserate landen bei Emmen)."""
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
    # Geo-Bucketing: jedes Inserat in seine echte Gemeinde.
    groups = {}
    for l in listings:
        groups.setdefault(attribute_market(l, market), []).append(l)
    bleed = sum(len(g) for k, g in groups.items() if k != market)
    for gm, gl in groups.items():
        host_freq = {}
        for l in gl:
            if l["host_id"]:
                host_freq[l["host_id"]] = host_freq.get(l["host_id"], 0) + 1
        for l in gl:
            cnt = host_freq.get(l["host_id"], 1) if l["host_id"] else 1
            l["host_listings_count"] = cnt
            l["is_pro_host"] = bool(l["is_superhost"] or cnt > 1)
        pros = sum(1 for l in gl if l["is_pro_host"])
        occs = [l["occupancy_proxy_pct"] for l in gl if l["occupancy_proxy_pct"]]
        # R2R-Brille: Entire-only fuer Earnings/Pearl; alle Inserate bleiben fuer Markt-/Konkurrenz-Dichte.
        ent = [l for l in gl if l.get("is_entire") is not False]
        e_occs = [l["occupancy_proxy_pct"] for l in ent if l["occupancy_proxy_pct"]]
        existing[gm] = {
            "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": source,
            "count": len(gl),
            "entire_count": len(ent),
            "pro_host_count": pros,
            "avg_occupancy_proxy_pct": round(sum(occs) / len(occs), 1) if occs else None,
            "avg_occupancy_entire_pct": round(sum(e_occs) / len(e_occs), 1) if e_occs else None,
            "listings": gl,
        }
        # ── Scraper Contract: Geo-Distanz + Run-Metadaten + Snapshot-Signatur (additiv) ──
        _center = market_center(gm)
        _rad = (_center or {}).get("radius_km", DEFAULT_RADIUS_KM)
        _ishare, _mdist, _maxd = enrich_geo(gl, _center, _rad)
        _rm = build_run_metadata(gm, precise_query(gm), scraper_mode=source, source_mode="calendar_or_reviews",
                                 check_in=None, check_out=None, stay_length=STAY_NIGHTS, currency="USD",
                                 center=_center, radius_km=_rad, geo_filter_mode=("radius" if _center else "airbnb_default"))
        _sig = build_snapshot_signature(gm, _rm, gl)
        existing[gm]["scrape_run"] = _rm
        existing[gm]["snapshot_signature"] = _sig
        existing[gm]["geo"] = {"in_market_share": _ishare, "median_distance_km": _mdist, "max_distance_km": _maxd}
        append_scrape_run(_rm, _sig)
        append_history(gm, gl)
        print(f"[airbnb] {gm}: {len(gl)} Inserate ({len(ent)} ganze), {pros} Profi-Hosts, "
              f"Entire-Occ {existing[gm]['avg_occupancy_entire_pct']}% · Geo in-radius {_ishare}%")
    for l in listings:
        l.pop("_avail_dates", None)   # transientes Feld nicht in die schlanke Serving-JSON
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)
    extra = [k for k in groups if k != market]
    if bleed:
        print(f"[airbnb] Geo-Zuordnung: {bleed} Inserate NICHT in '{market}' -> {extra} (Karten-Bleed korrigiert)")


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
            recs0 = by_date[date]
            # Entire-only fuer ADR/RevPAR/Occ (R2R-relevant). Legacy-Zeilen ohne is_entire
            # (== None) bleiben drin → sauber ab dem ersten Lauf mit Flag, ehrlich rueckwirkend.
            recs = [r for r in recs0 if r.get("is_entire") is not False]
            occs = [r["occ_proxy"] for r in recs if r.get("occ_proxy") is not None]
            occ = round(sum(occs) / len(occs), 1) if occs else None          # Markt-Ø (Entire = Röntgen)
            supply = len({r.get("property_id") for r in recs if r.get("property_id")})
            pros = sum(1 for r in recs if r.get("is_pro_host"))
            # ADR = Median der Nacht-Preise (USD, Fenster +42..+49 T) × USD/CHF (🟡 dokumentiert).
            # RevPAR = ADR × Markt-Auslastung. Nur Inserate MIT Preis (BD liefert ~45% leer).
            prices = [r["price_usd"] for r in recs if r.get("price_usd")]
            adr_usd = _median(prices)
            adr_chf = round(adr_usd * USD_CHF) if adr_usd is not None else None
            revpar_chf = round(adr_chf * occ / 100) if (adr_chf is not None and occ is not None) else None
            # Welcher Kalendermonat liegt im Preis-Fenster (Scrape-Tag +45 T = Mitte des +42..+49-Fensters)?
            # Das UI kalibriert die BFS-Saisonkurve gegen genau diesen Monat aufs echte Niveau.
            try:
                adr_month = (datetime.fromisoformat(date).date() + timedelta(days=45)).month
            except ValueError:
                adr_month = None
            series.append({"date": date, "occ": occ, "adr_chf": adr_chf, "revpar_chf": revpar_chf,
                           "adr_n": len(prices), "adr_month": adr_month, "supply": supply,
                           "pro_share": round(pros / len(recs) * 100) if recs else None})
        latest = series[-1]
        trend = {}
        if len(series) >= 2:
            prev = series[-2]
            if latest["occ"] is not None and prev["occ"] is not None:
                trend["occ_delta_pp"] = round(latest["occ"] - prev["occ"], 1)
            trend["supply_delta"] = latest["supply"] - prev["supply"]
            if latest.get("adr_chf") is not None and prev.get("adr_chf"):
                trend["adr_delta_pct"] = round((latest["adr_chf"] - prev["adr_chf"]) / prev["adr_chf"] * 100, 1)
            if latest.get("revpar_chf") is not None and prev.get("revpar_chf"):
                trend["revpar_delta_pct"] = round((latest["revpar_chf"] - prev["revpar_chf"]) / prev["revpar_chf"] * 100, 1)
        out[market] = {"latest": latest, "series": series, "trend": trend, "points": len(series),
                       "dynamics": _booking_dynamics(by_date)}
    return out


def _booking_dynamics(by_date):
    """Vergleicht die zwei jüngsten Snapshots pro Inserat → echte Buchungen (frei→belegt),
    Lead-Time, „bestes Geschäft". Leer bei <2 Datenpunkten (= bis morgen)."""
    dates = sorted(k for k in by_date if k)
    if len(dates) < 2:
        return {}
    t_prev, t_curr = dates[-2], dates[-1]
    prev = {r["property_id"]: set(r.get("avail_dates") or []) for r in by_date[t_prev] if r.get("property_id")}
    curr = {r["property_id"]: r for r in by_date[t_curr] if r.get("property_id")}
    try:
        t0 = datetime.fromisoformat(t_curr).date()
    except ValueError:
        t0 = datetime.now().date()
    total_booked, leads, with_book, best = 0, [], 0, None
    for pid, r in curr.items():
        if pid not in prev:
            continue
        avail_now = set(r.get("avail_dates") or [])
        booked = [d for d in (prev[pid] - avail_now) if d >= t_curr]   # frei→weg, Zukunft = gebucht/blockiert
        if not booked:
            continue
        with_book += 1
        total_booked += len(booked)
        for d in booked:
            try:
                leads.append((datetime.fromisoformat(d).date() - t0).days)
            except ValueError:
                pass
        if best is None or len(booked) > best["nights"]:
            best = {"property_id": pid, "name": r.get("room_type") or "", "nights": len(booked)}
    return {
        "from": t_prev, "to": t_curr,
        "nights_booked": total_booked,
        "listings_with_bookings": with_book,
        "avg_lead_days": round(sum(leads) / len(leads)) if leads else None,
        "best": best,
    }


def cmd_discover(args):
    """Discovery: Airbnb-Inserate per STANDORT finden (keine URL-Liste noetig) -> write_market.
    Basis fuer die Perlen-Rotation: neuen Ort scannen, bewerten, ggf. in den Fokus heben.
    Liefert ~100 Inserate/Ort inkl. Kalender (available_dates) -> volle Auslastung + Kapazitaet."""
    _load_dotenv()
    token = os.environ.get("BRIGHTDATA_API_KEY")
    if not token:
        sys.exit("BRIGHTDATA_API_KEY fehlt. In swissstr/.env setzen (nie committen).")
    loc = args.discover
    trig = (f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={DATASET_ID}"
            f"&include_errors=true&type=discover_new&discover_by=location")
    body = json.dumps([{"location": loc}]).encode("utf-8")
    req = urllib.request.Request(
        trig, data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    print(f"[airbnb] Discovery fuer '{loc}' ...")
    try:
        raw = urllib.request.urlopen(req, timeout=180).read().decode("utf-8")
    except urllib.error.HTTPError as e:
        sys.exit(f"BD-Discovery HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, f"airbnb_{args.market.lower()}.raw.txt")
    with open(raw_path, "w", encoding="utf-8") as fh:
        fh.write(raw)
    records = parse_records(raw)
    snap = find_snapshot_id(records)
    if snap:
        print(f"[airbnb] Discovery-Job — polle Snapshot {snap} ...")
        raw = poll_snapshot(snap, token)
        with open(raw_path, "w", encoding="utf-8") as fh:
            fh.write(raw)
        records = parse_records(raw)
    errs = sum(1 for r in records if isinstance(r, dict) and r.get("error_code"))
    print(f"[airbnb] Discovery '{loc}' -> {raw_path} ({len(records)} Inserate, {errs} Fehler)")
    write_market(args.market, records, source=f"BD-Discovery ({loc})")


def cmd_aggregate(args):
    trends = aggregate_trends()
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRENDS_FILE, "w", encoding="utf-8") as fh:
        json.dump(trends, fh, ensure_ascii=False, indent=2)
    pts = {m: t["points"] for m, t in trends.items()}
    print(f"[airbnb] Trends aggregiert: {len(trends)} Maerkte -> {TRENDS_FILE} | Datenpunkte: {pts}")


def cmd_reviews(args):
    """Review-ABSA ueber die Roh-Dumps -> data/airbnb-insights.json (pro Markt loben/bemaengeln)."""
    out = {}
    if not os.path.isdir(RAW_DIR):
        sys.exit("Kein data/raw/ — erst scrapen.")
    for fn in sorted(os.listdir(RAW_DIR)):
        if not fn.startswith("airbnb_") or not fn.endswith(".raw.txt"):
            continue
        market = fn[len("airbnb_"):-len(".raw.txt")]
        if market.startswith("_"):
            continue
        market = market[:1].upper() + market[1:]
        with open(os.path.join(RAW_DIR, fn), "r", encoding="utf-8") as fh:
            records = [r for r in parse_records(fh.read()) if isinstance(r, dict) and not r.get("error_code")]
        if not records:
            continue
        ins = analyze_market_reviews(records)
        if ins["reviews_analyzed"] > 0:
            out[market] = ins
            print(f"[airbnb] {market}: {ins['reviews_analyzed']} Reviews | loben {ins['loben']} | bemaengeln {ins['bemaengeln']}")
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INSIGHTS_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"[airbnb] Review-Insights -> {INSIGHTS_FILE} ({len(out)} Maerkte)")


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
    ap.add_argument("--discover", help="Standort-Discovery statt URL-Liste (z.B. 'Zug, Switzerland')")
    ap.add_argument("--aggregate", action="store_true", help="Zeitreihe -> data/airbnb-trends.json aggregieren")
    ap.add_argument("--reviews", action="store_true", help="Review-ABSA -> data/airbnb-insights.json")
    args = ap.parse_args()
    if args.aggregate:
        cmd_aggregate(args)
        return
    if args.reviews:
        cmd_reviews(args)
        return
    if not args.market:
        ap.error("--market ist Pflicht (ausser bei --aggregate).")
    if args.ingest:
        cmd_ingest(args)
    elif args.snapshot:
        cmd_snapshot(args)
    elif args.discover:
        cmd_discover(args)
    elif args.fetch:
        cmd_fetch(args)
    else:
        ap.error("--ingest <datei>, --fetch, --snapshot <id> oder --aggregate angeben.")


if __name__ == "__main__":
    main()
