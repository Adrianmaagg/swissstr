#!/usr/bin/env python3
"""Inserate aus dem Gmail-Suchagent-Postfach fuers Briefing (via lokalem Heimstatt-Agent).

Holt die per Portal-Suchabo eingegangenen Miet-Inserate (IMAP, ueber den laufenden
Heimstatt-Agent), filtert echte Inserate vom Mail-Rauschen (Aktivierungs-/Bestaetigungsmails)
und haengt pro Inserat eine R2R-Lukrativitaets-Ampel an:
  STR-Markt-Brutto (Median price x occ@30 x 30, kapazitaetsnah) im passenden Cockpit-Markt
  vs. die verlangte Bruttomiete -> Spielraum.

NUR LOKAL: braucht den Heimstatt-Agent (127.0.0.1:8782) bzw. dessen from_mail_<date>.json
(heimstatt liegt neben swissstr). Ohne Gmail-Zugang (Cloud-Lauf) liefert collect() eine leere
Sektion mit Hinweis - das Briefing bleibt valide. Tier: MOD (transparent, Rechenweg in 'method').
"""
import os, json, glob, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
HEIMSTATT_LISTINGS = os.path.normpath(os.path.join(HERE, "..", "..", "heimstatt", "data", "listings"))
AGENT_URL = "http://127.0.0.1:8782"

# Mail-Stadtname -> Cockpit-Markt-id (Dateiname lowercase). Ortsteile auf ihre Gemeinde.
CITY_ALIAS = {
    "emmenbrücke": "emmen", "emmenbruecke": "emmen", "emmenbrucke": "emmen",
    "kuessnacht": "küssnacht am rigi", "küssnacht": "küssnacht am rigi",
    "immensee": "küssnacht am rigi", "mosen": "hitzkirch", "oberwil bei zug": "walchwil",
    "aesch": "aesch lu",
}


def _norm(c):
    return (c or "").strip().lower()


