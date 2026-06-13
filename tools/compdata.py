#!/usr/bin/env python3
"""Exportiert den Wettbewerbs-Datensatz EINES Marktes fuer das interaktive Cockpit (cockpit.html).
Pro Inserat: Typ (Wohnung/Zimmer), Kapazitaet, Zimmer, Superhost, Favorit, Reviews, Rating,
Preis (~CHF), Host, URL — und Auslastung je Horizont (3/7/14/30/45/60/90/120 T).

Nur PDP-angereicherte in-radius-Inserate (Objekttyp bekannt). Schreibt data/cockpit-<market>.json.
Aufruf:  py -3.12 tools/compdata.py Kriens
"""
import sys, os, json, datetime, argparse
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa
import fetch_airbnb_free as ff

HORIZONS = [3, 7, 14, 30, 45, 60, 90, 120]
USD_CHF = 0.80


def occ_by_horizon(cal):
    """cal = {date: available}. Auslastung (% belegt) je Horizont ab heute."""
    today = datetime.date.today()
    out = {}
    for K in HORIZONS:
        un = tot = 0
        for i in range(K):
            d = (today + datetime.timedelta(days=i)).isoformat()
            if d in cal:
                tot += 1
                if not cal[d]:
                    un += 1
        out[str(K)] = round(un / tot * 100) if tot else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market")
    a = ap.parse_args()
    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    if a.market not in comp:
        sys.exit(f"{a.market}: keine Scrape-Daten.")
    seen, recs = set(), []
    src = [l for l in comp[a.market]["listings"]
           if l.get("in_market_radius") and l.get("pdp_is_entire") is not None]
    print(f"{a.market}: {len(src)} PDP-angereicherte Inserate. Lade Kalender ...")
    for l in src:
        if l["id"] in seen:
            continue
        seen.add(l["id"])
        days = ff.fetch_calendar(l["id"]); ff.time.sleep(0.55)
        cal = {d: av for d, av in days} if days else {}
        recs.append({
            "id": l["id"], "url": l.get("url"),
            "entire": bool(l.get("pdp_is_entire")),
            "room_type": l.get("pdp_room_type"),
            "capacity": l.get("pdp_person_capacity"),
            "bedrooms": l.get("bedrooms"),
            "superhost": l.get("pdp_is_superhost"),
            "guest_favorite": l.get("pdp_guest_favorite"),
            "reviews": l.get("reviews_count"),
            "rating": l.get("pdp_rating") or l.get("rating"),
            "price_chf": round(l["price_usd"] * USD_CHF) if l.get("price_usd") else None,
            "host": l.get("pdp_host_name"),
            "host_id": l.get("pdp_host_id"),
            "years_hosting": l.get("pdp_years_hosting"),
            "lat": l.get("lat"), "lon": l.get("long"),
            "dist_km": (round(l["distance_to_market_center_km"], 1)
                        if l.get("distance_to_market_center_km") is not None else None),
            "occ": occ_by_horizon(cal),
        })
    # Portfolio: wie viele Inserate IM MARKT teilen sich dieselbe host_id (Mehrfach-Betreiber-Signal).
    # Gesamt-Portfolio (auch ausserhalb) braeuchte die Host-Profilseite — hier nur in-market.
    from collections import Counter
    hc = Counter(r["host_id"] for r in recs if r["host_id"])
    for r in recs:
        r["portfolio_in_market"] = hc.get(r["host_id"], 1) if r["host_id"] else None
    ctr = fa.market_center(a.market) or {}
    out = {
        "_meta": {
            "market": a.market,
            "fetched": datetime.date.today().isoformat(),
            "horizons": HORIZONS,
            "center": {"lat": ctr.get("lat"), "lon": ctr.get("lng")},
            "n": len(recs),
            "note": "Auslastung = % belegt/gesperrt je Horizont ab fetched-Datum. Preis ~CHF (USD x0.8, Such-Fenster). occ-Quelle: oeffentl. Kalender.",
        },
        "listings": recs,
    }
    p = os.path.join(fa.DATA_DIR, f"cockpit-{a.market.lower()}.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    sh = sum(1 for r in recs if r["superhost"])
    ent = sum(1 for r in recs if r["entire"])
    print(f"  {len(recs)} Inserate -> {p}  ({ent} Wohnungen, {len(recs)-ent} Zimmer, {sh} Superhosts)")


if __name__ == "__main__":
    main()
