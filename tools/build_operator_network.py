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


# Kapazitaets-Segmente fuer die Positionierungs-Analyse (CH-Gaestelogik).
CAP_BANDS = [(1, 2, "1–2 Pers."), (3, 4, "3–4 Pers."), (5, 6, "5–6 Pers."), (7, 10, "7–10 Pers."), (11, 99, "11+ Pers.")]


def _band_idx(c):
    for i, (lo, hi, _) in enumerate(CAP_BANDS):
        if lo <= c <= hi:
            return i
    return None


def build_market_coverage(ops, market_pool):
    """Deckt auf, WELCHEN Markt/Welches Segment die Spieler abdecken — und WO Platz ist.
    Pro Markt: wer dominiert (Top-Spieler + Lead-Anteil), und je Kapazitaets-Segment
    Angebot/Belegung/Preis + Status: 'besetzt' (ein Operator haelt >=40%), 'chance'
    (Nachfrage >= Markt-Median aber Angebot duenn <=15% = Positionierungs-Luecke),
    'leer' (kein Angebot), 'normal'. Alles aus den Cockpit-Inseraten, Tier MOD."""
    mb = defaultdict(lambda: defaultdict(int))     # (markt, band) -> uid -> Anzahl
    mkt_op = defaultdict(lambda: defaultdict(int))  # markt -> uid -> Anzahl (Operator-Praesenz)
    for uid, op in ops.items():
        for o in op["own"]:
            m = o.get("market")
            mkt_op[m][uid] += 1
            c = o.get("capacity")
            if c:
                bi = _band_idx(c)
                if bi is not None:
                    mb[(m, bi)][uid] += 1
    out = {}
    for mkt, rows in market_pool.items():
        total = len(rows)
        occ_all = median([r["occ30"] for r in rows if r.get("occ30") is not None])
        bands = []
        for i, (lo, hi, lab) in enumerate(CAP_BANDS):
            sub = [r for r in rows if r.get("cap") and lo <= r["cap"] <= hi]
            n = len(sub)
            occ = median([r["occ30"] for r in sub if r.get("occ30") is not None])
            price = median([r["price"] for r in sub if r.get("price")])
            share = round(100 * n / total) if total else 0
            dom = None
            counts = mb.get((mkt, i))
            if counts:
                duid = max(counts, key=counts.get)
                dc = counts[duid]
                dop = ops.get(duid, {})
                dom = {"uid": duid, "name": dop.get("name"), "count": dc,
                       "share": round(100 * dc / n) if n else 0,
                       "reviews": dop.get("host_total_reviews")}
            if n == 0:
                status = "leer"
            elif dom and dom["share"] >= 40:
                status = "besetzt"
            elif occ is not None and occ_all is not None and occ >= occ_all and share <= 15 and n >= 1:
                status = "chance"
            else:
                status = "normal"
            bands.append({"band": lab, "n": n, "share": share,
                          "occ": round(occ) if occ is not None else None,
                          "price": round(price) if price else None,
                          "dominant": dom, "status": status})
        tp = sorted(mkt_op[mkt].items(), key=lambda kv: (kv[1], ops[kv[0]].get("host_total_reviews") or 0), reverse=True)[:6]
        top = [{"uid": u, "name": ops[u].get("name"), "role": ops[u].get("role"),
                "n_in_market": c, "share": round(100 * c / total) if total else 0,
                "reviews": ops[u].get("host_total_reviews")} for u, c in tp]
        lead_share = round(100 * sum(c for u, c in mkt_op[mkt].items() if ops[u].get("role") == "lead") / total) if total else 0
        out[mkt] = {"market": mkt, "total": total,
                    "occ_median": round(occ_all) if occ_all is not None else None,
                    "n_operators": len(mkt_op[mkt]), "lead_share": lead_share,
                    "n_chances": sum(1 for b in bands if b["status"] == "chance"),
                    "bands": bands, "top_players": top}
    return out


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


# Firmen-/Marken-Erkennung am Namen (Adrian: wer steckt dahinter — Person oder Verwaltung?).
_BRAND_WORDS = ["booking", "apartment", "suite", "hostel", "hospitality", "rental", "stays",
                "lodge", "residence", "residenz", "gmbh", " ag", " sa", "holiday", "ferien",
                "vermiet", "property", "management", "homes", "living", "group", "interhome",
                "immohost", "immo", "rentals", "sharedlock", "secra", "spirit", "blueground",
                "mooi", "smart apartments", "guestready", "alpinekeys", "airhosted", "host", "rooms"]


def classify_operator(name, total_listings, own_count):
    """-> (kind, label). 'brand' = Firmenname; 'pro' = Personenname aber gross (>=20 Inserate);
    'person' = einzeln/klein. Tier: Name 🟢 (gelesen), Schwelle 🟡."""
    nm = (name or "").lower()
    scale = total_listings or own_count or 0
    if any(w in nm for w in _BRAND_WORDS):
        return "brand", "Verwaltungs-Marke"
    if scale >= 20:
        return "pro", "Gross-Operator"
    return "person", "Person / kleines Team"


