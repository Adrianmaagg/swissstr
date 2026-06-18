#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""operator_xray.py — durchleuchtet die GROSSEN Spieler: holt vom oeffentlichen Host-Profil
(airbnb.com/users/show/<uid>) die ECHTE Gesamt-Inseratzahl Airbnb-weit. Adrian-Befund: Stephanie
zeigt im Netzwerk '1 Inserat', hat aber real 241 — wir sehen nur den Schnitt mit unseren gescrapten
Maerkten. Die Profilseite nennt die wahre Zahl ('241 listings') gratis im statischen HTML.

Quelle/Tier: 🟢 vom Host-Profil gelesen (Gesamtzahl + erste Inserat-IDs). Die VOLLE Liste aller 241
mit Ort braucht GraphQL-Pagination (Weg B) — hier zuerst die belastbare Gesamtzahl.

Aufruf:  py tools/operator_xray.py [--top 60] [--min-reviews 150] [--force]
Schreibt data/operator-xray.json (resumable: schon geholte uids werden uebersprungen).
"""
import sys, os, re, json, gzip, time, argparse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb_free as ff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PACE_S = 1.2


def fetch_profile(uid):
    req = urllib.request.Request(
        f"https://www.airbnb.com/users/show/{uid}",
        headers={"User-Agent": ff.UA, "Accept-Language": "en", "Accept": "text/html", "Accept-Encoding": "gzip"})
    try:
        r = urllib.request.urlopen(req, timeout=30); raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        html = raw.decode("utf-8", "replace")
    except Exception:
        return None
    # Echte Gesamtzahl: der Listings-Abschnitt nennt sie als Text 'N listings' (en-Locale).
    nums = []
    for m in re.findall(r"(\d[\d,]*)\s+listings?\b", html):
        digits = re.sub(r"\D", "", m)
        if digits:
            nums.append(int(digits))
    # erste sichtbare Inserat-IDs (erste Profil-Seite; der Rest laedt per GraphQL nach)
    room_ids = sorted(set(re.findall(r"/rooms/(\d{6,})", html)), key=lambda x: (len(x), x))
    # Gesamtzahl: 'N listings'-Text (gross/genau) ODER Fallback = sichtbare Inserat-Links
    # (kleine Profile zeigen keinen Text, aber alle Inserate als Links -> Lina 5 statt None).
    total = max(nums) if nums else (len(room_ids) if room_ids else None)
    # Profil-Name (Plausibilitaets-Check)
    nm = re.search(r'"smartName":"([^"]+)"', html) or re.search(r"<title>([^<]+)</title>", html)
    name = nm.group(1).strip() if nm else None
    return {"total_listings": total, "first_room_ids": room_ids[:20], "profile_name": name}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=60, help="wie viele Top-Operatoren (nach Operator-Bewertungen)")
    ap.add_argument("--min-reviews", type=int, default=150)
    ap.add_argument("--force", action="store_true", help="auch schon geholte neu ziehen")
    ap.add_argument("--only", help="nur diese uid (Test)")
    a = ap.parse_args()

    net = json.load(open(os.path.join(DATA, "operator-network.json"), encoding="utf-8"))
    ops = net["operators"]
    xpath = os.path.join(DATA, "operator-xray.json")
    cache = {}
    if os.path.exists(xpath) and not a.force:
        try: cache = json.load(open(xpath, encoding="utf-8")).get("operators", {})
        except Exception: cache = {}

    if a.only:
        targets = [a.only]
    else:
        # Alle Mehrfach-Betreiber (>=2 Inserate) ODER >=min_reviews — damit auch Kleinere ihr echtes
        # Gesamt-Portfolio zeigen (kein 'zeigt 2 statt echte 5' mehr).
        cand = [(uid, o) for uid, o in ops.items()
                if o.get("own_count", 0) >= 2 or (o.get("host_total_reviews") or 0) >= a.min_reviews]
        cand.sort(key=lambda kv: -((kv[1].get("host_total_reviews") or 0) + 1000 * (kv[1].get("own_count") or 0)))
        targets = [uid for uid, _ in cand[:a.top]]

    todo = [u for u in targets if a.force or u not in cache or (cache.get(u) or {}).get("total_listings") is None]
    print(f"X-Ray: {len(targets)} Top-Operatoren, {len(todo)} zu holen (~{PACE_S}s/Stk) ...")
    done = 0
    for uid in todo:
        d = fetch_profile(uid); time.sleep(PACE_S)
        if not d:
            continue
        o = ops.get(uid, {})
        cache[uid] = {
            "uid": uid, "name": o.get("name"),
            "total_listings": d["total_listings"],
            "own_count_in_markets": o.get("own_count"),
            "host_total_reviews": o.get("host_total_reviews"),
            "first_room_ids": d["first_room_ids"],
        }
        done += 1
        if d["total_listings"]:
            print(f"  {o.get('name')}: {d['total_listings']} Inserate gesamt "
                  f"(wir sehen {o.get('own_count')}, {o.get('host_total_reviews')} Bew.)")
    json.dump({"_meta": {"operators": len(cache), "note": "Gesamt-Inseratzahl Airbnb-weit vom Host-Profil (🟢)."},
               "operators": cache},
              open(xpath, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    print(f"-> {xpath}  ({len(cache)} Operatoren im X-Ray, +{done} neu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