def _trigger_pull(since_days=14, max_msgs=50, timeout=40):
    """Bittet den lokalen Agenten, frische Suchagent-Mails zu ziehen. Best effort."""
    try:
        req = urllib.request.Request(
            AGENT_URL + "/api/find-mails",
            data=json.dumps({"since_days": since_days, "max": max_msgs}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return {"error": str(e)}


def _latest_mail_file():
    files = sorted(glob.glob(os.path.join(HEIMSTATT_LISTINGS, "from_mail_*.json")))
    return files[-1] if files else None


def _is_real(it):
    if not isinstance(it, dict):
        return False
    if (it.get("raw") or {}).get("unparsed"):
        return False
    return bool(_norm(it.get("city")) and (it.get("rent_chf_brutto") or it.get("rent_chf_netto") or it.get("rooms")))


# Eine Miet-WOHNUNG ist als STR keine Gross-Ferieneinheit. Zimmer -> realistische Gaeste-Kapazitaet
# konservativ (Schlafzimmer ~ Zimmer-1.5, Gaeste ~ Zimmer+0.5). Gross-Objekte (Chalets) raus.
MAX_COMPARABLE_CAP = 8


def _persons_from_rooms(rooms):
    try:
        return max(2, round(float(rooms) + 0.5))  # 2.5Zi->3, 3.5->4, 4.5->5, 5.5->6 Gaeste
    except (TypeError, ValueError):
        return None


def _market_str_gross(market_id, persons):
    """Median STR-Brutto/Monat (price x occ@30 x 30) vergleichbarer WOHNUNGEN im Cockpit-Markt.
    Gross-Objekte (cap > 8) raus (keine Mietwohnungs-Entsprechung), kapazitaetsnah (+/-1 Pers),
    Fallback auf alle vergleichbaren Wohnungen wenn der enge Bucket zu duenn ist."""
    p = os.path.join(DATA, f"cockpit-{market_id}.json")
    if not os.path.exists(p):
        return None, 0
    try:
        c = json.load(open(p, encoding="utf-8"))
    except Exception:
        return None, 0
    rows = []
    for l in c.get("listings", []):
        if not l.get("in_municipality"):
            continue
        pr = l.get("price_chf"); occ = (l.get("occ") or {}).get("30"); cap = l.get("capacity")
        if not pr or occ is None or (cap and cap > MAX_COMPARABLE_CAP):
            continue
        rows.append((cap, pr * (occ / 100.0) * 30))
    if not rows:
        return None, 0
    near = [g for cap, g in rows if persons and cap and abs(cap - persons) <= 1]
    pool = sorted(near if len(near) >= 4 else [g for _, g in rows])
    n = len(pool)
    med = pool[n // 2] if n % 2 else (pool[n // 2 - 1] + pool[n // 2]) / 2
    return med, n


def _ampel(str_gross, rent):
    """Brutto-Multiple-Ampel: R2R muss aus dem STR-Brutto die Miete UND die laufenden Kosten
    (Plattform/Reinigung/Moebel-Amortisation/NK/Leerstand, grob ~50% vom Brutto) decken.
    Daumenregel: traegt sich grob ab Brutto ~2x Miete. Bewusst grob (genaue Rechnung = Akquise-Dossier)."""
    if not str_gross or not rent:
        return "grau", "STR-Markt-Ertrag oder Miete unbekannt - im Dossier pruefen."
    ratio = str_gross / rent
    base = f"STR-Markt-Brutto ~CHF {round(str_gross)}/Mt = {ratio:.1f}x Miete CHF {round(rent)}"
    if ratio >= 2.5:
        return "gruen", f"{base}. Klare R2R-Marge (auch nach ~50% Kosten). Im Dossier durchrechnen."
    if ratio >= 1.9:
        return "gelb", f"{base}. Grenzbereich - nach Kosten knapp, genau rechnen."
    return "rot", f"{base}. Brutto deckt Miete+Kosten kaum - vermutlich nicht tragfaehig."


def collect(since_days=14):
    """Sektion fuers Briefing. Loest best-effort einen frischen Mail-Pull aus, liest dann die
    neueste from_mail-Datei. Gibt available=False zurueck, wenn kein Gmail-Zugang da ist."""
    pull = _trigger_pull(since_days=since_days)
    f = _latest_mail_file()
    if not f:
        return {"available": False, "count": 0, "listings": [],
                "reason": "Kein Gmail-Zugang / keine from_mail-Datei - die Postfach-Sektion fuellt sich "
                          "nur beim lokalen Lauf mit laufendem Heimstatt-Agent.",
                "pull": pull}
    try:
        raw = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        return {"available": False, "count": 0, "listings": [], "reason": f"from_mail unlesbar: {e}"}
    items = raw.get("listings", raw if isinstance(raw, list) else [])
    real = [it for it in items if _is_real(it)]
    out = []
    for it in real:
        mid = CITY_ALIAS.get(_norm(it.get("city")), _norm(it.get("city")))
        persons = _persons_from_rooms(it.get("rooms"))
        rent = it.get("rent_chf_brutto") or it.get("rent_chf_netto")
        sg, n = _market_str_gross(mid, persons)
        amp, note = _ampel(sg, rent)
        in_cockpit = os.path.exists(os.path.join(DATA, f"cockpit-{mid}.json"))
        out.append({
            "city": it.get("city"), "market_id": mid if in_cockpit else None,
            "rooms": it.get("rooms"), "sqm": it.get("sqm"),
            "rent_brutto": it.get("rent_chf_brutto"), "rent_netto": it.get("rent_chf_netto"),
            "title": it.get("title"), "url": it.get("url"), "platform": it.get("platform"),
            "available_from": it.get("available_from"), "first_seen": it.get("first_seen_at"),
            "landlord": it.get("landlord_name") or it.get("landlord_company"),
            "str_market_gross": round(sg) if sg else None, "str_basis_n": n,
            "ampel": amp, "note": note,
        })
    order = {"gruen": 0, "gelb": 1, "grau": 2, "rot": 3}
    out.sort(key=lambda x: (order.get(x["ampel"], 9), -(x["str_market_gross"] or 0)))
    return {"available": True, "source": os.path.basename(f), "count": len(out),
            "noise_filtered": len(items) - len(real), "listings": out,
            "method": ("MOD - Inserate aus dem Gmail-Suchagent-Postfach (IMAP, lokal ueber Heimstatt-Agent). "
                       "Lukrativitaets-Ampel = grobe R2R-Vorsortierung: Median STR-BRUTTO vergleichbarer "
                       "Wohnungen (price x occ@30 x 30, kapazitaetsnah +/-1 Pers, Gross-Objekte cap>8 raus) "
                       "im passenden Cockpit-Markt geteilt durch verlangte Bruttomiete. Brutto muss Miete UND "
                       "~50% Kosten decken -> >=2.5x gruen, >=1.9x gelb, <1.9x rot. Brutto-Obergrenze, keine "
                       "Netto-Rechnung - die genaue Tragfaehigkeit steht im Akquise-Dossier (economics.js). "
                       "Aktivierungs-/Bestaetigungsmails (unparsed) herausgefiltert.")}


if __name__ == "__main__":
    r = collect()
    print(json.dumps({k: v for k, v in r.items() if k != "listings"}, ensure_ascii=False, indent=2))
    for l in r.get("listings", [])[:12]:
        print(f"  [{l['ampel']:5}] {l['city']:14} {l['rooms']}Zi  CHF {l['rent_brutto']}  - {l['note']}")