def operator_sector(pb):
    """Marktsektor-Achse aus dem Playbook (Adrian: 'in welchem Marktsektor sie sich befinden')."""
    if not pb:
        return None
    cap = pb.get("cap_median")
    adr = pb.get("adr_vs_market_pct")
    if cap is None:
        return None
    if cap >= 7:    base = "Gross-Einheiten (Gruppen/Chalets)"
    elif cap >= 5:  base = "Grosse Familien-Einheiten"
    elif cap <= 2:  base = "City-/Business-Apartments"
    else:           base = "Familien-Wohnungen"
    tier = "Premium" if (adr is not None and adr >= 12) else ("Preis/Volumen" if (adr is not None and adr <= -12) else "Mittelklasse")
    return f"{base} · {tier}"


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if n == 0:
        return None
    m = n // 2
    return xs[m] if n % 2 else (xs[m - 1] + xs[m]) / 2.0


def market_medians(pool):
    """pool[market] = [{cap,price,occ30}, ...] -> je Markt Median-Preis/-Belegung gesamt und je Kapazitaet.
    Das ist der Vergleichsmassstab: 'wie schlaegt sich der Operator gegen vergleichbare Inserate im selben Markt'."""
    meds = {}
    for mkt, rows in pool.items():
        by_cap = {}
        caps = sorted({r["cap"] for r in rows if r.get("cap")})
        for c in caps:
            ps = [r["price"] for r in rows if r.get("cap") == c and r.get("price")]
            os_ = [r["occ30"] for r in rows if r.get("cap") == c and r.get("occ30") is not None]
            by_cap[c] = {"price": median(ps), "occ30": median(os_), "n": len(ps)}
        meds[mkt] = {
            "by_cap": by_cap,
            "all_price": median([r["price"] for r in rows if r.get("price")]),
            "all_occ30": median([r["occ30"] for r in rows if r.get("occ30") is not None]),
        }
    return meds


