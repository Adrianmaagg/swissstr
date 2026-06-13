#!/usr/bin/env python3
"""Profi-Radar Stufe 1: reichert Inserate eines Marktes ueber die oeffentliche Inserat-Seite
(PDP, data-deferred-state-0, gleicher Weg wie Kalender) an mit den ECHTEN Feldern, die die
Suchseite nicht hat: Objekttyp (Apartment vs Zimmer!), Superhost, Guest-favorite, Kapazitaet,
PDP-Rating/Reviews. Schreibt zurueck in airbnb-competitors.json (Felder pdp_*).

Adrians Befund: Suchseiten-Entire-Erkennung ist unzuverlaessig (Privatzimmer rutschten durch).
roomType von der PDP ist autoritativ -> nur echte ganze Wohnungen behalten.

Aufruf:  py -3.12 tools/pdp_enrich.py Kriens [--max 60]
"""
import sys, os, re, json, gzip, time, urllib.request, argparse
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa
import fetch_airbnb_free as ff

PACE_S = 0.8


def first_key(o, key):
    """Erster Wert zu 'key' (case-insensitive) im verschachtelten Objekt, der kein dict/list ist."""
    kl = key.lower()
    stack = [o]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k.lower() == kl and not isinstance(v, (dict, list)) and v is not None:
                    return v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def fetch_pdp(rid):
    req = urllib.request.Request(f"https://www.airbnb.com/rooms/{rid}", headers={
        "User-Agent": ff.UA, "Accept-Language": "en", "Accept": "text/html", "Accept-Encoding": "gzip"})
    try:
        r = urllib.request.urlopen(req, timeout=30); raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        html = raw.decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r'<script id="data-deferred-state-0"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        state = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    rt = first_key(state, "roomType")
    # VERIFIZIERT zuverlaessig (gegen Probe + Adrians Augenschein):
    #   roomType / personCapacity / reviewCount / starRating — erstes Vorkommen = das Inserat selbst.
    # NICHT zuverlaessig per first_key: isSuperhost / isGuestFavorite — die Seite hat mehrere Vorkommen
    #   (Promo, Nachbar-Inserate), erstes ist NICHT das Inserat (361er-Zimmer kam faelschlich superhost=True).
    #   -> Superhost/Favorit kommen aus den Such-Karten-Badges (formattedBadges), separater Fix. TODO.
    return {
        "pdp_room_type": rt,                                   # 'Entire home/apt' | 'Private room' | ...
        "pdp_is_entire": (rt is not None and "entire" in str(rt).lower()),
        "pdp_person_capacity": first_key(state, "personCapacity"),
        "pdp_reviews": first_key(state, "reviewCount"),
        "pdp_rating": first_key(state, "starRating"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market")
    ap.add_argument("--max", type=int, default=80)
    a = ap.parse_args()

    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    if a.market not in comp:
        sys.exit(f"{a.market}: keine Scrape-Daten.")
    L = [l for l in comp[a.market]["listings"] if l.get("in_market_radius")][:a.max]
    print(f"{a.market}: PDP-Anreicherung fuer {len(L)} in-radius-Inserate (~{PACE_S}s/Stk) ...")
    ok, entire, rooms = 0, 0, 0
    seen = {}
    for l in L:
        rid = l["id"]
        if rid in seen:                 # Duplikate (Sweep+Liste) nur einmal abrufen
            l.update(seen[rid]); continue
        d = fetch_pdp(rid); time.sleep(PACE_S)
        if not d:
            continue
        seen[rid] = d
        l.update(d)
        ok += 1
        if d["pdp_is_entire"]: entire += 1
        elif d["pdp_room_type"]: rooms += 1
    json.dump(comp, open(fa.OUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  {ok} angereichert · {entire} ECHTE Wohnungen · {rooms} Zimmer (raus, Privatzimmer/Hotelzimmer)")


if __name__ == "__main__":
    main()
