#!/usr/bin/env python3
"""Coverage-Status der Cockpit-Snapshots (data/snapshots/<gemeinde>/<datum>.json).

Zeigt pro Gemeinde: erster/letzter Tag, Anzahl Tage, LUECKEN (verpasste Tage in der Spanne),
Inserate im letzten Snapshot, belegte Kalendertage gesamt. So sieht man auf einen Blick,
ob die taegliche Sammlung lueckenlos laeuft.

Aufruf:  py -3.12 tools/snapshot_status.py
"""
import os, json, datetime, glob

SNAPDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "snapshots")


def daterange_gaps(dates):
    """Fehlende Kalendertage zwischen erstem und letztem vorhandenen Datum."""
    if len(dates) < 2:
        return []
    ds = [datetime.date.fromisoformat(d) for d in dates]
    have = set(ds)
    gaps, d, last = [], ds[0], ds[-1]
    while d <= last:
        if d not in have:
            gaps.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return gaps


def main():
    if not os.path.isdir(SNAPDIR):
        print("Noch keine Snapshots (data/snapshots/ fehlt). Erst tools/compdata.py <Markt> laufen lassen.")
        return
    communes = sorted(d for d in os.listdir(SNAPDIR) if os.path.isdir(os.path.join(SNAPDIR, d)))
    if not communes:
        print("data/snapshots/ ist leer.")
        return
    print(f"{'Gemeinde':14} {'erster':12} {'letzter':12} {'Tage':>5} {'Lueck':>6} {'Inser.':>7} {'bel.Tage':>9}")
    print("-" * 70)
    tot_days = tot_booked = 0
    for c in communes:
        files = sorted(glob.glob(os.path.join(SNAPDIR, c, "*.json")))
        dates = [os.path.splitext(os.path.basename(f))[0] for f in files]
        if not dates:
            continue
        gaps = daterange_gaps(dates)
        # letzter Snapshot: Inserate + belegte Tage
        try:
            last = json.load(open(files[-1], encoding="utf-8"))
            n_ins = last.get("n", len(last.get("listings", [])))
            booked = sum(len(l.get("booked", [])) for l in last.get("listings", []))
        except Exception:
            n_ins = booked = 0
        flag = "" if not gaps else f"  <-- {len(gaps)} verpasst"
        print(f"{c:14} {dates[0]:12} {dates[-1]:12} {len(dates):>5} {len(gaps):>6} {n_ins:>7} {booked:>9}{flag}")
        tot_days += len(dates)
        tot_booked += booked
    print("-" * 70)
    print(f"{len(communes)} Gemeinden · {tot_days} Snapshot-Tage gesamt · {tot_booked} belegte Kalendertage im jeweils letzten Stand")
    # Hinweis auf Luecken
    any_gap = any(daterange_gaps(sorted(os.path.splitext(os.path.basename(f))[0]
                  for f in glob.glob(os.path.join(SNAPDIR, c, "*.json")))) for c in communes)
    if any_gap:
        print("ACHTUNG: Luecken vorhanden — taeglicher Lauf hat Tage verpasst (siehe 'Lueck'-Spalte).")
    else:
        print("Keine Luecken — lueckenlose Tagesreihe.")


if __name__ == "__main__":
    main()
