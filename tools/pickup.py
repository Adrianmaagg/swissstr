#!/usr/bin/env python3
"""Pickup-Analyse: vergleicht zwei datierte Cockpit-Snapshots und zeigt die ECHTEN Buchungen
dazwischen (ein Tag, der von frei -> belegt springt) + Buchungs-Velocity + Vorlaufzeit-Verteilung.

Das ist der Payoff der Snapshot-Retention (data/snapshots/): aus >=2 Tagen wird die Pickup-Kurve
messbar — genau das, was ein einzelner Snapshot prinzipiell nicht kann (Vorlaufzeit von Saison trennen).

Ehrlich: frei->belegt ist sehr wahrscheinlich eine Buchung (v.a. nahe Tage), KANN aber auch ein
host-Block sein; belegt->frei ist Storno ODER Block-Freigabe. Mit der Zeit (viele Tage) wird das
Muster eindeutig. Velocity der NAHEN Tage ist das staerkste Buchungssignal.

Aufruf:
  py -3.12 tools/pickup.py Kriens          # eine Gemeinde, letzte zwei Snapshots
  py -3.12 tools/pickup.py --all           # alle Gemeinden
  py -3.12 tools/pickup.py Kriens --json    # zusaetzlich data/cockpit-kriens-pickup.json schreiben
"""
import os, sys, json, glob, datetime, argparse

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SNAP = os.path.join(DATA, "snapshots")


def snapshot_files(commune):
    return sorted(glob.glob(os.path.join(SNAP, commune.lower(), "*.json")))


def _load(f):
    return json.load(open(f, encoding="utf-8"))


def _booked_by_id(snap):
    return {l["id"]: set(l.get("booked", [])) for l in snap.get("listings", [])}


def diff_snapshots(prev, curr):
    """Aggregierte + pro-Inserat Pickup-Zahlen zwischen zwei Snapshots (nur gemeinsame Inserate)."""
    pb, cb = _booked_by_id(prev), _booked_by_id(curr)
    common = set(pb) & set(cb)
    per = []
    tot_new = tot_freed = 0
    for lid in common:
        nb = cb[lid] - pb[lid]   # frei -> belegt  = Buchung
        fr = pb[lid] - cb[lid]   # belegt -> frei  = Storno / Block-Freigabe
        tot_new += len(nb); tot_freed += len(fr)
        if nb or fr:
            per.append({"id": lid, "newly_booked": sorted(nb), "freed": sorted(fr)})
    return {
        "prev_date": prev.get("date"), "curr_date": curr.get("date"),
        "n_common": len(common), "appeared": len(set(cb) - set(pb)), "disappeared": len(set(pb) - set(cb)),
        "newly_booked": tot_new, "freed": tot_freed, "net": tot_new - tot_freed,
        "per_listing": per,
    }


def lead_buckets(dates, asof):
    """Verteilt neu gebuchte Daten nach Vorlaufzeit (Tage ab asof)."""
    a = datetime.date.fromisoformat(asof)
    b = {"0-14": 0, "15-30": 0, "31-60": 0, "61+": 0}
    for d in dates:
        dd = (datetime.date.fromisoformat(d) - a).days
        if dd < 0:      continue
        elif dd <= 14:  b["0-14"] += 1
        elif dd <= 30:  b["15-30"] += 1
        elif dd <= 60:  b["31-60"] += 1
        else:           b["61+"] += 1
    return b


def report(commune, write_json=False):
    files = snapshot_files(commune)
    if len(files) < 2:
        print(f"{commune}: erst {len(files)} Snapshot — Pickup braucht >=2 Tage (kommt mit dem naechsten Tageslauf).")
        return None
    prev, curr = _load(files[-2]), _load(files[-1])
    d = diff_snapshots(prev, curr)
    days = (datetime.date.fromisoformat(d["curr_date"]) - datetime.date.fromisoformat(d["prev_date"])).days or 1
    all_new = [x for p in d["per_listing"] for x in p["newly_booked"]]
    buckets = lead_buckets(all_new, d["curr_date"])
    print(f"=== {commune}  {d['prev_date']} -> {d['curr_date']}  ({days} Tag/e) ===")
    print(f"  Inserate verglichen: {d['n_common']}  (neu im Markt: {d['appeared']}, verschwunden: {d['disappeared']})")
    print(f"  Neu gebucht (frei->belegt):              {d['newly_booked']:>4} Naechte")
    print(f"  Frei geworden (Storno/Block-Freigabe):   {d['freed']:>4} Naechte")
    print(f"  NETTO Pickup:                            {d['net']:>+4} Naechte   ({d['net']/days:+.1f}/Tag)")
    print(f"  Neu-Buchungen nach Vorlaufzeit:  0-14T {buckets['0-14']} | 15-30T {buckets['15-30']} | 31-60T {buckets['31-60']} | 61+T {buckets['61+']}")
    out = {k: v for k, v in d.items() if k != "per_listing"}
    out.update({"days": days, "net_per_day": round(d["net"] / days, 2), "lead_buckets": buckets})
    if write_json:
        p = os.path.join(DATA, f"cockpit-{commune.lower()}-pickup.json")
        json.dump(out, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
        print(f"  -> {p}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(SNAP):
        sys.exit("Noch keine Snapshots (data/snapshots/). Erst der Tageslauf muss laufen.")
    if a.all:
        communes = sorted(d for d in os.listdir(SNAP) if os.path.isdir(os.path.join(SNAP, d)))
        for c in communes:
            report(c, a.json)
            print()
    elif a.market:
        report(a.market, a.json)
    else:
        ap.error("Gemeinde angeben oder --all")


if __name__ == "__main__":
    main()