def compute_playbook(op, meds):
    """Dekodiert WIE ein Operator es umgesetzt hat — aus den eigenen Inseraten gegen den Markt.
    Liefert Kennzahlen (Objekt-Fokus, Preis-Posten vs Markt, Belegung, Qualitaet, Skalierung) +
    daraus abgeleitete, belegte Klartext-Saetze ('signals'). Nichts erfunden: jede Zahl aus den
    eigenen Inseraten bzw. dem Markt-Median; Vergleiche sind Tier MOD, Zaehl-Werte Tier OK."""
    units = [o for o in op["own"] if o.get("price_chf")]
    if not units:
        return None
    n = len(units)
    caps = [o["capacity"] for o in units if o.get("capacity")]
    cap_med = median(caps)
    entire_share = round(100 * sum(1 for o in units if o.get("entire")) / n)
    sh_share = round(100 * sum(1 for o in units if o.get("superhost")) / n)
    gf_share = round(100 * sum(1 for o in units if o.get("guest_favorite")) / n)
    ratings = [o["rating"] for o in units if o.get("rating")]
    rating_avg = round(median(ratings), 2) if ratings else None
    years = max([o["years_hosting"] for o in units if o.get("years_hosting")] or [0]) or None
    adr_med = median([o["price_chf"] for o in units])
    occ30_med = median([o["occ30"] for o in units if o.get("occ30") is not None])
    occ90_med = median([o["occ90"] for o in units if o.get("occ90") is not None])

    # Vergleich gegen den Markt — NUR kapazitaets-gematcht mit >=3 Vergleichsobjekten (sonst ehrlich kein
    # Aufschlag-Claim: ein 10-Pers-Luxus-Chalet gegen den Gesamt-Median zu stellen erfindet ein Premium).
    price_ratios, occ_deltas, matched = [], [], 0
    for o in units:
        m = meds.get(o["market"]) or {}
        bc = (m.get("by_cap") or {}).get(o.get("capacity"))
        if not (bc and bc.get("n", 0) >= 3):
            continue
        matched += 1
        if bc.get("price") and o.get("price_chf"):
            price_ratios.append(o["price_chf"] / bc["price"])
        if bc.get("occ30") is not None and o.get("occ30") is not None:
            occ_deltas.append(o["occ30"] - bc["occ30"])
    adr_vs_market = round((median(price_ratios) - 1) * 100) if price_ratios else None   # +% ueber vergleichbaren
    occ_vs_market = round(median(occ_deltas)) if occ_deltas else None                   # +pp ueber vergleichbaren

    team = len(op["partners"])     # Co-Hosts auf den eigenen Inseraten = Assistenten/Partner
    sig = []
    # Objekt-Fokus
    if cap_med is not None:
        cm = round(cap_med)
        if cm >= 6:   sig.append(f"Setzt auf grosse Einheiten (Ø {cm} Pers.) — Gruppen, Familien, Anlaesse.")
        elif cm <= 2: sig.append(f"Kleine Einheiten (Ø {cm} Pers.) — Paare, Geschaeftsreisende, hohe Frequenz.")
        else:         sig.append(f"Mittlere Einheiten (Ø {cm} Pers.) — Familien-Standardgroesse.")
    n_room = sum(1 for o in units if o.get("entire") is False)
    n_ent = sum(1 for o in units if o.get("entire") is True)
    if entire_share == 100 and n >= 2:
        sig.append("Ausschliesslich ganze Wohnungen (kein Zimmer-Sharing).")
    elif n_room and entire_share <= 60:
        sig.append(f"Objekt-Art: Mischung {n_ent} ganze Wohnungen + {n_room} Zimmer — Zimmer-Vermietung ist ein anderes Spiel als R2R.")
    elif n_room:
        sig.append(f"Objekt-Art: überwiegend ganze Wohnungen ({entire_share}%), {n_room} Zimmer dabei.")
    # Preis-Posten
    if adr_vs_market is not None:
        if adr_vs_market >= 12:   sig.append(f"Premium-Preis: ~{adr_vs_market}% ueber vergleichbaren Inseraten im selben Markt.")
        elif adr_vs_market <= -12: sig.append(f"Volumen-Strategie: ~{abs(adr_vs_market)}% unter dem Markt — fuellt ueber den Preis.")
        else:                      sig.append("Marktnah bepreist (kein Auf-/Abschlag).")
    # Belegung + Ehrlichkeit zu Kurzfenster-100%
    if occ30_med is not None:
        s = f"Belegung@30 median {round(occ30_med)}%"
        if occ_vs_market is not None and abs(occ_vs_market) >= 5:
            s += f" ({'+' if occ_vs_market>0 else ''}{occ_vs_market} pp ggü. Markt)"
        if occ90_med is not None:
            s += f", @90 {round(occ90_med)}%"
            if occ30_med >= 85 and occ90_med <= occ30_med - 25:
                s += " — Vorsicht: hohe Kurzfrist-Belegung faellt auf laengere Sicht stark ab"
        sig.append(s + ".")
    # Qualitaet
    q = []
    if sh_share >= 60: q.append(f"Superhost auf {sh_share}% der Inserate")
    if gf_share >= 40: q.append(f"Gaestefavorit auf {gf_share}%")
    if rating_avg:     q.append(f"Ø {rating_avg}★")
    if q: sig.append("Qualitaets-Disziplin: " + ", ".join(q) + ".")
    # Skalierung / Betriebsmodell
    scale = []
    if n >= 2:            scale.append(f"{n} Inserate")
    if len(op["markets"]) >= 2: scale.append(f"{len(op['markets'])} Maerkte")
    if team >= 1:        scale.append(f"Co-Host-Team ({team} {'Person' if team==1 else 'Personen'})")
    if scale: sig.append("Skalierung: " + ", ".join(scale) + ".")
    # Erfahrung
    exp = []
    if years: exp.append(f"{years} Jahre als Gastgeber")
    if op.get("host_total_reviews"): exp.append(f"{op['host_total_reviews']} Operator-Bewertungen")
    if exp: sig.append("Substanz: " + ", ".join(exp) + ".")

    return {
        "n_units": n, "cap_median": round(cap_med) if cap_med is not None else None,
        "entire_count": n_ent, "room_count": n_room,
        "entire_pct": entire_share, "superhost_pct": sh_share, "gf_pct": gf_share,
        "rating_avg": rating_avg, "years_hosting": years,
        "adr_median": round(adr_med) if adr_med else None, "adr_vs_market_pct": adr_vs_market,
        "occ30_median": round(occ30_med) if occ30_med is not None else None,
        "occ90_median": round(occ90_med) if occ90_med is not None else None,
        "occ_vs_market_pp": occ_vs_market, "team": team,
        "signals": sig,
    }


def tier_of(n):
    """Adrian-Stufen nach echtem Gesamt-Portfolio: small 10+ / mittel 50+ / big 200+ / extrem 400+."""
    if n is None:
        return None, None
    if n >= 400: return "extrem", "extrem big · 400+"
    if n >= 200: return "big", "big big · 200+"
    if n >= 50:  return "mittel", "mittel big · 50+"
    if n >= 10:  return "small", "small big · 10+"
    return "unter", "unter 10"


def load_xray():
    """Operator-X-Ray (echte Gesamt-Inseratzahl Airbnb-weit vom Host-Profil), falls vorhanden."""
    p = os.path.join(DATA, "operator-xray.json")
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p, encoding="utf-8")).get("operators", {})
    except Exception:
        return {}


