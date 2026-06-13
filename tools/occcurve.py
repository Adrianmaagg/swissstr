#!/usr/bin/env python3
"""Auslastungs-Kurve der AUSGESUCHTEN Inserate ueber mehrere Horizonte.
Fokus: nur PDP-verifizierte ganze Wohnungen (pdp_is_entire), in-radius, dedupliziert.
Fenster-Auslastung = Anteil nicht-verfuegbarer Tage in den naechsten K Tagen (was ein Gast sieht).

Naher Horizont hoch (kurzfristig gebucht), ferner tiefer (Vorlaufzeit). Ueber die Zeit
wiederholt laufen lassen -> man sieht, wie sich die Buchungen bei genau diesen Inseraten fuellen.

Aufruf:  py -3.12 tools/occcurve.py Kriens
         py -3.12 tools/occcurve.py Kriens --rooms   (Kategorie Zimmer statt Wohnungen)
"""
import sys, os, json, datetime, argparse
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa
import fetch_airbnb_free as ff

HORIZONS = [3, 7, 14, 30, 45, 60, 90, 120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market")
    ap.add_argument("--rooms", action="store_true", help="Kategorie Zimmer statt ganze Wohnungen")
    a = ap.parse_args()

    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    if a.market not in comp:
        sys.exit(f"{a.market}: keine Scrape-Daten.")
    want_entire = not a.rooms
    seen, sel = set(), []
    for l in comp[a.market]["listings"]:
        if not l.get("in_market_radius"):
            continue
        if l.get("pdp_is_entire") is None:  # nur PDP-angereicherte (Objekttyp bekannt)
            continue
        if bool(l.get("pdp_is_entire")) != want_entire:
            continue
        if l["id"] in seen:
            continue
        seen.add(l["id"]); sel.append(l)

    kind = "ganze Wohnungen" if want_entire else "Zimmer"
    today = datetime.date.today()
    print(f"{a.market} — {len(sel)} ausgesuchte {kind} (PDP-verifiziert). Stand {today.isoformat()}. Lade Kalender ...")

    cals = []
    for l in sel:
        days = ff.fetch_calendar(l["id"]); ff.time.sleep(0.55)
        if days:
            cals.append({d: av for d, av in days})

    print(f"  Kalender geladen: {len(cals)}/{len(sel)}\n")
    print(f"  {'Horizont':<12}{'Auslastung':>11}   (Anteil belegt/gesperrt)")
    for K in HORIZONS:
        win = [(today + datetime.timedelta(days=i)).isoformat() for i in range(K)]
        un = tot = 0
        for c in cals:
            for d in win:
                if d in c:
                    tot += 1
                    if not c[d]:
                        un += 1
        occ = round(un / tot * 100) if tot else 0
        bar = "#" * (occ // 4)
        print(f"  naechste {K:>3}T{occ:>8}%   {bar}")
    print("\n  Naher Horizont hoch = kurzfristig gebucht; faellt nach hinten = Vorlaufzeit (noch nicht gebucht).")


if __name__ == "__main__":
    main()
