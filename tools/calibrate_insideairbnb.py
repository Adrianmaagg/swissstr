# -*- coding: utf-8 -*-
"""calibrate_insideairbnb.py — Quervergleich Free-Scrape <-> InsideAirbnb (KEINE Bodenwahrheit).

PRAEMISSE (wichtig): InsideAirbnb ist NICHT die Wahrheit, gegen die wir den Free-Scrape messen.
Es sind ZWEI unabhaengige, je unvollkommene Quellen. Wo sie sich decken -> Konfidenz. Wo sie
divergieren -> wird PRO METRIK gefragt, WELCHE Quelle glaubwuerdiger ist und warum — nicht
automatisch InsideAirbnb. Es kann sehr wohl sein, dass UNSER Live-Scrape die bessere Zahl hat.

Wer wann besser ist:
  - FRISCHE: Free-Scrape ist live (gestern); InsideAirbnb ist ein Stichtags-Snapshot (oft Monate/
    Jahre alt). Das Tool zieht die InsideAirbnb-Aktualitaet (juengstes last_review) raus — ist sie
    alt, ist UNSERE Zahl naeher an der heutigen Marktrealitaet.
  - LIVE-FILTER: Free-Scrape liefert nur aktuell buchbare Inserate. InsideAirbnb enthaelt Zombies
    (0 Reviews, Preis leer, nie gebucht) -> sein Roh-Count UEBERZEICHNET die echte Konkurrenz.
    Das Tool zaehlt diese Zombies offen mit.
  - COVERAGE: InsideAirbnb hat ungleich mehr Inserate (Voll-Stadt) -> stabilere Verteilung.
  - PRO-HOST: hier ist InsideAirbnb klar besser. Der Free-Scrape sieht KEINE Host-Daten
    (is_pro_host hartcodiert False=0). InsideAirbnb (calculated_host_listings_count) liefert den
    echten Profi-Anteil. Das ist unsere bekannte Blindstelle, kein Streitpunkt.
  - PREIS/OCCUPANCY: beidseitig nur Angebotspreis- bzw. Review-Proxy (MOD). Divergenz heisst NICHT
    "Free-Scrape falsch". Gleiche Methode (occupancy_proxy, Radius, Entire-Filter) angewandt, damit
    die Differenz die Daten misst, nicht die Rechnung.

Tier: beide 🟡 MOD. Der Vergleich macht KEINE Seite decision_grade — er sagt nur, wo wir uns auf
den Free-Scrape verlassen koennen und wo eine Quelle die andere korrigiert.

Aufruf:  python tools/calibrate_insideairbnb.py Zürich
"""
import csv
import io
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_airbnb as fa  # occupancy_proxy, haversine_km

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# Waehrungs-Normalisierung NUR fuer den Zusatz-Vergleich — offen ausgewiesen, MOD.
USD_PER_CHF = 1.12  # grob 2026; bewusst konservativ; Vergleich ist indikativ, nicht decision_grade
PRO_HOST_MIN_LISTINGS = 2  # Host mit >=2 Inseraten = Profi/Vollzeit-Indiz


