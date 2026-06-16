#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_operator_network.py — erzeugt data/operator-network.json: den OPERATOR-GRAPHEN ueber
alle gescrapten Maerkte. Adrians Befund: Top-Betreiber sind Co-Hosting-NETZWERKE mit Hierarchie,
kein flaches host_id-Portfolio. Beispiel Vitznau: Carmen (686 Gesamt-Bewertungen, 'Business'/
Superhost) = Lead; Yannick (eigene Inserate + Co-Host bei Carmen) = Coach/Partner; die zwei 'Jan'
= Assistenten (nur Co-Host, kein eigenes Inserat).

Quelle: data/cockpit-*.json (host_uid + host_total_reviews + cohosts, von pdp_enrich/compdata).
Verknuepfung: pro Inserat Kante Lead-host_uid <-> jede cohost-uid; gleiche nackte Zahl = gleiche
Person (Lead kommt als DemandUser:<n>, Co-Host als User:<n>). Connected-Components = Netzwerke.

Rolle:  lead      = eigene Inserate UND (>=50 Operator-Bewertungen ODER Titel 'Business' ODER >=3 Inserate)
        host      = eigene Inserate, aber kleiner/unabhaengig
        assistant = NUR Co-Host, kein eigenes Inserat

Schreibt: operators{uid->Knoten} + networks[] (>=2 Mitglieder mit echtem Co-Hosting).
"""
import json, os, glob
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def cockpit_files():
    for f in sorted(glob.glob(os.path.join(DATA, "cockpit-*.json"))):
        b = os.path.basename(f)
        if b.endswith("-pickup.json") or "markets" in b or "season" in b:
            continue
        yield f, b


class UF:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb: self.p[ra] = rb


def est_month_chf(price, occ30):
    """Brutto-Monatsumsatz-Schaetzung (Tier MOD): Nachtpreis x Belegung@30 x 30 Naechte."""
    if not price or occ30 is None:
        return 0
    return round(price * (occ30 / 100.0) * 30)


def main():
    ops = {}          # uid -> Knoten
    edges = []        # (lead_uid, cohost_uid)

    def node(uid, name=None):
        n = ops.get(uid)
        if not n:
            n = ops[uid] = {
                "uid": uid, "name": name, "own": [], "markets": set(),
                "host_total_reviews": None, "host_rating": None, "host_title": None,
                "superhost": None, "cohost_on": [], "partners": {},
            }
        if name and not n["name"]:
            n["name"] = name
        return n

    for f, b in cockpit_files():
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        mkt = (d.get("_meta") or {}).get("market") or b.replace("cockpit-", "").replace(".json", "")
        for l in d.get("listings", []):
            huid = l.get("host_uid")
            if not huid:
                continue
            huid = str(huid)
            op = node(huid, l.get("host"))
            occ30 = (l.get("occ") or {}).get("30")
            op["own"].append({
                "id": l.get("id"), "market": mkt, "url": l.get("url"),
                "price_chf": l.get("price_chf"), "occ30": occ30,
                "reviews": l.get("reviews"), "title": l.get("host_title"),
                "superhost": l.get("superhost"), "in_muni": l.get("in_municipality"),
                "est_month": est_month_chf(l.get("price_chf"), occ30),
            })
            op["markets"].add(mkt)
            htr = l.get("host_total_reviews")
            if htr is not None:
                op["host_total_reviews"] = max(op["host_total_reviews"] or 0, htr)
            op["host_rating"] = op["host_rating"] or l.get("host_rating")
            op["host_title"] = op["host_title"] or l.get("host_title")
            if l.get("superhost"):
                op["superhost"] = True
            for c in (l.get("cohosts") or []):
                cuid = c.get("uid")
                if not cuid:
                    continue
                cuid = str(cuid)
                if cuid == huid:
                    continue
                cn = node(cuid, c.get("name"))
                cn["cohost_on"].append({"lead": huid, "listing": l.get("id"), "market": mkt})
                op["partners"][cuid] = c.get("name")
                edges.append((huid, cuid))

    # Rollen + Ertrag je Operator
    for uid, op in ops.items():
        own = len(op["own"])
        rev = op["host_total_reviews"] or 0
        if own >= 1 and (rev >= 50 or op["host_title"] == "Business" or own >= 3):
            op["role"] = "lead"
        elif own >= 1:
            op["role"] = "host"
        else:
            op["role"] = "assistant"
        op["own_count"] = own
        op["cohost_count"] = len(op["cohost_on"])
        op["est_month_chf"] = sum(o["est_month"] for o in op["own"])
        op["markets"] = sorted(op["markets"])

    # Netzwerke = Connected Components ueber Co-Host-Kanten
    uf = UF()
    for a, b in edges:
        uf.union(a, b)
    comp = defaultdict(list)
    for uid in ops:
        if uid in uf.p:                      # nur Knoten mit mind. einer Kante
            comp[uf.find(uid)].append(uid)

    networks = []
    for root, members in comp.items():
        if len(members) < 2:
            continue
        mem = [ops[u] for u in members]
        # Lead = hoechste Operator-Bewertungszahl unter denen mit eigenen Inseraten, sonst meiste Inserate
        leads = [m for m in mem if m["own_count"] >= 1]
        lead = max(leads or mem, key=lambda m: (m["host_total_reviews"] or 0, m["own_count"]))
        markets = sorted({mk for m in mem for mk in m["markets"]})
        networks.append({
            "id": "net_" + lead["uid"],
            "lead_uid": lead["uid"], "lead_name": lead["name"],
            "n_members": len(mem),
            "total_reviews": sum(m["host_total_reviews"] or 0 for m in mem),
            "own_listings": sum(m["own_count"] for m in mem),
            "markets": markets, "n_markets": len(markets),
            "cross_market": len(markets) >= 2,
            "est_month_chf": sum(m["est_month_chf"] for m in mem),
            "members": sorted(
                [{"uid": m["uid"], "name": m["name"], "role": m["role"],
                  "own_count": m["own_count"], "cohost_count": m["cohost_count"],
                  "host_total_reviews": m["host_total_reviews"],
                  "host_rating": m["host_rating"], "host_title": m["host_title"],
                  "superhost": m["superhost"], "markets": m["markets"],
                  "est_month_chf": m["est_month_chf"]} for m in mem],
                key=lambda x: (0 if x["role"] == "lead" else 1 if x["role"] == "host" else 2,
                               -(x["host_total_reviews"] or 0)),
            ),
        })
        net_id = "net_" + lead["uid"]
        for m in mem:
            m["network_id"] = net_id

    networks.sort(key=lambda n: (-n["total_reviews"], -n["own_listings"]))

    # Operatoren serialisierbar machen (partners dict -> Liste)
    out_ops = {}
    for uid, op in ops.items():
        out_ops[uid] = {
            "uid": uid, "name": op["name"], "role": op["role"],
            "own_count": op["own_count"], "cohost_count": op["cohost_count"],
            "markets": op["markets"], "n_markets": len(op["markets"]),
            "host_total_reviews": op["host_total_reviews"], "host_rating": op["host_rating"],
            "host_title": op["host_title"], "superhost": op["superhost"],
            "est_month_chf": op["est_month_chf"],
            "network_id": op.get("network_id"),
            "partners": [{"uid": k, "name": v} for k, v in op["partners"].items()],
            "own": op["own"],
            "cohost_on": op["cohost_on"],
        }

    p = os.path.join(DATA, "operator-network.json")
    json.dump({
        "_meta": {
            "operators": len(out_ops), "networks": len(networks),
            "note": "Operator-Graph aus Inserat-PDP (host_total_reviews + cohosts). "
                    "Ertrag = Tier MOD (Nachtpreis x Belegung@30 x 30). Lead/Host/Assistant aus Eigen-Inseraten + Bewertungszahl.",
        },
        "networks": networks,
        "operators": out_ops,
    }, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)

    multi = sum(1 for n in networks if n["n_members"] >= 3)
    cross = sum(1 for n in networks if n["cross_market"])
    print(f"Operator-Netzwerk: {len(out_ops)} Operatoren, {len(networks)} Netzwerke "
          f"(>=3 Mitglieder: {multi}, cross-Markt: {cross}) -> {p}")
    for n in networks[:8]:
        roles = "+".join(f"{m['name']}({m['role'][0]})" for m in n["members"][:5])
        print(f"  {n['lead_name']}: {n['n_members']} Mitgl., {n['total_reviews']} Bew., "
              f"{n['own_listings']} Inserate, {n['markets']} — {roles}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
