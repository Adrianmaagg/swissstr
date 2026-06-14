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
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa  # occupancy_proxy, OUT_FILE, _to_float

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
STAY_NIGHTS = 7
# Contract G (scraper-contract.md): Discovery MUSS mehrere Zukunfts-Fenster scannen — die Suche zeigt nur
# FREIE Inserate, ein Nah-Fenster uebersieht die ausgebuchten Top-Performer (Guest Favorites). Darum
# zusaetzlich zum Referenz-Fenster (+42, treibt Preis/Signatur) weitere Fenster ziehen und listingIds unionen.
DISCOVERY_EXTRA_OFFSETS = [21, 90, 150]   # ~3 Wochen / ~3 Monate / ~November (ab heute), zusaetzlich zu +42
DISCOVERY_STAY = 3                        # kurzer Probe-Aufenthalt = maximale Verfuegbarkeits-Oberflaeche


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


# ── Kalender pro Inserat (GRATIS, oeffentlicher PdpAvailabilityCalendar-Endpoint) ──
# Entdeckt 2026-06-12: der Free-Pfad KANN doch Kalender — nicht im Such-HTML, aber ueber
# einen zweiten oeffentlichen GraphQL-Endpoint je Inserat (gleicher Weg wie Inside Airbnb).
# Liefert pro Tag available true/false ueber ~6 Monate. Das schliesst die Auslastungs-OBERGRENZE
# (v0.9.101-Spanne) auch im Free-Pfad — vorher BD-only.
AIRBNB_PUBLIC_KEY = "d306zoyjsyarp7ifhu67rjxn52tv0t20"   # Airbnbs oeffentlicher Web-Client-Key (in jeder Seite)
CAL_SHA = "8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade"  # persisted-query PdpAvailabilityCalendar
CAL_MONTHS = 6                # Horizont: ~183 Tage
CAL_PACE_S = 0.7              # Hoeflichkeits-Pause je Inserat (Sperr-Vermeidung statt Proxy)
CAL_MAX_LISTINGS = 80         # harter Deckel je Markt (Runaway/Rate-Limit-Schutz)


def fetch_calendar(listing_id):
    """Holt die Tages-Verfuegbarkeit eines Inserats. Gibt sortierte Liste von
    (datum_iso, available_bool) zurueck, oder None bei Fehler/leer."""
    now = datetime.datetime.now(datetime.timezone.utc)
    variables = {"request": {"count": CAL_MONTHS, "listingId": str(listing_id),
                             "month": now.month, "year": now.year}}
    ext = {"persistedQuery": {"version": 1, "sha256Hash": CAL_SHA}}
    qs = urllib.parse.urlencode({
        "operationName": "PdpAvailabilityCalendar", "locale": "en", "currency": "CHF",
        "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps(ext, separators=(",", ":")),
    })
    url = f"https://www.airbnb.com/api/v3/PdpAvailabilityCalendar/{CAL_SHA}?{qs}"
    req = urllib.request.Request(url, headers={
        "X-Airbnb-API-Key": AIRBNB_PUBLIC_KEY, "User-Agent": UA,
        "Accept": "application/json", "Accept-Encoding": "gzip"})
    try:
        r = urllib.request.urlopen(req, timeout=25)
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        data = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        return None
    months = (_dig(data, "data", "merlin", "pdpAvailabilityCalendar", "calendarMonths") or [])
    days = []
    for m in months:
        for d in (m.get("days") or []):
            dt = d.get("calendarDate")
            if dt:
                days.append((dt, bool(d.get("available"))))
    days.sort()
    return days or None