def _f(x):
    try:
        if x is None or str(x).strip() == "":
            return None
        return float(str(x).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _slug(market):
    return market.lower().replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("/", "-").replace(" ", "_")


def load_insideairbnb(market, center, radius_km):
    """Liest <slug>_listings.csv, filtert auf Radius um Marktzentrum + Entire-Home."""
    path = os.path.join(DATA, "insideairbnb", _slug(market) + "_listings.csv")
    if not os.path.exists(path):
        # tolerant: erste passende CSV im Ordner
        d = os.path.join(DATA, "insideairbnb")
        cand = [f for f in os.listdir(d) if f.endswith("_listings.csv")] if os.path.isdir(d) else []
        if len(cand) == 1:
            path = os.path.join(d, cand[0])
        else:
            raise SystemExit("InsideAirbnb-CSV nicht gefunden: %s" % path)

    total_in_radius = 0
    entire = []  # dicts: price, rpm, occ, host_count, reviews, last_review, zombie
    last_reviews = []  # Frische-Signal (juengstes Review im Datensatz)
    with io.open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            lat, lng = _f(row.get("latitude")), _f(row.get("longitude"))
            if lat is None or lng is None:
                continue
            dist = fa.haversine_km(center["lat"], center["lng"], lat, lng)
            if dist is None or dist > radius_km:
                continue
            total_in_radius += 1
            lr = (row.get("last_review") or "").strip()
            if len(lr) == 10 and lr[4] == "-":
                last_reviews.append(lr)
            rt = (row.get("room_type") or "").strip().lower()
            if rt not in ("entire home/apt", "entire home", "entire place"):
                continue
            rpm = _f(row.get("reviews_per_month"))
            price = _f(row.get("price"))
            reviews = _f(row.get("number_of_reviews")) or 0
            entire.append({
                "price": price,
                "rpm": rpm,
                "occ": fa.occupancy_proxy(rpm) if rpm else None,
                "host_count": _f(row.get("calculated_host_listings_count")),
                "reviews": reviews,
                "last_review": lr if lr else None,
                # Zombie = nie/kaum gebuchtes Inserat: keine Reviews UND kein Preis -> haengt im Index,
                # ist aber keine echte Live-Konkurrenz. Free-Scrape filtert solche strukturell raus.
                "zombie": (reviews == 0 and price is None),
                "dist": dist,
            })
    freshest = max(last_reviews) if last_reviews else None
    return total_in_radius, entire, freshest


def _median(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else None


def _iqr(xs):
    xs = sorted(x for x in xs if x is not None)
    if len(xs) < 4:
        return None
    q1 = xs[len(xs) // 4]
    q3 = xs[(len(xs) * 3) // 4]
    return round(q3 - q1, 1)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 1) if xs else None


def build_reference(market, center, radius_km):
    total, entire, freshest = load_insideairbnb(market, center, radius_km)
    # Live-Sicht: Zombies raus, damit der Vergleich gegen den (nur-live) Free-Scrape fair ist.
    live = [e for e in entire if not e["zombie"]]
    n_zombie = len(entire) - len(live)
    prices = [e["price"] for e in live if e["price"] is not None]
    occs = [e["occ"] for e in live if e["occ"] is not None]
    pro = [e for e in live if e["host_count"] and e["host_count"] >= PRO_HOST_MIN_LISTINGS]
    return {
        "source": "InsideAirbnb (Voll-Stadt-Snapshot, MOD — KEINE Bodenwahrheit)",
        "csv": _slug(market) + "_listings.csv",
        "radius_km": radius_km,
        "center": center,
        "freshest_review": freshest,
        "freshness_note": "juengstes last_review im Datensatz = grobes Aktualitaets-Signal des Snapshots",
        "n_total_in_radius": total,
        "n_entire_raw": len(entire),
        "n_entire_zombie": n_zombie,
        "zombie_share_pct": round(100.0 * n_zombie / len(entire), 1) if entire else None,
        "n_entire_live": len(live),
        "entire_share_pct": round(100.0 * len(entire) / total, 1) if total else None,
        "n_entire_with_price": len(prices),
        "adr_median_native": _median(prices),
        "adr_iqr_native": _iqr(prices),
        "n_entire_with_reviews": len(occs),
        "occ_proxy_median_pct": _median(occs),
        "occ_proxy_mean_pct": _mean(occs),
        "pro_host_share_pct": round(100.0 * len(pro) / len(live), 1) if live else None,
        "pro_host_count": len(pro),
        "occ_method": "reviews (identisch zu fetch_airbnb.occupancy_proxy)",
        "price_currency_note": "Listing-Waehrung gemischt (CHF/USD) — nativ, nicht normalisiert",
    }


def load_free_scrape(market):
    c = json.load(io.open(os.path.join(DATA, "airbnb-competitors.json"), encoding="utf-8"))
    z = c.get(market)
    if not z:
        raise SystemExit("Markt nicht in airbnb-competitors.json: %s" % market)
    ent = [l for l in z.get("listings", []) if l.get("is_entire")]
    prices = [l.get("price_usd") for l in ent if l.get("price_usd") is not None]
    return {
        "source": z.get("source", "free-scrape"),
        "fetched": z.get("fetched"),
        "count": z.get("count"),
        "entire_count": z.get("entire_count"),
        "n_entire_with_price": len(prices),
        "adr_median_usd": _median(prices),
        "adr_iqr_usd": _iqr(prices),
        "occ_entire_mean_pct": z.get("avg_occupancy_entire_pct"),
        "pro_host_count": z.get("pro_host_count"),
        "pro_host_note": "Free-Scrape sieht KEINE Host-Daten -> hartcodiert 0 (Blindstelle)",
    }


def build_report(market):
    centers = json.load(io.open(os.path.join(DATA, "market-centers.json"), encoding="utf-8"))
    c = centers.get(market)
    if not c:
        raise SystemExit("Markt nicht in market-centers.json: %s" % market)
    radius_km = c.get("radius_km", 8)
    center = {"lat": c["lat"], "lng": c["lng"]}

    gt = build_reference(market, center, radius_km)
    fs = load_free_scrape(market)

    # Normalisierter ADR-Vergleich (offen ausgewiesener Kurs) — indikativ.
    adr_gt_usd = round(gt["adr_median_native"] * USD_PER_CHF, 1) if gt["adr_median_native"] else None
    adr_delta_pct = None
    if adr_gt_usd and fs["adr_median_usd"]:
        adr_delta_pct = round(100.0 * (fs["adr_median_usd"] - adr_gt_usd) / adr_gt_usd, 1)

    occ_delta_pp = None
    if gt["occ_proxy_mean_pct"] is not None and fs["occ_entire_mean_pct"] is not None:
        occ_delta_pp = round(fs["occ_entire_mean_pct"] - gt["occ_proxy_mean_pct"], 1)

    deltas = {
        "adr_median_usd_free": fs["adr_median_usd"],
        "adr_median_usd_reference_normalized": adr_gt_usd,
        "adr_delta_pct": adr_delta_pct,
        "adr_currency_assumption": "InsideAirbnb-Preis x %.2f USD/CHF (MOD, offen ausgewiesen)" % USD_PER_CHF,
        "occ_entire_free_pct": fs["occ_entire_mean_pct"],
        "occ_entire_reference_pct": gt["occ_proxy_mean_pct"],
        "occ_delta_pp": occ_delta_pp,
        "pro_host_free": fs["pro_host_count"],
        "pro_host_reference_pct": gt["pro_host_share_pct"],
        "sample_ratio": "%s (free, live) vs %s (InsideAirbnb live entweder/radius, %s Zombies entfernt)" % (
            fs["entire_count"], gt["n_entire_live"], gt["n_entire_zombie"]),
    }

    verdict = _verdict(deltas, fs, gt)

    return {
        "market": market,
        "tier": "MOD — Quervergleich zweier unvollkommener Quellen, KEINE Seite decision_grade",
        "premise": "InsideAirbnb ist NICHT Bodenwahrheit. Pro Metrik wird gefragt, welche Quelle glaubwuerdiger ist.",
        "reference": gt,
        "free_scrape": fs,
        "deltas": deltas,
        "verdict": verdict,
        "caveats": [
            "InsideAirbnb = Stichtags-Snapshot (juengstes Review %s); Free-Scrape = live (%s)." % (
                gt["freshest_review"], fs["fetched"]),
            "InsideAirbnb-Rohcount enthielt %s Zombie-Inserate (0 Reviews + kein Preis) -> hier rausgefiltert." % gt["n_entire_zombie"],
            "Preis-Waehrung gemischt; ADR-Vergleich indikativ (Kurs %.2f offen)." % USD_PER_CHF,
            "Occupancy beidseitig nur Review-Proxy (MOD), kein Kalender.",
            "Pro-Host: nur InsideAirbnb hat Host-Daten -> hier ist es die bessere Quelle, Free-Scrape ist blind.",
        ],
    }


def _credibility(metric, free_val, ref_val, fresh, fetched):
    """Sagt, WELCHE Quelle bei dieser Metrik glaubwuerdiger ist — nicht automatisch InsideAirbnb."""
    stale = (fresh or "9999") < "2026-01"  # Snapshot aelter als ~6 Mt -> Free-Scrape frischer
    if metric == "pro_host":
        return "InsideAirbnb (Free-Scrape strukturell blind)"
    if stale:
        return "Free-Scrape frischer (Snapshot last_review %s vs live %s) -> bei Divergenz eher uns glauben" % (fresh, fetched)
    return "beide aktuell -> Divergenz = echte Stichproben-/Methoden-Streuung, keine Seite gewinnt klar"


def _verdict(d, fs, gt):
    v = []
    fresh, fetched = gt["freshest_review"], fs["fetched"]
    # ADR — kein "richtig/falsch"-Tag gegen InsideAirbnb, sondern Naehe + welche Quelle glaubwuerdiger
    if d["adr_delta_pct"] is not None:
        a = abs(d["adr_delta_pct"])
        nah = "decken sich" if a <= 15 else ("grob plausibel" if a <= 30 else "divergieren")
        v.append("ADR %s: Free %s USD vs InsideAirbnb~%s USD (%+.0f%%). %s" % (
            nah, fs["adr_median_usd"], d["adr_median_usd_reference_normalized"], d["adr_delta_pct"],
            _credibility("adr", fs["adr_median_usd"], d["adr_median_usd_reference_normalized"], fresh, fetched)))
    # Occupancy
    if d["occ_delta_pp"] is not None:
        a = abs(d["occ_delta_pp"])
        nah = "decken sich" if a <= 8 else ("grob plausibel" if a <= 18 else "divergieren")
        v.append("Occupancy(Review) %s: Free %s%% vs InsideAirbnb %s%% (%+.0f pp). %s" % (
            nah, fs["occ_entire_mean_pct"], gt["occ_proxy_mean_pct"], d["occ_delta_pp"],
            _credibility("occ", fs["occ_entire_mean_pct"], gt["occ_proxy_mean_pct"], fresh, fetched)))
    # Pro-Host — die eine Metrik, wo InsideAirbnb klar besser ist
    if gt["pro_host_share_pct"] is not None:
        v.append("Pro-Host: Free sieht 0%%, InsideAirbnb %.0f%% (%s von %s live entire). "
                 "Hier korrigiert InsideAirbnb uns -> Free-Scrape unterschaetzt Profi-Konkurrenz systematisch." % (
                     gt["pro_host_share_pct"], gt["pro_host_count"], gt["n_entire_live"]))
    # Coverage vs Frische — der Kern von Adrians Einwand
    v.append("Coverage: InsideAirbnb %s live entire (%s Zombies entfernt) vs Free %s. "
             "Mehr Masse (stabiler) ABER Stichtag %s; Free ist live %s." % (
                 gt["n_entire_live"], gt["n_entire_zombie"], fs["entire_count"], fresh, fetched))
    return v


def main():
    market = sys.argv[1] if len(sys.argv) > 1 else "Zürich"
    rep = build_report(market)
    out = os.path.join(DATA, "insideairbnb-calibration.json")
    # bestehende Reports anderer Maerkte erhalten
    existing = {}
    if os.path.exists(out):
        try:
            existing = json.load(io.open(out, encoding="utf-8"))
        except (ValueError, OSError):
            existing = {}
    if not isinstance(existing, dict) or "market" in existing:
        existing = {}  # altes single-market Format -> neu als dict-of-markets
    existing[market] = rep
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(existing, ensure_ascii=False, indent=2))

    print("=== Kalibrierung %s — Free-Scrape vs InsideAirbnb ===" % market)
    for line in rep["verdict"]:
        print(" -", line)
    print("Report -> %s" % out)


if __name__ == "__main__":
    main()
