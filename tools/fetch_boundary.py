#!/usr/bin/env python3
"""Holt die echte Gemeindegrenze (Polygon) eines Marktes via OSM Nominatim und speichert sie
nach data/boundary-<market>.geojson. Damit klassifiziert das Cockpit Inserate per Punkt-in-Polygon
(drin = wirklich im Ort) statt per grobem Radius-Kreis.

Aufruf:  py -3.12 tools/fetch_boundary.py Kriens "Kriens, Luzern, Switzerland"
"""
import sys, os, json, time, urllib.parse, urllib.request, gzip
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa

def main():
    if len(sys.argv) < 2:
        sys.exit("Aufruf: fetch_boundary.py <market> [query]")
    market = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else f"{market}, Switzerland"
    q = urllib.parse.urlencode({"q": query, "format": "json", "polygon_geojson": "1",
                                "limit": "3", "countrycodes": "ch"})
    req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + q,
        headers={"User-Agent": "SwissSTR/1.0 (R2R market research)", "Accept-Encoding": "gzip"})
    r = urllib.request.urlopen(req, timeout=30); raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
    res = json.loads(raw.decode("utf-8", "replace"))
    # bevorzugt das administrative boundary-Ergebnis (Gemeinde)
    pick = next((it for it in res if it.get("class") == "boundary"
                 and it.get("geojson", {}).get("type") in ("Polygon", "MultiPolygon")), None)
    if not pick:
        pick = next((it for it in res if it.get("geojson", {}).get("type") in ("Polygon", "MultiPolygon")), None)
    if not pick:
        sys.exit("Keine Polygon-Grenze gefunden.")
    out = {"market": market, "display_name": pick.get("display_name"),
           "osm_type": f"{pick.get('class')}/{pick.get('type')}",
           "geometry": pick["geojson"]}
    p = os.path.join(fa.DATA_DIR, f"boundary-{market.lower()}.geojson")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False)
    g = pick["geojson"]
    n = len(g.get("coordinates", [[]])[0]) if g["type"] == "Polygon" else sum(len(poly[0]) for poly in g.get("coordinates", []))
    print(f"{market}: Grenze gespeichert -> {p}  ({g['type']}, ~{n} Punkte, {pick.get('display_name','')[:50]})")

if __name__ == "__main__":
    main()
