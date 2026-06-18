#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Morgen-Briefing: ein lernender Discovery-Loop ueber die schon gesammelten Cockpit-Daten.

Der Daily-Scrape SAMMELT nur. Dieser Schritt DESTILLIERT taeglich das, was Adrian
morgens in 30 Sekunden wissen will - und schaerft sich mit, weil er die wachsende
Snapshot-Historie nutzt (Neuzugaenge sind nur sichtbar, weil es einen Vortag gibt):

  NEUSTARTER   - gerade neu aufgetauchtes Inserat mit wenig/keinen Bewertungen ->
                 Eigentuemer ist frisch dabei, evtl. ueberfordert = R2R-/Mandats-Ziel,
                 das man manuell nie rechtzeitig findet.
  STILLE PERLE - fast immer ausgebucht, aber UNTER dem Markt-Preis -> unterbepreister
                 Betreiber = Uebernahme-/Mandats-Kandidat ("ich hol mehr raus").
  TOP-VERDIENER- wer verdient am meisten + was macht er anders (lebendes Playbook,
                 zeigt neue Orte/Strategien).
  BEWEGUNG     - echter Pickup ueber Nacht (frei->belegt) je Markt, aus pickup.json.

Rechnet NICHTS Spekulatives - alle Werte sind aus echten Scrape-Inputs abgeleitet
(Tier MOD). Schreibt data/briefing.json; briefing.html rendert es.

