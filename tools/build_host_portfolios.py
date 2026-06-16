#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_host_portfolios.py — erzeugt data/host-portfolios.json: pro host_id die GESAMTE
Inserat-Zahl ueber ALLE gescrapten Maerkte (in-Gemeinde). Adrian-Befund: ein Host hat in
Kriens nur 1 Wohnung, ueber die Maerkte aber mehrere -> per-Markt unterzaehlt. Das Cockpit
liest diesen Index und zeigt in der PORTF.-Spalte die ECHTE Portfolio-Groesse + Maerkte.
"""
import json, os, glob
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def main():
    hosts = {}
    for f in glob.glob(os.path.join(DATA, "cockpit-*.json")):
        base = os.path.basename(f)
        if base.endswith("-pickup.json") or "markets" in base or "season" in base:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        mkt = (d.get("_meta") or {}).get("market") or base
        for l in d.get("listings", []):
            if l.get("in_municipality") is not True:
                continue
            hid = l.get("host_id")
            if not hid:
                continue
            h = hosts.setdefault(hid, {"name": None, "total": 0, "markets": defaultdict(int), "listing_ids": []})
            h["name"] = l.get("host") or h["name"]
            h["total"] += 1
            h["markets"][mkt] += 1
            if l.get("id"):
                h["listing_ids"].append(str(l["id"]))
    out = {}
    for hid, h in hosts.items():
        out[hid] = {
            "name": h["name"],
            "total": h["total"],
            "markets": dict(h["markets"]),          # {Markt: Anzahl}
            "n_markets": len(h["markets"]),
            "listing_ids": h["listing_ids"],
        }
    p = os.path.join(DATA, "host-portfolios.json")
    json.dump({"_meta": {"hosts": len(out)}, "hosts": out},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    multi = sum(1 for v in out.values() if v["total"] >= 2)
    cross = sum(1 for v in out.values() if v["n_markets"] >= 2)
    print(f"Host-Portfolios: {len(out)} Hosts -> {p}  (>=2 Inserate: {multi}, cross-Markt: {cross})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
