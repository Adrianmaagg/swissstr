#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""discover_competitors.py — findet die GROSSEN STR-Verwalter, die in der ganzen Schweiz agieren,
auch die ausserhalb unserer gescrapten Maerkte. Quelle: das Airbtics-Branchenverzeichnis
(top-airbnb-management-companies-in-<region>-switzerland) — dort steht je Firma die Airbnb-Host-ID
im Link. Die dort gezeigte Inseratzahl ist meist ein Platzhalter ('23'), darum holen wir die
ECHTE Gesamt-Inseratzahl selbst per X-Ray ueber die Host-ID (operator_xray.fetch_profile).

Stufen (Adrian): small big 10+, mittel big 50+, big big 200+, extrem big 400+.

Aufruf:  py tools/discover_competitors.py [--force]
Schreibt data/competitors-ch.json (resumable: bekannte uids werden nicht neu gezogen).
"""
import sys, os, re, json, gzip, time, argparse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb_free as ff
import operator_xray as ox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PACE_S = 1.2

CH = "https://airbtics.com/top-airbnb-management-companies-in-switzerland"
TMPL = "https://airbtics.com/top-airbnb-management-companies-in-{}-switzerland"
REGIONS = [
    "zurich", "geneva", "basel", "bern", "lausanne", "lucerne", "lugano", "locarno",
    "ticino", "valais", "vaud", "grisons", "graubunden", "zermatt", "verbier", "grindelwald",
    "interlaken", "davos", "st-moritz", "arosa", "flims", "laax", "montreux", "crans-montana",
    "saas-fee", "engelberg", "wengen", "gstaad", "ascona", "bagnes", "andermatt", "leukerbad",
    "scuol", "lenzerheide", "villars", "nendaz", "anzere", "champery", "morzine",
]


def tier_of(n):
    if n is None:
        return None, None
    if n >= 400: return "extrem", "extrem big · 400+"
    if n >= 200: return "big", "big big · 200+"
    if n >= 50:  return "mittel", "mittel big · 50+"
    if n >= 10:  return "small", "small big · 10+"
    return "unter", "unter 10"


def fetch_html(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": ff.UA, "Accept-Language": "en", "Accept": "text/html", "Accept-Encoding": "gzip"})
    try:
        r = urllib.request.urlopen(req, timeout=30); raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "replace")
    except Exception:
        return None


def prettify(slug):
    s = re.sub(r"\(tm\)", "", slug)
    s = s.replace("-", " ").replace("daffaires", "d'affaires").strip()
    return " ".join(w.capitalize() for w in s.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    # 1) Verzeichnis-Seiten abgrasen -> uid -> name. NUR echte CH-Seiten:
    #    ungueltige Slugs leiten auf eine globale US-Fallback-Seite (>2700 Firmen) um ->
    #    am Titel ('... in <X>, Switzerland') + Sicherheits-Deckel erkennen und verwerfen.
    found = {}
    pages = [CH] + [TMPL.format(r) for r in REGIONS]
    okp = 0
    for u in pages:
        html = fetch_html(u); time.sleep(0.4)
        if not html:
            continue
        tm = re.search(r"<title>([^<]+)", html)
        title = tm.group(1) if tm else ""
        if "switzerland" not in title.lower():          # US-Fallback / Fremd-Region -> raus
            continue
        hits = re.findall(r"/airbnb-management-companies/([a-z0-9\-\(\)']+?)-(\d{4,})", html)
        uids = {uid: prettify(slug) for slug, uid in hits}
        if len(uids) > 250:                              # versteckte Mega-Liste -> raus
            continue
        okp += 1
        for uid, nm in uids.items():
            found.setdefault(uid, nm)
    print(f"Verzeichnis: {okp} CH-Seiten ok -> {len(found)} eindeutige Firmen (Host-IDs)")

    # 2) Cache laden (resumable)
    p = os.path.join(DATA, "competitors-ch.json")
    cache = {}
    if os.path.exists(p) and not a.force:
        try: cache = json.load(open(p, encoding="utf-8")).get("competitors", {})
        except Exception: cache = {}

    def flush():
        # Ausgabe NUR aus den CH-Verzeichnis-uids (found) — alter Cache-Muell faellt raus.
        out = {uid: cache[uid] for uid in found if uid in cache}
        counts = {"extrem": 0, "big": 0, "mittel": 0, "small": 0, "unter": 0}
        for v in out.values():
            if v.get("tier"): counts[v["tier"]] = counts.get(v["tier"], 0) + 1
        json.dump({"_meta": {"competitors": len(out), "tiers": counts,
                             "note": "STR-Verwalter aus Airbtics-CH-Verzeichnis (CH-Seiten, nicht global). Echte Inseratzahl per Host-Profil-X-Ray. Stufen: small 10+/mittel 50+/big 200+/extrem 400+."},
                   "competitors": out},
                  open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
        return out, counts

    todo = [uid for uid in found if a.force or uid not in cache]
    print(f"X-Ray: {len(todo)} neue Firmen zu durchleuchten (~{PACE_S}s/Stk) ...")
    done = 0
    for uid in todo:
        d = ox.fetch_profile(uid); time.sleep(PACE_S)
        if not d:
            continue
        total = d.get("total_listings")
        t, tl = tier_of(total)
        cache[uid] = {
            "uid": uid, "name": d.get("profile_name") or found.get(uid),
            "dir_name": found.get(uid),
            "total_listings": total, "tier": t, "tier_label": tl,
            "source": "airbtics",
        }
        done += 1
        if total:
            print(f"  {(cache[uid]['name'] or '?')[:34]:34} {total:>5} Inserate  [{t}]")
        if done % 20 == 0:
            flush()      # inkrementell sichern -> ein Stopp verliert nichts mehr

    out, counts = flush()
    print(f"-> {p}  ({len(out)} Firmen) Stufen: "
          f"extrem {counts['extrem']} · big {counts['big']} · mittel {counts['mittel']} · small {counts['small']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