def classify_calendar(days):
    """Adrians Heuristik 'gebucht vs. host-geblockt' aus dem Tages-Muster.

    Das v0.9.101-Problem: 'nicht verfuegbar' = gebucht ODER host-gesperrt, untrennbar in
    einem Snapshot. Adrians Beobachtung loest es naeherungsweise ueber die FORM der Sperre:
      - ganze Monate am Stueck dicht (ein dominanter Langblock) -> host-geblockt/privat -> NICHT als Nachfrage
      - alles andere (verstreute Buchungen ODER viel frei)      -> echtes Marktsignal -> zaehlt

    Wichtig (Korrektur 1. Wurf): NUR der dominante Langblock ist 'geblockt'. Ein fast LEERES
    Inserat (7% belegt, ein grosser Frei-Block) ist NICHT geblockt — es ist schwach gebucht,
    und schwache Nachfrage ist ein ehrliches Signal, das zaehlen muss.

    block_suspect = laengster Nicht-verfuegbar-Block ist >=45 Tage UND macht >=70% ALLER
    nicht-verfuegbaren Tage aus (= eine einzige lange Sperre, nicht verstreute Buchungen).

    Liefert: occ_pct (Anteil nicht-verfuegbar = Auslastungs-Obergrenze), managed (bool),
    longest_block_days, gap_count, unavail_days. Heuristik, kein gemessener Ist-Wert."""
    if not days:
        return None
    n = len(days)
    unavail = sum(1 for _, a in days if not a)
    occ_pct = round(unavail / n * 100)
    # Laengster zusammenhaengender Nicht-verfuegbar-Block + Anzahl getrennter Frei-Luecken
    longest, cur, gaps, in_gap = 0, 0, 0, False
    for _, a in days:
        if not a:
            cur += 1; longest = max(longest, cur)
            in_gap = False
        else:
            cur = 0
            if not in_gap:
                gaps += 1; in_gap = True
    block_share = (longest / unavail) if unavail else 0
    block_suspect = (longest >= 45) and (block_share >= 0.70)
    managed = not block_suspect
    return {"occ_pct": occ_pct, "managed": managed,
            "longest_block_days": longest, "gap_count": gaps,
            "unavail_days": unavail, "calendar_days": n}


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
    # Preis: primaryLine (Stay-Total bei Datumsbereich) -> Nacht. price_mode explizit = stay_total (Contract F).
    pl = _dig(it, "structuredDisplayPrice", "primaryLine") or {}
    total = _money(pl.get("discountedPrice") or pl.get("price"))
    nightly = round(total / STAY_NIGHTS, 2) if total else None
    pc = fa.price_contract(total, "stay_total" if total else "unknown", "USD", STAY_NIGHTS)
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
    # Entire-vs-Room aus dem Suchtitel ("Apartment in Stans" = Entire · "Room in Vitznau" = Zimmer).
    is_ent = fa.is_entire(it.get("title"))
    # Kapazitaet (guests) schaetzen wir aus Zimmern (Airbnb-Suche gibt keine guests):
    # Studio/1Zi -> 2P, 2Zi -> 4P, 3Zi -> 6P ... (grob, fuers Luecken-Segment). 🟡
    guests = int(beds * 2) if beds else None
    # Auslastung: Review-Velocity-Proxy (grobe Annahme 24 Mt aktiv -> rpm)
    rpm = round(reviews / 24.0, 2) if reviews else None
    occ = fa.occupancy_proxy(rpm) if rpm is not None else None
    return {
        "id": rid, "name": name,
        "url": f"https://www.airbnb.com/rooms/{rid}" if rid else None,
        "room_type": room_type, "is_entire": is_ent, "bedrooms": beds,
        "price_usd": nightly, "rating": rating,
        "reviews_count": reviews, "reviews_per_month": rpm,
        "occupancy_proxy_pct": occ, "occ_method": "reviews" if occ is not None else None,
        "occ_calendar_pct": None, "occ_reviews_pct": occ,
        "host_id": None, "host_name": None, "guests": guests,
        "lat": coord.get("latitude"), "long": coord.get("longitude"),
        "location": None, "is_superhost": False, "host_listings_count": None,
        "is_pro_host": False, "next_free": None, "free_7d": None, "free_30d": None,
        # ── Scraper Contract (additiv) ──
        "price_raw": pc["price_raw"], "price_currency": pc["price_currency"],
        "price_mode": pc["price_mode"], "normalized_nightly_price": pc["normalized_nightly_price"],
        "available_nights": None, "unavailable_nights": None, "calendar_window_days": None,
        "calendar_snapshot_date": None,  # free-Scrape hat keinen Kalender
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def run_free_scraper_preflight(market, query, bbox=None):
    """Hartes Preflight-Gate, jetzt Tier-A-bewusst.

    Der Free-Scraper hat KEINE bestaetigte Airbnb-Place-ID (kein Autocomplete-Pick). Tier A bindet
    die Geografie aber an der QUELLE via Map-Bounds (ne/sw aus EIGENEM Geocode, market-centers.json)
    statt nur per nachgelagertem Distanzfilter — das eliminiert Geo-Bleed bei Namenskollision
    (Genève→Kentucky, Wädenswil→Kanada) strukturell, weil Airbnb nur das Rechteck durchsucht.

    Die Bounds sind SYNTHETISCH (unser Zentrum), NICHT Airbnbs Place-ID. Darum bleibt
    source_tier_max 'usable' und NIE 'decision_grade' — Kalender (Auslastung nur Review-Proxy),
    Bot-Schutz und ein bestaetigter Ort fehlen weiterhin. Ohne Bounds (Markt nicht in
    market-centers.json) faellt es auf den alten Zustand zurueck: place_selection 'missing', max 'exploratory'."""
    has_bounds = bool(bbox)
    blocking = []
    if not has_bounds:
        blocking.append("keine Geo-Bindung — Textquery ist KEIN bestaetigter Ort (Namenskollision moeglich)")
    blocking.append("kein Kalender — Auslastung nur Review-Proxy (keine Booking-Pace)")
    blocking.append("keine bestaetigte Airbnb-Place-ID — Map-Bounds sind synthetisch (eigener Geocode)")
    return {
        "preflight_status": "ok" if has_bounds else "warning",
        "place_selection_status": "synthetic_bounds" if has_bounds else "missing",
        "source_tier_max": "usable" if has_bounds else "exploratory",
        "geo_filter_mode": "map_bounds" if has_bounds else "posthoc_radius_only",
        "no_airbnb_place_selection": True,
        "map_bounds": bbox,
        "blocking_reasons": blocking,
        "required_next_step": ("Fuer decision-grade: BD-Discovery (Kalender + bestaetigter Ort)"
                               if has_bounds else
                               "Marktzentrum in market-centers.json ergaenzen (Map-Bounds) ODER BD-Discovery"),
        "market": market, "query": query,
    }


def source_tier_from_geo(in_market_share, has_bounds=True):
    """Post-Scrape Source-Tier aus inMarketShare. Ohne Place-Selection NIE 'decision_grade'.
    Ohne Map-Bounds (kein Geocode) zudem hoechstens 'exploratory' — eine reine Textquery bleibt schwach.
    0% -> unusable · 1-69% -> exploratory · >=70% (mit Bounds) -> usable (Maximum)."""
    if in_market_share is None or in_market_share == 0:
        return "unusable"
    if not has_bounds or in_market_share < 70:
        return "exploratory"
    return "usable"


# ── Map-Bounding-Box-Sweep (Quadtree) ──────────────────────────────────────
# Warum: eine Airbnb-Suche ist bei ~300 / 15-17 Seiten gedeckelt, und die eingebettete
# Suchseite liefert ohnehin nur EINE Kartenansicht (~18-44, viele Dupes). Pagination via
# items_offset ist auf diesem Endpoint tot (empirisch). Lösung = Geografie zerlegen: jede
# kleine ne/sw-Box liefert ihre eigenen ~18 Inserate. Wird eine Box "voll" zurückgegeben,
# vierteln wir sie weiter (Quadtree), sonst ist sie erschöpft. Union = (fast) Vollabdeckung.
# Nebeneffekt: Suche nach KOORDINATEN-Box statt Ortsname → Namenskollisions-Bleed strukturell weg.
BOX_FULL = 17          # >= so viele Treffer in einer Box => dichter, weiter vierteln
SWEEP_PACE_S = 0.8     # Höflichkeits-Pause zwischen Box-Requests (Sperr-Vermeidung statt Proxy)
SWEEP_MAX_REQUESTS = 160  # harter Deckel je Markt (Schutz vor Runaway / Rate-Limit)


def _box_url(ci, co, nelat, nelng, swlat, swlng, zoom):
    return ("https://www.airbnb.com/s/homes?adults=2"
            f"&checkin={ci}&checkout={co}&currency=USD&locale=en"
            f"&search_by_map=true&ne_lat={nelat:.6f}&ne_lng={nelng:.6f}"
            f"&sw_lat={swlat:.6f}&sw_lng={swlng:.6f}&zoom={zoom}")


def _fetch_box(ci, co, box, zoom, stats):
    """Eine Kachel abfragen → Liste geparster Listings (mit id). Zählt Requests/Fehler in stats."""
    if stats["requests"] >= SWEEP_MAX_REQUESTS:
        return []
    url = _box_url(ci, co, box["ne_lat"], box["ne_lng"], box["sw_lat"], box["sw_lng"], zoom)
    stats["requests"] += 1
    try:
        html = _fetch(url)
    except Exception as e:
        stats["errors"] += 1
        print(f"[sweep]   box-FEHLER {type(e).__name__}: {e}")
        return []
    listings = [l for l in (_to_listing(it) for it in _parse_search(html)) if l["id"]]
    time.sleep(SWEEP_PACE_S)
    return listings


def _split_box(box):
    """Box in 4 Quadranten zerlegen."""
    mlat = (box["ne_lat"] + box["sw_lat"]) / 2
    mlng = (box["ne_lng"] + box["sw_lng"]) / 2
    return [
        {"ne_lat": box["ne_lat"], "ne_lng": box["ne_lng"], "sw_lat": mlat, "sw_lng": mlng},
        {"ne_lat": box["ne_lat"], "ne_lng": mlng, "sw_lat": mlat, "sw_lng": box["sw_lng"]},
        {"ne_lat": mlat, "ne_lng": box["ne_lng"], "sw_lat": box["sw_lat"], "sw_lng": mlng},
        {"ne_lat": mlat, "ne_lng": mlng, "sw_lat": box["sw_lat"], "sw_lng": box["sw_lng"]},
    ]


def collect_sweep(center, radius_km, ci, co, max_depth):
    """Rekursiver Quadtree-Sweep um das Marktzentrum. Gibt deduplizierte Roh-Listings + stats."""
    box0 = fa.bounding_box(center, radius_km)
    if not box0:
        return [], {"requests": 0, "errors": 0, "boxes": 0, "max_depth": 0}
    by_id = {}
    stats = {"requests": 0, "errors": 0, "boxes": 0, "max_depth": 0}

    def visit(box, depth):
        stats["boxes"] += 1
        stats["max_depth"] = max(stats["max_depth"], depth)
        zoom = min(18, fa.bbox_zoom(radius_km) + depth)
        found = _fetch_box(ci, co, box, zoom, stats)
        for l in found:
            by_id.setdefault(l["id"], l)
        # Box dicht UND Tiefe übrig UND Request-Budget übrig → weiter vierteln.
        if len(found) >= BOX_FULL and depth < max_depth and stats["requests"] < SWEEP_MAX_REQUESTS:
            for q in _split_box(box):
                visit(q, depth + 1)

    visit(box0, 0)
    return list(by_id.values()), stats


def boundary_bbox(market, buffer_km=1.0):
    """Map-Bounds aus der ECHTEN Gemeindegrenze (boundary-<m>.geojson) + Puffer — praeziser als ein
    Radius-Kreis. Adrians Punkt: 'die Map aktivieren, dann stimmt alles' — die Grenze IST die Such-Flaeche,
    kein geratener Radius. Gibt {ne/sw_lat/lng, _eff_radius_km} oder None (keine Grenze vorhanden)."""
    p = os.path.join(fa.DATA_DIR, f"boundary-{market.lower()}.geojson")
    if not os.path.isfile(p):
        return None
    try:
        g = json.load(open(p, encoding="utf-8")).get("geometry", {})
    except Exception:
        return None
    t = g.get("type")
    if t == "Polygon":
        pts = [pt for ring in g["coordinates"] for pt in ring]
    elif t == "MultiPolygon":
        pts = [pt for poly in g["coordinates"] for ring in poly for pt in ring]
    else:
        return None
    if not pts:
        return None
    lons = [pt[0] for pt in pts]; lats = [pt[1] for pt in pts]
    dlat = buffer_km / 111.0; dlon = buffer_km / 78.0   # Projekt-Konvention (CH-Breiten)
    sw_lat, ne_lat = min(lats) - dlat, max(lats) + dlat
    sw_lng, ne_lng = min(lons) - dlon, max(lons) + dlon
    eff_radius = max((ne_lat - sw_lat) * 111, (ne_lng - sw_lng) * 78) / 2.0  # halbe groessere Kante (km) -> Zoom
    return {"sw_lat": round(sw_lat, 6), "sw_lng": round(sw_lng, 6),
            "ne_lat": round(ne_lat, 6), "ne_lng": round(ne_lng, 6), "_eff_radius_km": round(eff_radius, 2)}


def run(location, market, sweep=False, max_depth=3, no_calendar=False, force=False):
    ci = (datetime.date.today() + datetime.timedelta(days=42)).isoformat()
    co = (datetime.date.today() + datetime.timedelta(days=49)).isoformat()
    # Contract E: praezise Query gegen Namenskollision (Genève→USA), wenn Marktzentrum bekannt.
    center = fa.market_center(market)
    radius = (center or {}).get("radius_km", fa.DEFAULT_RADIUS_KM)
    query = fa.precise_query(market) if (center and center.get("canton")) else location
    ss = urllib.parse.quote(query.replace("/", " "), safe="")
    url = (f"https://www.airbnb.com/s/{ss}/homes?adults=2&checkin={ci}&checkout={co}"
           f"&currency=USD&locale=en")
    # Tier A: Geo-Bindung an der QUELLE — Map-Bounds in die Suche geben (Airbnb durchsucht NUR das Rechteck).
    # Bevorzugt aus der ECHTEN Gemeindegrenze (praezise, kein geratener Radius); Fallback = Radius-Kreis.
    bbox = boundary_bbox(market)
    if bbox:
        zoom_radius = bbox.pop("_eff_radius_km"); geo_src = "Gemeindegrenze+1km"
    else:
        bbox = fa.bounding_box(center, radius); zoom_radius = radius; geo_src = f"Radius {radius}km"
    if bbox:
        url += (f"&ne_lat={bbox['ne_lat']}&ne_lng={bbox['ne_lng']}"
                f"&sw_lat={bbox['sw_lat']}&sw_lng={bbox['sw_lng']}"
                f"&zoom={fa.bbox_zoom(zoom_radius)}&search_by_map=true")
    print(f"[free] Such-Flaeche: {geo_src}")
    preflight = run_free_scraper_preflight(market, query, bbox)
    mode = "sweep" if sweep else "single"
    print(f"[free] Suche '{query}' ({mode}) ... [preflight {preflight['preflight_status']} · "
          f"geo={preflight['geo_filter_mode']} · place_selection={preflight['place_selection_status']} · "
          f"max-tier {preflight['source_tier_max']}]")
    if sweep and bbox:
        # Quadtree-Sweep: viele kleine Box-Queries statt einer → Vollabdeckung statt ~40er-Decke.
        listings, sw = collect_sweep(center, radius, ci, co, max_depth)
        # Koordinaten-Boxen liefern KEINE Ratings/Reviews (nur die Namens-Liste tut das), und beide
        # Mengen überlappen kaum (die Liste zeigt promotete/andere Inserate). Darum die Namens-Liste
        # OHNE Bounds ziehen und in den Pool UNIONEN: Sweep bringt Preis/Supply/Geo-Breite, die Liste
        # bringt den Review-Belegungs-Proxy. Overlap → Review-Felder mergen; Rest → anhängen (im Radius).
        rmerged, radded = 0, 0
        try:
            rss = urllib.parse.quote(query.replace("/", " "), safe="")
            rurl = (f"https://www.airbnb.com/s/{rss}/homes?adults=2&checkin={ci}&checkout={co}"
                    f"&currency=USD&locale=en")
            rlist = [l for l in (_to_listing(it) for it in _parse_search(_fetch(rurl)))
                     if l["id"] and l.get("reviews_count")]
            by_id = {l["id"]: l for l in listings}
            REV = ("rating", "reviews_count", "reviews_per_month",
                   "occupancy_proxy_pct", "occ_method", "occ_reviews_pct")
            for src in rlist:
                tgt = by_id.get(src["id"])
                if tgt:
                    for k in REV:
                        tgt[k] = src[k]
                    rmerged += 1
                else:
                    listings.append(src)
                    radded += 1
        except Exception as e:
            print(f"[sweep] WARN Review-Union: {e}")
        print(f"[sweep] {market}: {sw['boxes']} Boxen / {sw['requests']} Requests "
              f"(Tiefe {sw['max_depth']}, {sw['errors']} Fehler) -> {len(listings)} eindeutige Inserate "
              f"({rmerged} Review-Merge, {radded} Review-Listings dazu)")
    else:
        if sweep and not bbox:
            print("[sweep] kein Marktzentrum/Box -> Fallback Einzel-Query.")
        html = _fetch(url)
        items = _parse_search(html)
        listings = [_to_listing(it) for it in items]
        listings = [l for l in listings if l["id"]]
    if not listings:
        print("[free] Keine Inserate geparst (Seitenstruktur geaendert?).")
        return
    # ── Contract G: Mehr-Fenster-Discovery — ausgebuchte Top-Inserate sind im Nah-Fenster unsichtbar. ──
    # Referenz-Fenster (+42, oben) treibt Preis/Signatur; hier zusaetzliche Zukunfts-Fenster scannen und unionen.
    existing_ids = {l["id"] for l in listings}
    used_windows = [42]
    disc_added = 0
    for off in DISCOVERY_EXTRA_OFFSETS:
        ci_d = (datetime.date.today() + datetime.timedelta(days=off)).isoformat()
        co_d = (datetime.date.today() + datetime.timedelta(days=off + DISCOVERY_STAY)).isoformat()
        durl = (f"https://www.airbnb.com/s/{ss}/homes?adults=2&checkin={ci_d}&checkout={co_d}"
                f"&currency=USD&locale=en")
        if bbox:
            durl += (f"&ne_lat={bbox['ne_lat']}&ne_lng={bbox['ne_lng']}"
                     f"&sw_lat={bbox['sw_lat']}&sw_lng={bbox['sw_lng']}"
                     f"&zoom={fa.bbox_zoom(zoom_radius)}&search_by_map=true")
        try:
            ditems = _parse_search(_fetch(durl))
            win_new = 0
            for it in ditems:
                dl = _to_listing(it)
                if dl.get("id") and dl["id"] not in existing_ids:
                    dl["discovered_window_offset"] = off   # Herkunft transparent (Preis aus Discovery-Fenster)
                    listings.append(dl); existing_ids.add(dl["id"]); disc_added += 1; win_new += 1
            used_windows.append(off)
            print(f"[discovery] Fenster +{off}T ({ci_d}): {len(ditems)} gefunden, {win_new} neu -> Union {len(listings)}")
        except Exception as e:
            print(f"[discovery] WARN Fenster +{off}T: {e}")
    print(f"[discovery] Contract G: Fenster {used_windows} -> +{disc_added} zuvor unsichtbare Inserate (ausgebucht im Nah-Fenster).")
    # Contract E: Geo-Bleed an der Quelle. Distanz markieren (NICHT loeschen), Aggregat bevorzugt aus in-radius.
    # Bei Tier A sollte in_share jetzt hoch sein (Bounds filtern schon serverseitig); der Distanzcheck verifiziert.
    in_share, med_dist, max_dist = fa.enrich_geo(listings, center, radius)
    agg = [l for l in listings if l.get("in_market_radius")] if center else listings  # leer = ehrlich (alles ausserhalb)

    # ── Kalender-Obergrenze je in-radius-Inserat (gratis, PdpAvailabilityCalendar) ──
    if not no_calendar:
        cal_targets = agg[:CAL_MAX_LISTINGS]
        print(f"[cal] Hole Kalender fuer {len(cal_targets)} in-radius-Inserate (~{CAL_PACE_S}s/Inserat) ...")
        got = 0
        for l in cal_targets:
            days = fetch_calendar(l["id"])
            time.sleep(CAL_PACE_S)
            c = classify_calendar(days) if days else None
            if not c:
                continue
            got += 1
            l["calendar_window_days"] = c["calendar_days"]
            l["calendar_snapshot_date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            l["cal_managed"] = c["managed"]                 # Adrian-Heuristik: aktiv bewirtschaftet?
            l["cal_longest_block_days"] = c["longest_block_days"]
            l["cal_gap_count"] = c["gap_count"]
            l["cal_occ_raw_pct"] = c["occ_pct"]             # Roh-Obergrenze (inkl. Blocks) — Evidenz, transparent
            # Engine-Felder (occupancyBand liest occ_calendar_pct) NUR fuer aktiv bewirtschaftete Inserate
            # setzen — host-geblockte (ganze Monate dicht) wuerden die Obergrenze sonst kuenstlich heben (Horw-Problem).
            if c["managed"]:
                l["occ_calendar_pct"] = c["occ_pct"]
                l["occ_method"] = "calendar"               # hebt Cube von Review-Proxy auf Kalender
        print(f"[cal] {got}/{len(cal_targets)} Kalender geladen "
              f"({sum(1 for l in cal_targets if l.get('cal_managed'))} aktiv bewirtschaftet, "
              f"{sum(1 for l in cal_targets if l.get('cal_managed') is False)} Block-Verdacht).")
    occs = [l["occupancy_proxy_pct"] for l in agg if l["occupancy_proxy_pct"] is not None]
    ent = [l for l in agg if l.get("is_entire") is not False]
    e_occs = [l["occupancy_proxy_pct"] for l in ent if l["occupancy_proxy_pct"] is not None]
    # Kalender-Obergrenze: nur aus AKTIV BEWIRTSCHAFTETEN Inseraten (Adrian-Filter) — host-geblockte
    # (ganze Monate dicht) wuerden die Auslastung kuenstlich hochziehen (Horw-Inserat 180/183 = privat, nicht 98% gebucht).
    cal_managed = [l for l in ent if l.get("occ_calendar_pct") is not None and l.get("cal_managed")]
    cal_all = [l for l in ent if l.get("occ_calendar_pct") is not None]
    avg_cal_managed = round(sum(l["occ_calendar_pct"] for l in cal_managed) / len(cal_managed)) if cal_managed else None
    avg_cal_all = round(sum(l["occ_calendar_pct"] for l in cal_all) / len(cal_all)) if cal_all else None
    run_meta = fa.build_run_metadata(market, query, scraper_mode="free_sweep" if sweep else "free_search", source_mode="reviews",
                                     check_in=ci, check_out=co, stay_length=STAY_NIGHTS, currency="USD",
                                     center=center, radius_km=radius,
                                     geo_filter_mode=preflight["geo_filter_mode"])  # Tier A: map_bounds wenn Center bekannt
    run_meta["no_airbnb_place_selection"] = True
    run_meta["place_selection_status"] = preflight["place_selection_status"]
    run_meta["source_tier_max"] = preflight["source_tier_max"]
    run_meta["map_bounds"] = bbox  # synthetische Bounds (eigener Geocode) — fuer Reproduzierbarkeit/Signatur
    run_meta["discovery_windows"] = used_windows  # Contract G: welche Zukunfts-Fenster (Offset-Tage) gescannt wurden
    # Post-Scrape Source-Tier aus dem tatsaechlichen inMarketShare (0->unusable, 1-69->exploratory, >=70->usable mit Bounds).
    source_tier = source_tier_from_geo(in_share, has_bounds=bool(bbox))
    brief = ("Free-Scraper ungeeignet. BD / Browser Automation / Map-Bounds / Place-ID noetig."
             if source_tier == "unusable" else
             ("Nur Hinweis/Beobachtung — keine starke Markt-/Oekonomik-Aussage (exploratory, Place-Selection fehlt)."
              if source_tier == "exploratory" else
              "Brauchbar, aber NICHT decision-grade (Place-Selection fehlt) — vor Entscheid mit BD/Place-ID bestaetigen."))
    sig = fa.build_snapshot_signature(market, run_meta, listings)
    entry = {
        "fetched": datetime.datetime.now().strftime("%Y-%m-%d"),
        "source": "free-scrape (Airbnb-Suche, Review-Proxy)",
        "count": len(agg),                 # in-radius (Cube-relevant); Rohdaten bleiben in listings
        "count_all": len(listings),
        "entire_count": len(ent),
        "pro_host_count": 0,
        "avg_occupancy_proxy_pct": round(sum(occs) / len(occs), 1) if occs else None,
        "avg_occupancy_entire_pct": round(sum(e_occs) / len(e_occs), 1) if e_occs else None,
        # Kalender-Obergrenze (v0.9.101-Spanne, jetzt auch free): managed = Adrian-gefiltert (host-Blocks raus).
        "avg_occupancy_calendar_managed_pct": avg_cal_managed,
        "avg_occupancy_calendar_all_pct": avg_cal_all,
        "calendar_listings_managed": len(cal_managed),
        "calendar_listings_total": len(cal_all),
        "geo": {"in_market_share": in_share, "median_distance_km": med_dist, "max_distance_km": max_dist},
        # ── Preflight-Gate: ohne Place-Selection nie decision-grade ──
        "place_selection_status": preflight["place_selection_status"],
        "no_airbnb_place_selection": True,
        "source_tier": source_tier,
        "source_tier_max": preflight["source_tier_max"],
        "strategy_brief": brief,
        "scrape_run": run_meta,
        "snapshot_signature": sig,
        "listings": listings,             # ALLE (Roh-Evidenz erhalten)
    }
    if source_tier == "unusable":
        print(f"[free] {market}: source_tier=UNUSABLE (in-radius {in_share}%) — {brief}")
    os.makedirs(fa.DATA_DIR, exist_ok=True)
    data = {}
    if os.path.isfile(fa.OUT_FILE):
        try:
            data = json.load(open(fa.OUT_FILE, encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    # DRIFT-GUARD: ein degradierter Scrape (Rate-Limit/Block/Geo-Aussetzer) darf gute Daten NICHT zerstoeren.
    # Bricht die Inseratezahl ggue. dem letzten guten Stand um >50% ein (und war der >=20), NICHT ueberschreiben.
    prev = data.get(market)
    prev_n = len(prev.get("listings", [])) if isinstance(prev, dict) else 0
    if prev_n >= 20 and not force and len(listings) < prev_n * 0.5:
        print(f"[free] DRIFT-GUARD: {market} neuer Scrape {len(listings)} Inserate << letzter guter Stand {prev_n} "
              f"(>50% Einbruch — vermutl. Rate-Limit/Block). competitors.json NICHT ueberschrieben. (--force zum Erzwingen bei bewusster Parameter-Aenderung)")
        raise SystemExit(2)
    data[market] = entry
    with open(fa.OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    # In die Zeitreihe einspeisen -> --aggregate zieht ADR/RevPAR -> Perlen-Radar scort den Markt.
    try:
        fa.append_history(market, listings)
    except Exception as e:
        print(f"[free] WARN Zeitreihe: {e}")
    try:
        fa.append_scrape_run(run_meta, sig)
    except Exception as e:
        print(f"[free] WARN Run-Log: {e}")
    prices = [l["normalized_nightly_price"] for l in agg if l.get("normalized_nightly_price")]
    cal_txt = (f", Kalender-Obergrenze(managed) {avg_cal_managed}% aus {len(cal_managed)} aktiven"
               if avg_cal_managed is not None else "")
    print(f"[free] {market}: {len(listings)} roh / {len(agg)} in-radius ({len(ent)} ganze), {len(prices)} mit Preis, "
          f"Geo in-radius {in_share}%, Entire-Auslastung(Review) {entry['avg_occupancy_entire_pct']}%{cal_txt} -> {fa.OUT_FILE}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("location", help="z.B. 'Zug, Switzerland'")
    ap.add_argument("--market", required=True, help="Markt-Key (z.B. Zug)")
    ap.add_argument("--sweep", action="store_true",
                    help="Quadtree-Bounding-Box-Sweep statt Einzel-Query (viel mehr Inserate, braucht Marktzentrum)")
    ap.add_argument("--max-depth", type=int, default=3,
                    help="Sweep-Rekursionstiefe (3 = bis zu 64 Kacheln; höher für Grossstädte)")
    ap.add_argument("--no-calendar", action="store_true",
                    help="Kalender-Abruf je Inserat ueberspringen (schneller; nur Review-Proxy)")
    ap.add_argument("--force", action="store_true",
                    help="Drift-Guard umgehen (bei bewusster Parameter-Aenderung, z.B. Radius-Recalibration)")
    a = ap.parse_args()
    run(a.location, a.market, sweep=a.sweep, max_depth=a.max_depth, no_calendar=a.no_calendar, force=a.force)
