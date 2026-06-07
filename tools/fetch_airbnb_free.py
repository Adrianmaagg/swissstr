"""Gratis-Airbnb-Scraper (ohne Bright Data, ohne Proxy).

Holt die Airbnb-Suchseite eines Ortes, parst den eingebetteten Zustand
(`data-deferred-state-0`) und schreibt Inserate (Name, Preis, Rating, Groesse)
in data/airbnb-competitors.json -- dieselbe Struktur wie der BD-Pfad.

Bewusst OHNE Kalender/Belegung: die ist nicht im HTML (braucht BD oder Headless).
Auslastung daher als Review-Velocity-Proxy (gröber, 🟡) -- die "Booking Pace"
holen wir nur via BD fuer die vielversprechenden Maerkte.

Aufruf:  python tools/fetch_airbnb_free.py "Zug, Switzerland" --market Zug
"""
from __future__ import annotations

import argparse
import base64
import datetime
import gzip
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa  # occupancy_proxy, OUT_FILE, _to_float

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
STAY_NIGHTS = 7


def _fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "en", "Accept": "text/html",
        "Accept-Encoding": "gzip"})
    r = urllib.request.urlopen(req, timeout=30)
    raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def _money(s):
    if not s:
        return None
    digits = re.sub(r"[^\d.]", "", s.replace("’", "").replace(",", "").replace("'", ""))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def _dig(d, *ks):
    for k in ks:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def _parse_search(html):
    m = re.search(r'<script id="data-deferred-state-0"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    state = json.loads(m.group(1))
    items = []
    def walk(o):
        if isinstance(o, dict):
            if "demandStayListing" in o and "structuredDisplayPrice" in o:
                items.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(state)
    return items


def _to_listing(it):
    dl = it.get("demandStayListing") or {}
    lid_b64 = dl.get("id") or ""
    try:
        rid = base64.b64decode(lid_b64).decode().split(":")[-1]
    except Exception:
        rid = lid_b64 or None
    name = _dig(dl, "description", "name", "localizedStringWithTranslationPreference") or it.get("title")
    coord = _dig(dl, "location", "coordinate") or {}
    # Preis: primaryLine (Stay-Total bei Datumsbereich) -> Nacht
    pl = _dig(it, "structuredDisplayPrice", "primaryLine") or {}
    total = _money(pl.get("discountedPrice") or pl.get("price"))
    nightly = round(total / STAY_NIGHTS, 2) if total else None
    # Rating + Reviews aus "4.87 (47)"
    rating, reviews = None, None
    mm = re.match(r"([\d.]+)\s*\((\d+)\)", str(it.get("avgRatingLocalized") or ""))
    if mm:
        rating = float(mm.group(1)); reviews = int(mm.group(2))
    # Groesse aus structuredContent "X bedroom(s)"
    beds = None
    sc = _dig(it, "structuredContent", "primaryLine")
    blob = json.dumps(sc, ensure_ascii=False) if sc else (it.get("title") or "")
    mb = re.search(r"(\d+)\s*(?:bedroom|Schlafzimmer)", blob)
    if mb:
        beds = float(mb.group(1))
    room_type = (it.get("title") or "").split(" in ")[0].strip() or None
    # Auslastung: Review-Velocity-Proxy (grobe Annahme 24 Mt aktiv -> rpm)
    rpm = round(reviews / 24.0, 2) if reviews else None
    occ = fa.occupancy_proxy(rpm) if rpm is not None else None
    return {
        "id": rid, "name": name,
        "url": f"https://www.airbnb.com/rooms/{rid}" if rid else None,
        "room_type": room_type, "bedrooms": beds, "guests": None,
        "price_usd": nightly, "rating": rating,
        "reviews_count": reviews, "reviews_per_month": rpm,
        "occupancy_proxy_pct": occ, "occ_method": "reviews" if occ is not None else None,
        "occ_calendar_pct": None, "occ_reviews_pct": occ,
        "host_id": None, "host_name": None,
        "lat": coord.get("latitude"), "long": coord.get("longitude"),
        "location": None, "is_superhost": False, "host_listings_count": None,
        "is_pro_host": False, "next_free": None, "free_7d": None, "free_30d": None,
    }


def run(location, market):
    ci = (datetime.date.today() + datetime.timedelta(days=42)).isoformat()
    co = (datetime.date.today() + datetime.timedelta(days=49)).isoformat()
    ss = urllib.parse.quote(location)
    url = (f"https://www.airbnb.com/s/{ss}/homes?adults=2&checkin={ci}&checkout={co}"
           f"&currency=USD&locale=en")
    print(f"[free] Suche '{location}' ...")
    html = _fetch(url)
    items = _parse_search(html)
    listings = [_to_listing(it) for it in items]
    listings = [l for l in listings if l["id"]]
    if not listings:
        print("[free] Keine Inserate geparst (Seitenstruktur geaendert?).")
        return
    occs = [l["occupancy_proxy_pct"] for l in listings if l["occupancy_proxy_pct"] is not None]
    entry = {
        "fetched": datetime.datetime.now().strftime("%Y-%m-%d"),
        "source": "free-scrape (Airbnb-Suche, Review-Proxy)",
        "count": len(listings),
        "pro_host_count": 0,
        "avg_occupancy_proxy_pct": round(sum(occs) / len(occs), 1) if occs else None,
        "listings": listings,
    }
    os.makedirs(fa.DATA_DIR, exist_ok=True)
    data = {}
    if os.path.isfile(fa.OUT_FILE):
        try:
            data = json.load(open(fa.OUT_FILE, encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data[market] = entry
    with open(fa.OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    prices = [l["price_usd"] for l in listings if l["price_usd"]]
    print(f"[free] {market}: {len(listings)} Inserate, {len(prices)} mit Preis, "
          f"Ø-Auslastung(Review) {entry['avg_occupancy_proxy_pct']}% -> {fa.OUT_FILE}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("location", help="z.B. 'Zug, Switzerland'")
    ap.add_argument("--market", required=True, help="Markt-Key (z.B. Zug)")
    a = ap.parse_args()
    run(a.location, a.market)
