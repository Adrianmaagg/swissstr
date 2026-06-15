#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Einmal-Reparatur: Discovery-Inserate hatten ihren 3-Nächte-Aufenthalts-Total faelschlich
durch STAY_NIGHTS=7 statt DISCOVERY_STAY=3 geteilt -> Preis ~2.3x zu tief (Bug bis v0.9.143).
Korrigiert price_usd/normalized_nightly_price in airbnb-competitors.json fuer alle Inserate mit
discovered_window_offset!=None & price_mode==stay_total & price_raw, und patcht price_chf in den
cockpit-*.json per Inserat-ID. Reine Re-Normalisierung aus vorhandenen Rohwerten, kein Netz.
"""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DISCOVERY_STAY = 3
USD_CHF = 0.80


def main():
    comp_path = os.path.join(DATA, "airbnb-competitors.json")
    comp = json.load(open(comp_path, encoding="utf-8"))
    # id -> korrigierter price_chf, je Markt (capitalisierter Schluessel wie in competitors)
    corrected = {}   # market_name -> {id: price_chf}
    n_fixed = 0
    for mk, blob in comp.items():
        if not isinstance(blob, dict) or "listings" not in blob:
            continue
        corrected[mk] = {}
        for l in blob["listings"]:
            off = l.get("discovered_window_offset")
            raw = l.get("price_raw")
            if off is not None and l.get("price_mode") == "stay_total" and raw:
                new_usd = round(raw / DISCOVERY_STAY, 2)
                if l.get("price_usd") != new_usd:
                    l["price_usd"] = new_usd
                    l["normalized_nightly_price"] = new_usd
                    l["priced_stay_nights"] = DISCOVERY_STAY
                    n_fixed += 1
            if l.get("price_usd"):
                corrected[mk][str(l["id"])] = round(l["price_usd"] * USD_CHF)
    json.dump(comp, open(comp_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"airbnb-competitors.json: {n_fixed} Discovery-Preise re-normalisiert (÷{DISCOVERY_STAY} statt ÷7).")

    # cockpit-*.json patchen (per _meta.market -> competitors-Schluessel, dann id-Lookup)
    n_cock = 0
    for f in glob.glob(os.path.join(DATA, "cockpit-*.json")):
        base = os.path.basename(f)[len("cockpit-"):-len(".json")]
        if base.endswith("-pickup") or base in ("season-proxy", "markets"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        mname = (d.get("_meta") or {}).get("market")
        cmap = corrected.get(mname) or {}
        if not cmap:
            continue
        ch = 0
        for l in d.get("listings", []):
            new = cmap.get(str(l.get("id")))
            if new is not None and l.get("price_chf") != new:
                l["price_chf"] = new
                ch += 1
        if ch:
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"  {os.path.basename(f)}: {ch} Preise gepatcht ({mname}).")
            n_cock += ch
    print(f"Cockpit-Dateien: {n_cock} Preise gepatcht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
