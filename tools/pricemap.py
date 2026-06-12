#!/usr/bin/env python3
"""Preis-Spiegel eines Kreises: was kosten die Inserate im Markt, nach Groesse + Bewertung.

Reine Ist-Aufnahme aus den gespeicherten Scrape-Daten (Suchseiten-Nachtpreis). KEINE
Vermieter-Optimierung — nur die nuechterne Frage 'was ist der Preis im Kreis'.

WICHTIG: Der oeffentliche Kalender liefert Verfuegbarkeit, aber KEINEN Preis (Feld leer im
Massen-Endpoint). Preise stammen daher aus der Suchseite = ein DATUMS-FENSTER (~6 Wo voraus,
zur Scrape-Zeit). Fuer Preise eines bestimmten Zielmonats braucht es einen datierten Re-Scrape.
Waehrung: Scrape lief in USD -> hier nach CHF umgerechnet (Kurs gelabelt, ~Naeherung).

Aufruf:  py -3.12 tools/pricemap.py Kriens Emmen Horw Ebikon Meggen
"""
import sys, os, json, statistics, collections, argparse
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa

USD_CHF = 0.80  # 1 USD ~ 0.80 CHF (Naeherung 2026; CHF stark). Scrape-Preise sind USD-konvertiert.


def rband(r):
    if r is None: return "ohne Bew."
    if r >= 4.9: return "4.9+"
    if r >= 4.7: return "4.7-4.89"
    if r >= 4.5: return "4.5-4.69"
    return "<4.5"


def size_lbl(b):
    if not b:
        return "? Zi"
    n = int(b)
    if n >= 4:
        return "4+ Zi/8P+"
    return f"{n} Zi/~{n*2}P"


def listing_occ(l):
    """Beste verfuegbare Auslastung je Inserat: Kalender (managed) > Kalender-Roh > Review-Proxy.
    Kalender = 6-Monats-Vorausschau (vorne hoeher durch Vorlaufzeit, hinten tiefer)."""
    for k in ("occ_calendar_pct", "cal_occ_raw_pct", "occ_reviews_pct", "occupancy_proxy_pct"):
        v = l.get(k)
        if v is not None:
            return v
    return None


def market_pricemap(market, comp):
    if market not in comp:
        print(f"\n{market}: keine Scrape-Daten."); return
    L = [l for l in comp[market]["listings"] if l.get("in_market_radius") and l.get("is_entire") is not False]
    rows = []
    for l in L:
        usd = l.get("price_usd")
        if not usd:
            continue
        rows.append({"rating": l.get("rating"), "beds": l.get("bedrooms"),
                     "reviews": l.get("reviews_count"),
                     "price": round(usd * USD_CHF), "occ": listing_occ(l)})
    stand = comp[market].get("fetched", "?")
    print(f"\n{market} — Preis-Spiegel im Kreis  (in-radius, ganze Wohnungen · Stand {stand})")
    if not rows:
        print("  keine Preisdaten."); return
    ps = sorted(r["price"] for r in rows)
    occs_all = [r["occ"] for r in rows if r["occ"] is not None]
    occ_txt = f" · Ausl. ~{round(statistics.median(occs_all))}%" if occs_all else ""
    print(f"  {len(rows)} Inserate · ~CHF/Nacht · Spanne {ps[0]}-{ps[-1]} · "
          f"Median {round(statistics.median(ps))}{occ_txt}")
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(size_lbl(r["beds"]), rband(r["rating"]))].append(r)
    print(f"  {'Groesse':<11}{'Bewertung':<11}{'n':>3}{'Boden':>7}{'Median':>8}{'Spitze':>8}{'Ausl%':>7}")
    for key in sorted(cells):
        cs = cells[key]
        pr = sorted(c["price"] for c in cs)
        oc = [c["occ"] for c in cs if c["occ"] is not None]
        occ = round(statistics.median(oc)) if oc else "-"
        print(f"  {key[0]:<11}{key[1]:<11}{len(cs):>3}{pr[0]:>7}{round(statistics.median(pr)):>8}{pr[-1]:>8}{str(occ):>7}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markets", nargs="+")
    a = ap.parse_args()
    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    print(f"Preise ~CHF/Nacht (USD-Scrape x {USD_CHF}) · Such-Fenster ~6 Wo voraus. "
          f"Ausl% = Kalender 6-Mt-Vorausschau (vorne hoeher/Vorlaufzeit), host-Blocks raus.")
    for mk in a.markets:
        market_pricemap(mk, comp)


if __name__ == "__main__":
    main()
