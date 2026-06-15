#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ensure_center.py <Market> [Canton] — sorgt dafuer, dass ein Markt ein Center in
data/market-centers.json hat (noetig, damit fetch_airbnb_free die Geo-Klassifizierung
nicht als UNUSABLE flaggt — siehe Zermatt-Befund). Leitet Center+Radius aus der schon
geholten Gemeindegrenze (boundary-<m>.geojson) ab: Centroid = Mittel aller Polygon-Punkte,
radius_km = halbe Bbox-Diagonale (gedeckelt). Idempotent: vorhandene Center bleiben.
"""
import sys, os, json, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def _coords(geom):
    t = geom.get("type")
    out = []
    if t == "Polygon":
        for ring in geom.get("coordinates", []):
            out += ring
    elif t == "MultiPolygon":
        for poly in geom.get("coordinates", []):
            for ring in poly:
                out += ring
    return out  # [lon, lat] pairs


def main():
    if len(sys.argv) < 2:
        sys.exit("Aufruf: ensure_center.py <Market> [Canton]")
    market = sys.argv[1]
    canton = sys.argv[2] if len(sys.argv) > 2 else ""
    bpath = os.path.join(DATA, f"boundary-{market.lower()}.geojson")
    cpath = os.path.join(DATA, "market-centers.json")
    centers = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    cur = centers.get(market)
    if isinstance(cur, dict) and cur.get("lat") is not None:
        print(f"{market}: Center vorhanden ({cur['lat']},{cur['lng']}) — ok")
        return 0
    if not os.path.exists(bpath):
        print(f"{market}: keine Grenze ({bpath}) — Center kann nicht abgeleitet werden")
        return 2
    g = json.load(open(bpath, encoding="utf-8")).get("geometry", {})
    pts = _coords(g)
    if not pts:
        print(f"{market}: Grenze ohne Punkte — uebersprungen")
        return 2
    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]
    lat = round(sum(lats) / len(lats), 5); lng = round(sum(lons) / len(lons), 5)
    # Radius aus halber Bbox-Diagonale (km), gedeckelt 3..12
    dlat = (max(lats) - min(lats)) * 111.32
    dlng = (max(lons) - min(lons)) * 111.32 * max(0.01, math.cos(math.radians(lat)))
    radius = max(3, min(12, round(math.hypot(dlat, dlng) / 2)))
    centers[market] = {"lat": lat, "lng": lng, "canton": canton, "radius_km": radius}
    json.dump(centers, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{market}: Center abgeleitet -> {lat},{lng} (r={radius}km)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
