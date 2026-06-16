#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""log_reviews.py — Weg A (robuste Review-Velocity OHNE Airbnb-Lazy-Load).
Schreibt pro Inserat die heutige Bewertungs-ANZAHL in data/review-history.json
(Zeitreihe je listing_id). Die Differenz ueber die Zeit = neue Bewertungen/Monat =
Adrians "min. 2 Bewertungen im letzten Monat" — von UNS gemessen, kein years_hosting,
kein Hash, kein Headless. Reift mit den Tagen (Monat ~30T, 4-Monats-Schnitt ~4 Mt).

Idempotent: ein Eintrag pro listing_id pro Datum (heutiger wird ersetzt).
Im Tageslauf + scrape_all + GitHub-Action nach compdata aufrufen.
"""
import json, os, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
HIST = os.path.join(DATA, "review-history.json")
MAX_POINTS = 220   # ~7 Monate taeglich; aeltere abschneiden


def velocity(points, months=4):
    """Bewertungen/Monat ueber das juengste <=months-Fenster. None wenn zu wenig Historie."""
    if len(points) < 2:
        return None
    pts = sorted(points, key=lambda p: p["date"])
    last = pts[-1]
    d_last = datetime.date.fromisoformat(last["date"])
    cutoff = d_last - datetime.timedelta(days=round(months * 30.4))
    # fruehester Punkt >= cutoff (sonst der aelteste, dann ueber die echte Spanne normieren)
    base = next((p for p in pts if datetime.date.fromisoformat(p["date"]) >= cutoff), pts[0])
    days = (d_last - datetime.date.fromisoformat(base["date"])).days
    if days < 7:
        return None   # zu kurze Spanne -> noch keine belastbare Velocity
    dn = last["reviews"] - base["reviews"]
    return round(dn / (days / 30.4), 2)   # neue Bewertungen pro Monat


def main():
    today = datetime.date.today().isoformat()
    hist = {}
    if os.path.exists(HIST):
        try:
            hist = json.load(open(HIST, encoding="utf-8")).get("listings", {})
        except Exception:
            hist = {}
    n = 0
    for f in glob.glob(os.path.join(DATA, "cockpit-*.json")):
        b = os.path.basename(f)
        if b.endswith("-pickup.json") or "markets" in b or "season" in b:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        mkt = (d.get("_meta") or {}).get("market") or b
        for l in d.get("listings", []):
            lid = str(l.get("id") or "")
            rev = l.get("reviews")
            if not lid or rev is None:
                continue
            e = hist.setdefault(lid, {"market": mkt, "host_id": l.get("host_id"), "points": []})
            e["market"] = mkt
            e["points"] = [p for p in e["points"] if p["date"] != today]   # heutigen ersetzen
            e["points"].append({"date": today, "reviews": rev})
            e["points"] = e["points"][-MAX_POINTS:]
            e["vpm_4mo"] = velocity(e["points"], 4)   # aktuelle Velocity (None bis genug Historie)
            n += 1
    ready = sum(1 for e in hist.values() if e.get("vpm_4mo") is not None)
    json.dump({"_meta": {"updated": today, "listings_tracked": len(hist), "with_velocity": ready}, "listings": hist},
              open(HIST, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Review-History: {n} Inserate heute geloggt, {len(hist)} verfolgt, {ready} mit echter Velocity (>=~1 Woche Spanne).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
