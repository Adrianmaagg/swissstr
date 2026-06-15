#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_market_manifest.py — erzeugt data/cockpit-markets.json: die Liste ALLER
Maerkte, die ein frisches cockpit-<key>.json haben. start.html (Karte) und
cockpit.html (Dropdown) lesen dieses Manifest -> neu gescrapte Maerkte erscheinen
automatisch, ohne Hardcode. Pro Markt: key (Dateiname-Slug), name (_meta.market),
canton (aus market-centers.json), lat/lon (_meta.center).
"""
import json, os, glob, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def main():
    centers = {}
    cp = os.path.join(DATA, "market-centers.json")
    if os.path.exists(cp):
        centers = json.load(open(cp, encoding="utf-8"))
    out = []
    for f in glob.glob(os.path.join(DATA, "cockpit-*.json")):
        base = os.path.basename(f)[len("cockpit-"):-len(".json")]
        # "markets" = unsere eigene Ausgabedatei (cockpit-markets.json), kein Markt
        if base.endswith("-pickup") or base in ("season-proxy", "markets"):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        meta = d.get("_meta") or {}
        name = meta.get("market") or base.title()
        ctr = meta.get("center") or {}
        L = d.get("listings") or []
        # in-Gemeinde-Zahl als kleiner Frische-/Substanz-Hinweis
        n_in = sum(1 for l in L if l.get("in_municipality") is True) or len(L)
        cinfo = centers.get(name) or {}
        out.append({
            "key": base,
            "name": name,
            "canton": cinfo.get("canton") or "",
            "lat": ctr.get("lat"),
            "lon": ctr.get("lon"),
            "n": n_in,
            "fetched": meta.get("fetched"),
        })
    out.sort(key=lambda m: m["name"])
    p = os.path.join(DATA, "cockpit-markets.json")
    json.dump({"_meta": {"count": len(out)}, "markets": out},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Manifest: {len(out)} Maerkte -> {p}")
    print("  " + ", ".join(m["name"] for m in out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
