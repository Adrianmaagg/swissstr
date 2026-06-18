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
import json, os, math

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


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

    # Anker = gescrapte Maerkte MIT BFS UND Koordinaten (nur die kennen wir geografisch)
    anchors = [m for m in manifest
               if m.get("lat") and m.get("lon") and has_bfs(m.get("name", ""))]
    if not anchors:
        print("WARN: keine BFS-Anker mit Koordinaten gefunden — Proxy bleibt leer.")

    proxy = {
        "_note": "AUTO-GEBAUT von tools/build_season_proxy.py — Gemeinden ohne eigene "
                 "BFS-Hoteldaten -> naechster gescrapter Markt MIT BFS (Luftlinie, gleiche "
                 "Region). Nur die Saison-FORM wird geliehen, das Niveau bleibt vom Markt selbst."
    }
    mapped = []
    for m in manifest:
        name = str(m.get("name", "")).strip()
        if not name or has_bfs(name):
            continue  # hat eigene BFS-Saison
        if not (m.get("lat") and m.get("lon")) or not anchors:
            continue
        best = min(anchors, key=lambda a: _hav(m["lat"], m["lon"], a["lat"], a["lon"]))
        dist = _hav(m["lat"], m["lon"], best["lat"], best["lon"])
        proxy[name.lower()] = bfs[str(best["name"]).strip().lower()]
        mapped.append((name, best["name"], round(dist, 1)))

    out = os.path.join(DATA, "cockpit-season-proxy.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(proxy, f, ensure_ascii=False, indent=2)

    print(f"Saison-Proxy: {len(mapped)} Gemeinden ohne BFS -> naechster BFS-Nachbar "
          f"({len(anchors)} Anker). -> {os.path.relpath(out)}")
    for nm, prx, d in sorted(mapped, key=lambda x: x[0]):
        print(f"  {nm:22s} -> {prx:16s} ({d} km)")


if __name__ == "__main__":
    main()
