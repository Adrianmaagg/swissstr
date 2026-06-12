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
    return f"{int(b)} Zi/~{int(b)*2}P" if b else "? Zi"


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
                     "price": round(usd * USD_CHF)})
    stand = comp[market].get("fetched", "?")
    print(f"\n{market} — Preis-Spiegel im Kreis  (in-radius, ganze Wohnungen · Stand {stand})")
    if not rows:
        print("  keine Preisdaten."); return
    ps = sorted(r["price"] for r in rows)
    print(f"  {len(rows)} Inserate · ~CHF/Nacht · Spanne {ps[0]}-{ps[-1]} · unteres Viertel {ps[len(ps)//4]} · "
          f"Median {round(statistics.median(ps))} · oberes Viertel {ps[len(ps)*3//4]}")
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(size_lbl(r["beds"]), rband(r["rating"]))].append(r)
    print(f"  {'Groesse':<11}{'Bewertung':<11}{'n':>3}{'Boden':>7}{'Median':>8}{'Spitze':>8}")
    for key in sorted(cells):
        pr = sorted(c["price"] for c in cells[key])
        print(f"  {key[0]:<11}{key[1]:<11}{len(pr):>3}{pr[0]:>7}{round(statistics.median(pr)):>8}{pr[-1]:>8}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markets", nargs="+")
    a = ap.parse_args()
    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    print(f"Preise ~CHF/Nacht (USD-Scrape x {USD_CHF}) · Such-Fenster ~6 Wo voraus zur Scrape-Zeit.")
    for mk in a.markets:
        market_pricemap(mk, comp)


if __name__ == "__main__":
    main()
