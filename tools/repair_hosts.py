#!/usr/bin/env python3
"""Einmal-Heilung: Inserate mit host==None in den Serving-Cockpits bekamen bei einem
Scrape-Lauf eine transient nicht geladene Host-Karte -> Host-Name/ID wurden zu null
ueberschrieben ("fehlen jetzt mehrere Hosts"). Der aktuelle Code zieht die Hosts wieder
sauber; dieses Skript holt GEZIELT nur die betroffenen Inserate neu und patcht:

  - data/cockpit-*.json   (Serving-Daten, die die App liest)
  - data/airbnb-competitors.json (Quelle, pdp_*-Felder) — damit der naechste Lauf konsistent bleibt

Die Wurzel ist mit der Selbstheilung in pdp_enrich.py (merge_pdp) bereits geschlossen.

Aufruf:  python tools/repair_hosts.py [--max N]
"""
import sys, os, json, glob, time, argparse
sys.path.insert(0, os.path.dirname(__file__))
import pdp_enrich as pe

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# cockpit-Feld <- fetch_pdp-Feld
HOST_MAP = {
    "host": "pdp_host_name", "host_id": "pdp_host_id", "host_uid": "pdp_host_uid",
    "host_total_reviews": "pdp_host_total_reviews", "host_rating": "pdp_host_rating",
    "host_title": "pdp_host_title", "years_hosting": "pdp_years_hosting",
    "host_started_year": "pdp_host_started_year",
}


def _cockpit_files():
    out = []
    for p in sorted(glob.glob(os.path.join(DATA, "cockpit-*.json"))):
        base = os.path.basename(p)[len("cockpit-"):-len(".json")]
        if base.endswith("-pickup") or base in ("markets", "season-proxy"):
            continue
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=200, help="max. PDP-Fetches (Schutz)")
    a = ap.parse_args()

    files = _cockpit_files()
    # 1) alle host-losen Inserate sammeln (id -> [(file, listing), ...])
    missing = {}
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        for l in d.get("listings", []):
            if l.get("host") is None and l.get("id"):
                missing.setdefault(str(l["id"]), []).append((p, l))
    ids = list(missing.keys())[:a.max]
    print(f"{len(missing)} host-lose Inserate ueber {len(files)} Maerkte; fetche {len(ids)} (~{pe.PACE_S}s/Stk) ...")

    # 2) je id EINMAL die PDP ziehen, Host-Felder extrahieren
    fixed_fields = {}   # id -> {cockpit_field: value}
    healed = 0
    for i, rid in enumerate(ids):
        dp = pe.fetch_pdp(rid)
        time.sleep(pe.PACE_S)
        if not dp or not dp.get("pdp_host_name"):
            continue
        fixed_fields[rid] = {ck: dp.get(pk) for ck, pk in HOST_MAP.items()}
        healed += 1
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(ids)} ...")
    print(f"  {healed} Hosts wieder ausgelesen.")

    # 3) Cockpit-Dateien patchen (nur die geheilten, nur wo host noch null)
    touched_files = set()
    for rid, vals in fixed_fields.items():
        for p, _l in missing.get(rid, []):
            touched_files.add(p)
    for p in sorted(touched_files):
        d = json.load(open(p, encoding="utf-8"))
        changed = 0
        for l in d.get("listings", []):
            if l.get("host") is None and str(l.get("id")) in fixed_fields:
                for ck, v in fixed_fields[str(l["id"])].items():
                    if v is not None or ck not in l:
                        l[ck] = v
                changed += 1
        if changed:
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
            print(f"  {os.path.basename(p)}: {changed} Hosts gepatcht")

    # 4) Quelle (airbnb-competitors.json) ebenfalls patchen (pdp_*-Felder), best effort
    comp_p = os.path.join(DATA, "airbnb-competitors.json")
    if os.path.exists(comp_p):
        comp = json.load(open(comp_p, encoding="utf-8"))
        cn = 0
        for mkt in comp.values():
            if not isinstance(mkt, dict):
                continue
            for l in mkt.get("listings", []):
                rid = str(l.get("id"))
                if rid in fixed_fields and not l.get("pdp_host_name"):
                    for ck, v in fixed_fields[rid].items():
                        l[HOST_MAP[ck]] = v
                    cn += 1
        if cn:
            with open(comp_p, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(comp, fh, ensure_ascii=False, indent=2)
            print(f"  airbnb-competitors.json: {cn} Eintraege gepatcht")

    print(f"FERTIG: {healed} Hosts geheilt.")


if __name__ == "__main__":
    main()
