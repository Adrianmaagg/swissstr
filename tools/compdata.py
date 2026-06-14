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


def load_boundary(market):
    p = os.path.join(fa.DATA_DIR, f"boundary-{market.lower()}.geojson")
    if not os.path.isfile(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def _rings(geom):
    """Aeussere Ringe als Liste von [(lon,lat),...] (Polygon + MultiPolygon)."""
    if not geom: return []
    if geom["type"] == "Polygon": return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon": return [poly[0] for poly in geom["coordinates"]]
    return []


def point_in(lon, lat, rings):
    """Ray-Casting: liegt (lon,lat) in irgendeinem Ring?"""
    if lon is None or lat is None: return None
    for ring in rings:
        inside = False; n = len(ring); j = n - 1
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
            if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi):
                inside = not inside
            j = i
        if inside: return True
    return False


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
    boundary = load_boundary(a.market)
    rings = _rings(boundary["geometry"]) if boundary else []
    seen, recs, snaps = set(), [], []
    src = [l for l in comp[a.market]["listings"]
           if l.get("in_market_radius") and l.get("pdp_is_entire") is not None]
    print(f"{a.market}: {len(src)} PDP-angereicherte Inserate{' · Gemeindegrenze geladen' if rings else ' · KEINE Grenze (Radius-Fallback)'}. Lade Kalender ...")
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
            "in_municipality": (point_in(l.get("long"), l.get("lat"), rings) if rings else None),
            "cal_managed": l.get("cal_managed"),                       # Block-Heuristik: aktiv vermietet vs host-blockiert/privat
            "cal_occ_raw_pct": l.get("cal_occ_raw_pct"),               # Roh-Obergrenze (inkl. Blocks)
            "cal_longest_block_days": l.get("cal_longest_block_days"),
            "occ": occ_by_horizon(cal),
        })
        # RETENTION: Roh-Kalender (das Gold fuer Pickup-Kurve/r) pro Tag aufheben, statt ihn wie bisher zu verwerfen.
        booked = sorted(d for d, av in cal.items() if not av)
        win = sorted(cal.keys())
        snaps.append({"id": l["id"], "price_chf": recs[-1]["price_chf"], "n_days": len(cal),
                      "window": [win[0], win[-1]] if win else [None, None], "booked": booked})
    # Portfolio: wie viele Inserate IM MARKT teilen sich dieselbe host_id (Mehrfach-Betreiber-Signal).
    # Gesamt-Portfolio (auch ausserhalb) braeuchte die Host-Profilseite — hier nur in-market.
    from collections import Counter
    hc = Counter(r["host_id"] for r in recs if r["host_id"])
    for r in recs:
        r["portfolio_in_market"] = hc.get(r["host_id"], 1) if r["host_id"] else None
    # SELBSTHEILUNG: ein misslungener Scrape (0 Inserate) darf den letzten guten Stand NIE ueberschreiben.
    if not recs:
        sys.exit(f"{a.market}: 0 verwertbare Inserate — Serving-JSON + Snapshot NICHT ueberschrieben (letzter guter Stand bleibt erhalten).")
    ctr = fa.market_center(a.market) or {}
    out = {
        "_meta": {
            "market": a.market,
            "fetched": datetime.date.today().isoformat(),
            "horizons": HORIZONS,
            "center": {"lat": ctr.get("lat"), "lon": ctr.get("lng")},
            "boundary": boundary["geometry"] if boundary else None,
            "n": len(recs),
            "n_in_municipality": sum(1 for r in recs if r["in_municipality"]),
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
    # --- RETENTION: datierter Snapshot mit Roh-Kalendern (append-only Historie; gross+privat -> gitignored) ---
    snapdir = os.path.join(fa.DATA_DIR, "snapshots", a.market.lower())
    os.makedirs(snapdir, exist_ok=True)
    sp = os.path.join(snapdir, datetime.date.today().isoformat() + ".json")
    snap_out = {"market": a.market, "date": datetime.date.today().isoformat(),
                "center": out["_meta"]["center"], "n": len(snaps), "listings": snaps}
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(snap_out, fh, ensure_ascii=False)
    booked_days = sum(len(s["booked"]) for s in snaps)
    print(f"  Snapshot -> {sp}  ({len(snaps)} Inserate, {booked_days} belegte Kalendertage aufgehoben)")


if __name__ == "__main__":
    main()