Aufruf:  python tools/briefing.py
"""
import os, sys, json, glob, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import briefing_mails  # Postfach-Inserate (Gmail-Suchagent, nur lokal mit Heimstatt-Agent)
except Exception:
    briefing_mails = None

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SNAP = os.path.join(DATA, "snapshots")

# --- Schwellen (transparent, im UI als Methode dokumentiert) ---
NEW_REVIEWS_MAX = 3      # <= so wenige Bewertungen => "frisch gestartet"
FRESH_ID_DIGITS = 12     # moderne Airbnb-IDs sind ~19-stellig; alte (re-aufgetauchte) ~8 -> kein echter Neustart
STRONG_OCC      = 70     # occ@30 >= % => starke Nachfrage (Perle-Kandidat)
UNDERPRICE      = 0.85   # Preis <= 85% des Markt-Medians (gleiche Kapazitaet) => unterbepreist
MIN_BUCKET      = 4      # so viele Vergleichs-Inserate noetig, sonst Fallback Gesamt-Median


def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _market_files():
    """Alle Serving-Cockpits (cockpit-<m>.json), ohne -pickup/-markets/-season."""
    out = []
    for p in sorted(glob.glob(os.path.join(DATA, "cockpit-*.json"))):
        base = os.path.basename(p)[len("cockpit-"):-len(".json")]
        if base.endswith("-pickup") or base in ("markets", "season-proxy"):
            continue
        out.append((base, p))
    return out


def _monthly_gross(l):
    """Brutto-Monatsumsatz ~ Preis x occ@30 x 30 (gleiche Logik wie im Cockpit)."""
    occ = (l.get("occ") or {}).get("30")
    pr = l.get("price_chf")
    if occ is None or pr is None:
        return None
    return round(pr * (occ / 100.0) * 30)


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _dedup_by_host(cards):
    """Pro Betreiber (host-Name) nur das STAERKSTE Inserat behalten. Sonst erscheint eine
    Firma mit mehreren Inseraten (z.B. 'Spirit Apartments') mehrfach in der Top-Verdiener-Liste
    - Adrian will je Betreiber EINEN Eintrag (das Portfolio steht ja als 'N Inserate' dran)."""
    best = {}
    for c in cards:
        key = (c.get("host") or "").strip().lower() or str(c.get("id"))
        if key not in best or c["monthly_gross"] > best[key]["monthly_gross"]:
            best[key] = c
    return sorted(best.values(), key=lambda x: x["monthly_gross"], reverse=True)


def _snapshot_ids(market_id):
    """(prev_ids, curr_date) aus den zwei letzten Snapshots; (None, None) wenn <2."""
    files = sorted(glob.glob(os.path.join(SNAP, market_id, "*.json")))
    if len(files) < 2:
        return None, None
    prev = _load(files[-2])
    curr = _load(files[-1])
    prev_ids = {l["id"] for l in prev.get("listings", [])}
    curr_ids = {l["id"] for l in curr.get("listings", [])}
    return (curr_ids - prev_ids), curr.get("date")


def _listing_card(market_name, market_id, l, reason, extra=None):
    occ30 = (l.get("occ") or {}).get("30")
    card = {
        "market": market_name, "market_id": market_id,
        "id": l["id"], "url": l.get("url"),
        "host": l.get("host"), "capacity": l.get("capacity"),
        "room_type": l.get("room_type"), "superhost": l.get("superhost"),
        "reviews": l.get("reviews"), "rating": l.get("rating"),
        "price_chf": l.get("price_chf"), "occ30": occ30,
        "monthly_gross": _monthly_gross(l),
        "portfolio": l.get("portfolio_in_market"),
        "reason": reason,
    }
    if extra:
        card.update(extra)
    return card


def analyse_market(market_id, path):
    c = _load(path)
    name = (c.get("_meta") or {}).get("market") or market_id.title()
    listings = c.get("listings", [])
    inmun = [l for l in listings if l.get("in_municipality")]
    by_id = {l["id"]: l for l in listings}

    # Markt-Median-Preis je Kapazitaet (fuer "unter Marktpreis")
    cap_prices = {}
    for l in inmun:
        if l.get("price_chf"):
            cap_prices.setdefault(l.get("capacity"), []).append(l["price_chf"])
    overall_med = _median([l["price_chf"] for l in inmun if l.get("price_chf")])

    def market_price_for(l):
        bucket = cap_prices.get(l.get("capacity"), [])
        return _median(bucket) if len(bucket) >= MIN_BUCKET else overall_med

    # --- Neuzugaenge (braucht >=2 Snapshots) ---
    appeared, curr_date = _snapshot_ids(market_id)
    neustarter, neuzugaenge = [], []
    if appeared is not None:
        for lid in appeared:
            l = by_id.get(lid)
            if not l or not l.get("in_municipality"):
                continue
            rv = l.get("reviews")
            fresh_id = str(lid).isdigit() and len(str(lid)) >= FRESH_ID_DIGITS
            if (rv is None or rv <= NEW_REVIEWS_MAX) and fresh_id:
                neustarter.append(_listing_card(name, market_id, l,
                    f"Gerade neu aufgetaucht, erst {rv if rv is not None else 0} Bewertungen "
                    f"- Eigentuemer frisch dabei, idealer R2R-/Mandats-Kontakt."))
            elif rv is None or rv <= NEW_REVIEWS_MAX:
                # wenig Bewertungen, aber ALTE ID -> kein echter Neustart, nur in der Suche re-aufgetaucht.
                neuzugaenge.append(_listing_card(name, market_id, l,
                    "Altes Inserat neu in der Suche aufgetaucht (kurze ID = kein echter Neustart)."))
            else:
                neuzugaenge.append(_listing_card(name, market_id, l,
                    f"Neu in der Suche ({rv} Bewertungen) - etablierter Host, beobachten."))

    # --- Stille Perlen (braucht nur den aktuellen Stand) ---
    stille = []
    for l in inmun:
        occ30 = (l.get("occ") or {}).get("30")
        pr = l.get("price_chf")
        if occ30 is None or pr is None or occ30 < STRONG_OCC:
            continue
        med = market_price_for(l)
        if med and pr <= UNDERPRICE * med:
            gap = round(med - pr)
            stille.append(_listing_card(name, market_id, l,
                f"{occ30}% belegt, aber nur CHF {pr} - rund CHF {gap} unter dem Marktpreis "
                f"(Median CHF {round(med)}). Unterbepreist = Mandats-Chance.",
                extra={"market_price": round(med), "price_gap": gap,
                       "money_score": round((med - pr) / med * occ30, 1)}))

    # --- Top-Verdiener ---
    earners = []
    for l in inmun:
        mg = _monthly_gross(l)
        if mg:
            earners.append(_listing_card(name, market_id, l, ""))
    earners.sort(key=lambda x: x["monthly_gross"], reverse=True)
    for e in earners:
        e["reason"] = (f"CHF {e['monthly_gross']}/Mt brutto bei {e['occ30']}% Belegung, "
                       f"{e['capacity']} Pers, CHF {e['price_chf']}/Nacht"
                       + (", Superhost" if e.get("superhost") else "")
                       + (f", {e['portfolio']} Inserate im Markt" if (e.get('portfolio') or 0) > 1 else "")
                       + ".")

    # --- Bewegung ueber Nacht (Pickup) ---
    pickup = None
    pp = os.path.join(DATA, f"cockpit-{market_id}-pickup.json")
    if os.path.exists(pp):
        d = _load(pp)
        pickup = {"net": d.get("net"), "net_per_day": d.get("net_per_day"),
                  "newly_booked": d.get("newly_booked"), "freed": d.get("freed"),
                  "appeared": d.get("appeared"), "from": d.get("prev_date"), "to": d.get("curr_date"),
                  "days": d.get("days"), "lead_buckets": d.get("lead_buckets")}

    return {
        "name": name, "market_id": market_id,
        "n_listings": len(listings), "n_in_municipality": len(inmun),
        "neustarter": neustarter, "neuzugaenge": neuzugaenge,
        "stille_perlen": sorted(stille, key=lambda x: x["money_score"], reverse=True),
        "top_verdiener": _dedup_by_host(earners)[:3],
        "pickup": pickup, "has_history": appeared is not None,
    }


def main():
    markets = _market_files()
    if not markets:
        sys.exit("Keine cockpit-<m>.json gefunden - erst der Tageslauf muss laufen.")
    by_market = {}
    for mid, path in markets:
        try:
            by_market[mid] = analyse_market(mid, path)
        except Exception as e:
            print(f"  WARNUNG {mid}: {e}")

    # Cross-Markt-Highlights (das, was oben auf der Seite steht)
    all_neustarter, all_stille, all_earners, bewegung = [], [], [], []
    for m in by_market.values():
        all_neustarter += m["neustarter"]
        all_stille += m["stille_perlen"]
        all_earners += m["top_verdiener"]
        if m["pickup"] and m["pickup"].get("net") is not None:
            bewegung.append({"market": m["name"], "market_id": m["market_id"], **m["pickup"]})
    all_neustarter.sort(key=lambda x: (-(x["occ30"] or 0), x["reviews"] if x["reviews"] is not None else -1))
    all_stille.sort(key=lambda x: x["money_score"], reverse=True)
    all_earners.sort(key=lambda x: x["monthly_gross"], reverse=True)
    bewegung.sort(key=lambda x: (x["net"] if x["net"] is not None else -999), reverse=True)

    today = datetime.date.today().isoformat()
    out = {
        "generated": today,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "markets_covered": sorted(m["name"] for m in by_market.values()),
        "summary": {
            "neustarter": len(all_neustarter),
            "stille_perlen": len(all_stille),
            "neuzugaenge": sum(len(m["neuzugaenge"]) for m in by_market.values()),
            "net_pickup": sum(b["net"] for b in bewegung if b.get("net") is not None),
            "markets": len(by_market),
            "markets_with_history": sum(1 for m in by_market.values() if m["has_history"]),
        },
        "highlights": {
            "neustarter": all_neustarter[:12],
            "stille_perlen": all_stille[:12],
            "top_verdiener": _dedup_by_host(all_earners)[:10],
            "bewegung": bewegung,
        },
        "by_market": by_market,
        "method": ("MOD - abgeleitet aus echten Scrape-Inputs. Neustarter: neu im Snapshot-Vergleich "
                   f"mit <= {NEW_REVIEWS_MAX} Bewertungen UND moderner (>= {FRESH_ID_DIGITS}-stelliger) Airbnb-ID "
                   "(alte re-aufgetauchte Inserate -> Neuzugaenge, kein echter Neustart). "
                   f"Stille Perle: occ@30 >= {STRONG_OCC}% und Preis "
                   f"<= {int(UNDERPRICE*100)}% des Markt-Medians (gleiche Kapazitaet). "
                   "Top-Verdiener: Preis x occ@30 x 30. Bewegung: frei->belegt seit letztem Snapshot."),
    }
    p = os.path.join(DATA, "briefing.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    # --- Postfach: Inserate aus dem Gmail-Suchagent -> SEPARATE LOKALE Datei ---
    # Enthaelt Vermieter-Namen/Objekte = NICHT ins (public) Repo. Gitignored, briefing.html
    # laedt sie zusaetzlich; im Cloud-Lauf fehlt sie -> Sektion bleibt leer.
    pf_n = 0
    if briefing_mails is not None:
        try:
            pf = briefing_mails.collect()
            pf_n = pf.get("count", 0) if pf.get("available") else 0
            with open(os.path.join(DATA, "briefing-postfach.local.json"), "w",
                      encoding="utf-8", newline="\n") as fh:
                json.dump(pf, fh, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  Postfach uebersprungen: {e}")
    s = out["summary"]
    print(f"Briefing {today}: {s['neustarter']} Neustarter, {s['stille_perlen']} stille Perlen, "
          f"{s['neuzugaenge']} weitere Neuzugaenge, Netto-Pickup {s['net_pickup']:+d} Naechte "
          f"ueber {s['markets']} Maerkte ({s['markets_with_history']} mit Historie); "
          f"{pf_n} Postfach-Inserate.")
    print(f"  -> {p}")


if __name__ == "__main__":
    main()