def main():
    ops = {}          # uid -> Knoten
    edges = []        # (lead_uid, cohost_uid)
    xray = load_xray()

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

    market_pool = defaultdict(list)   # market -> alle Inserate (fuer Markt-Mediane = Vergleichsmassstab)

    for f, b in cockpit_files():
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        mkt = (d.get("_meta") or {}).get("market") or b.replace("cockpit-", "").replace(".json", "")
        for l in d.get("listings", []):
            occ = l.get("occ") or {}
            occ30 = occ.get("30")
            # Markt-Pool IMMER fuellen (auch ohne host_uid) — er ist der Vergleichsmassstab.
            market_pool[mkt].append({"cap": l.get("capacity"), "price": l.get("price_chf"), "occ30": occ30})
            huid = l.get("host_uid")
            if not huid:
                continue
            huid = str(huid)
            op = node(huid, l.get("host"))
            op["own"].append({
                "id": l.get("id"), "market": mkt, "url": l.get("url"),
                "price_chf": l.get("price_chf"), "occ30": occ30, "occ90": occ.get("90"), "occ7": occ.get("7"),
                "capacity": l.get("capacity"), "bedrooms": l.get("bedrooms"), "entire": l.get("entire"),
                "rating": l.get("rating"), "guest_favorite": l.get("guest_favorite"),
                "years_hosting": l.get("years_hosting"),
                "lat": l.get("lat"), "lon": l.get("lon"),
                "in_muni_flag": l.get("in_municipality"),
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
        op["entire_count"] = sum(1 for o in op["own"] if o.get("entire") is True)   # ganze Wohnungen (erfasst)
        op["room_count"] = sum(1 for o in op["own"] if o.get("entire") is False)    # Zimmer (erfasst) — anderes Spiel als R2R
        op["est_month_chf"] = sum(o["est_month"] for o in op["own"])
        op["markets"] = sorted(op["markets"])

    # Playbook-Analyse: WIE hat der Operator es umgesetzt (nur fuer die mit eigenen Inseraten)
    meds = market_medians(market_pool)
    for op in ops.values():
        op["playbook"] = compute_playbook(op, meds) if op["own_count"] >= 1 else None

    # Markt-Abdeckung & Positionierungs-Luecken (wer deckt was ab, wo ist Platz)
    market_coverage = build_market_coverage(ops, market_pool)

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
            "entire_listings": sum(m["entire_count"] for m in mem),
            "room_listings": sum(m["room_count"] for m in mem),
            "markets": markets, "n_markets": len(markets),
            "cross_market": len(markets) >= 2,
            "est_month_chf": sum(m["est_month_chf"] for m in mem),
            "members": sorted(
                [{"uid": m["uid"], "name": m["name"], "role": m["role"],
                  "own_count": m["own_count"], "cohost_count": m["cohost_count"],
                  "host_total_reviews": m["host_total_reviews"],
                  "host_rating": m["host_rating"], "host_title": m["host_title"],
                  "superhost": m["superhost"], "markets": m["markets"],
                  "est_month_chf": m["est_month_chf"], "playbook": m.get("playbook"),
                  "entire_count": m["entire_count"], "room_count": m["room_count"],
                  "total_listings": (xray.get(m["uid"]) or {}).get("total_listings")} for m in mem],
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
        _tl = (xray.get(uid) or {}).get("total_listings")
        _kind, _klabel = classify_operator(op["name"], _tl, op["own_count"])
        _sector = operator_sector(op.get("playbook"))
        _tier, _tlabel = tier_of(_tl)
        out_ops[uid] = {
            "uid": uid, "name": op["name"], "role": op["role"],
            "own_count": op["own_count"], "cohost_count": op["cohost_count"],
            "entire_count": op["entire_count"], "room_count": op["room_count"],
            "markets": op["markets"], "n_markets": len(op["markets"]),
            "host_total_reviews": op["host_total_reviews"], "host_rating": op["host_rating"],
            "host_title": op["host_title"], "superhost": op["superhost"],
            "est_month_chf": op["est_month_chf"],
            "network_id": op.get("network_id"),
            "partners": [{"uid": k, "name": v} for k, v in op["partners"].items()],
            "own": op["own"],
            "cohost_on": op["cohost_on"],
            "playbook": op.get("playbook"),
            "total_listings": _tl,   # echtes Airbnb-weites Portfolio (🟢 Host-Profil)
            "tier": _tier, "tier_label": _tlabel,   # small/mittel/big/extrem big (nach Gesamt-Portfolio)
            "kind": _kind, "kind_label": _klabel,   # brand | pro | person — wer dahinter steckt
            "sector": _sector,                      # Marktsektor-Achse
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
        "market_coverage": market_coverage,
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
