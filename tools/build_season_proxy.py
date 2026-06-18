#!/usr/bin/env python3
"""
build_season_proxy.py — Saison-Form-Proxy fuer Gemeinden ohne eigene BFS-Hoteldaten.

Die Cockpit-Jahres-Prognose braucht eine Saison-FORM (BFS-Monatsdaten, je Kalendermonat
normiert). Kleine Gemeinden (Ennetbuergen, Buochs, Stansstad, Gersau, ...) haben keine
eigenen BFS-Hoteldaten -> ohne Proxy zeigt die Prognose nur "kein Saison-Profil".

Dieses Tool ordnet JEDER gescrapten Gemeinde OHNE eigene BFS-Daten den NAECHSTEN gescrapten
Markt MIT BFS-Daten zu (Luftlinie aus den Manifest-Koordinaten = gleiche Region = gleiche
Saison-Welle). Das gemessene NIVEAU bleibt vom Markt selbst; nur die VERTEILUNG uebers Jahr
wird geliehen (die UI markiert das ehrlich: "Saison-Form via Proxy <Nachbar>").

In:  data/cockpit-markets.json (Manifest: key/name/canton/lat/lon der gescrapten Maerkte)
     data/market-facts.json    (welche Namen ein bfs_monthly tragen = BFS-Anker)
Out: data/cockpit-season-proxy.json   { "<name_lower>": "<BFS-Nachbar-Name>", ... }
"""
import json, os, math, re

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
JS = os.path.join(os.path.dirname(__file__), "..", "js")

# Kantons-Vollname -> Code (Manifest fuehrt Vollnamen, market-facts fuehrt Codes)
CANTON2CODE = {
    "zürich": "ZH", "bern": "BE", "luzern": "LU", "uri": "UR", "schwyz": "SZ",
    "obwalden": "OW", "nidwalden": "NW", "glarus": "GL", "zug": "ZG", "freiburg": "FR",
    "solothurn": "SO", "basel-stadt": "BS", "basel-landschaft": "BL", "schaffhausen": "SH",
    "appenzell ausserrhoden": "AR", "appenzell innerrhoden": "AI", "st. gallen": "SG",
    "graubünden": "GR", "aargau": "AG", "thurgau": "TG", "tessin": "TI", "waadt": "VD",
    "wallis": "VS", "neuenburg": "NE", "genf": "GE", "jura": "JU",
}


def _canton_code(c):
    c = str(c or "").strip()
    if len(c) == 2:
        return c.upper()
    return CANTON2CODE.get(c.lower(), c.upper())


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _load_js_coords():
    """MARKET_COORDS aus js/coords.js parsen -> { name: (lat, lon) }."""
    path = os.path.join(JS, "coords.js")
    if not os.path.exists(path):
        return {}
    txt = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'"([^"]+)"\s*:\s*\{\s*lat:\s*([\d.]+),\s*lon:\s*([\d.]+)', txt):
        out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out


def _hav(la1, lo1, la2, lo2):
    r = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main():
    manifest = _load(os.path.join(DATA, "cockpit-markets.json")).get("markets", [])
    facts = _load(os.path.join(DATA, "market-facts.json"))

    # Namen (lowercase -> kanonisch) der Maerkte MIT eigener BFS-Saison
    bfs = {}
    for x in facts:
        if x.get("bfs_monthly"):
            nm = str(x.get("name", "")).strip()
            if nm:
                bfs[nm.lower()] = nm

    def has_bfs(name):
        return str(name).strip().lower() in bfs

    js_coords = _load_js_coords()
    man_by_name = {str(m.get("name", "")).strip().lower(): m for m in manifest}

    def coords_for(name, man_entry):
        # Manifest-Koordinaten (genauer, falls gescrapt) sonst js/coords.js (Gemeinde-Zentroid)
        if man_entry and man_entry.get("lat") and man_entry.get("lon"):
            return (man_entry["lat"], man_entry["lon"])
        return js_coords.get(str(name).strip())

    # Anker = ALLE BFS-Maerkte (market-facts) mit bekannten Koordinaten — auch NICHT-gescrapte
    # Hubs wie Luzern Stadt (robusteste, stabilste BFS-Saison der Region). Distanz + Kanton
    # entscheiden weiterhin, welcher Anker am vergleichbarsten ist.
    anchors = []
    for x in facts:
        if not x.get("bfs_monthly"):
            continue
        nm = str(x.get("name", "")).strip()
        c = coords_for(nm, man_by_name.get(nm.lower()))
        if not c:
            continue
        anchors.append({"name": nm, "canton": _canton_code(x.get("canton")), "lat": c[0], "lon": c[1]})
    if not anchors:
        print("WARN: keine BFS-Anker mit Koordinaten gefunden — Proxy bleibt leer.")

    proxy = {
        "_note": "AUTO-GEBAUT von tools/build_season_proxy.py — Gemeinden ohne eigene "
                 "BFS-Hoteldaten -> VERGLEICHBARSTER Markt MIT BFS-Saison. Anker = ALLE "
                 "BFS-Maerkte mit bekannten Koordinaten (auch nicht-gescrapte Hubs wie Luzern "
                 "Stadt). Auswahl = Luftlinie, aber gleicher KANTON zaehlt halb so weit "
                 "(Mikro-Region als Vergleichbarkeits-Proxy: ein Nidwalden-See-Dorf passt "
                 "besser als ein Luzerner Vorort, auch wenn der naeher liegt). Nur die "
                 "Saison-FORM wird geliehen, das Niveau bleibt vom Markt selbst."
    }

    def comp_score(t_canton, t_lat, t_lon, a):
        """Vergleichbarkeit: Luftlinie, gleicher Kanton zaehlt halb so weit."""
        d = _hav(t_lat, t_lon, a["lat"], a["lon"])
        return d * (0.5 if t_canton and t_canton == a["canton"] else 1.0)

    mapped = []
    for m in manifest:
        name = str(m.get("name", "")).strip()
        if not name or has_bfs(name):
            continue  # hat eigene BFS-Saison
        if not (m.get("lat") and m.get("lon")) or not anchors:
            continue
        t_canton = _canton_code(m.get("canton"))
        best = min(anchors, key=lambda a: comp_score(t_canton, m["lat"], m["lon"], a))
        dist = _hav(m["lat"], m["lon"], best["lat"], best["lon"])
        same = t_canton == best["canton"]
        proxy[name.lower()] = best["name"]
        mapped.append((name, best["name"], round(dist, 1), same))

    out = os.path.join(DATA, "cockpit-season-proxy.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(proxy, f, ensure_ascii=False, indent=2)

    print(f"Saison-Proxy: {len(mapped)} Gemeinden ohne BFS -> vergleichbarster BFS-Markt "
          f"({len(anchors)} Anker, gleicher Kanton bevorzugt). -> {os.path.relpath(out)}")
    for nm, prx, d, same in sorted(mapped, key=lambda x: x[0]):
        print(f"  {nm:22s} -> {prx:16s} ({d} km{', gleicher Kanton' if same else ''})")


if __name__ == "__main__":
    main()
