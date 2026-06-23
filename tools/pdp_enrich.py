#!/usr/bin/env python3
"""Profi-Radar Stufe 1: reichert Inserate eines Marktes ueber die oeffentliche Inserat-Seite
(PDP, data-deferred-state-0, gleicher Weg wie Kalender) an mit den ECHTEN Feldern, die die
Suchseite nicht hat: Objekttyp (Apartment vs Zimmer!), Superhost, Guest-favorite, Kapazitaet,
PDP-Rating/Reviews. Schreibt zurueck in airbnb-competitors.json (Felder pdp_*).

Adrians Befund: Suchseiten-Entire-Erkennung ist unzuverlaessig (Privatzimmer rutschten durch).
roomType von der PDP ist autoritativ -> nur echte ganze Wohnungen behalten.

Aufruf:  py -3.12 tools/pdp_enrich.py Kriens [--max 60]
"""
import sys, os, re, json, gzip, time, base64, urllib.request, argparse, datetime
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa
import fetch_airbnb_free as ff

PACE_S = 0.8


def uid_num(b64):
    """Numerische User-ID aus base64 'DemandUser:<n>' ODER 'User:<n>' — die zwei Airbnb-Praefixe
    fuer DIESELBE Person (Lead-Host kommt als DemandUser:, Co-Host als User:). Ueber die nackte
    Zahl verknuepfen wir Co-Host und eigenes Inserat zum Operator-Netzwerk."""
    if not b64:
        return None
    try:
        dec = base64.b64decode(str(b64)).decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r":(\d+)", dec)
    return m.group(1) if m else None


def first_key(o, key):
    """Erster Wert zu 'key' (case-insensitive) im verschachtelten Objekt, der kein dict/list ist."""
    kl = key.lower()
    stack = [o]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k.lower() == kl and not isinstance(v, (dict, list)) and v is not None:
                    return v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def first_list(o, key):
    """Erste Liste zu 'key' (case-insensitive) im verschachtelten Objekt."""
    kl = key.lower()
    stack = [o]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k.lower() == kl and isinstance(v, list):
                    return v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def find_dict(o, pred):
    """Erstes dict (DFS), das pred erfuellt — fuer Kontext-gebundene Extraktion."""
    stack = [o]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if pred(cur):
                return cur
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def find_text(o, rx):
    """Erster String-Wert (DFS), auf den die Regex matcht -> Gruppe 1 (oder None)."""
    stack = [o]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            m = rx.search(cur)
            if m:
                return m.group(1)
        elif isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def fetch_pdp(rid):
    req = urllib.request.Request(f"https://www.airbnb.com/rooms/{rid}", headers={
        "User-Agent": ff.UA, "Accept-Language": "en", "Accept": "text/html", "Accept-Encoding": "gzip"})
    try:
        r = urllib.request.urlopen(req, timeout=30); raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        html = raw.decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r'<script id="data-deferred-state-0"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        state = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    rt = first_key(state, "roomType")
    # Superhost ZUVERLAESSIG aus der Host-Karte (PassportCardData) — nicht per first_key (das griff
    # ein True aus Nachbar-Inseraten; 361er-Zimmer kam faelschlich superhost=True). Bonus: Host-Name+ID
    # (= Portfolio-Signal: mehrere Inserate desselben userId = professioneller Mehrfach-Betreiber).
    card = find_dict(state, lambda d: d.get("__typename") == "PassportCardData") or {}
    # Guest-favorite aus dem Quality-Abschnitt (hat isGuestFavorite + guestFavoriteDescription).
    qual = find_dict(state, lambda d: "isGuestFavorite" in d and "guestFavoriteDescription" in d) or {}
    # Tenure: stats-Item type=YEARS_HOSTING -> "8 years of hosting" -> Jahre als int.
    yh = find_dict(state, lambda d: d.get("type") == "YEARS_HOSTING") or {}
    ym = re.search(r"(\d+)", str(yh.get("a11yValue") or yh.get("value") or ""))
    years_hosting = int(ym.group(1)) if ym else None
    # NEUE Hosts (z.B. Kenana) haben KEIN YEARS_HOSTING-Item -> Tenure steht als Text:
    # Host-Karte titleText "Started hosting in 2025" + irgendwo im State "1 year hosting".
    title = str(card.get("titleText") or "")
    sy = re.search(r"[Ss]tarted hosting in (\d{4})", title)
    host_started_year = int(sy.group(1)) if sy else None
    if years_hosting is None:
        th = find_text(state, re.compile(r"(\d+)\s+years?\s+hosting", re.I))
        if th:
            years_hosting = int(th)
        elif host_started_year:
            # "Started hosting in 2025", gescraped 2026 -> 1 Jahr. Floor 1 (kein /0 in vpm),
            # konservativ: ueberschaetzte Tenure unterschaetzt die Velocity -> kein Fehl-Einschluss.
            years_hosting = max(1, datetime.datetime.now().year - host_started_year)
    # CO-HOST-NETZWERK: Operator-Gesamtsignal aus der Host-Karte (ratingCount = ALLE Bewertungen des
    # Betreibers ueber sein ganzes Portfolio, sofort = schaerfstes Profi-Signal ohne 3-Mt-Wartezeit;
    # titleText 'Superhost'/'Business') + die Co-Hosts (Assistenten/Partner) aus dem 'cohosts'-Block.
    cohosts = []
    raw_ch = first_list(state, "cohosts") or []
    for c in raw_ch:
        if isinstance(c, dict) and c.get("name"):
            cohosts.append({"uid": uid_num(c.get("userId")), "name": c.get("name")})
    return {
        "pdp_room_type": rt,                                   # 'Entire home/apt' | 'Private room' | ...
        "pdp_is_entire": (rt is not None and "entire" in str(rt).lower()),
        "pdp_person_capacity": first_key(state, "personCapacity"),
        "pdp_reviews": first_key(state, "reviewCount"),
        "pdp_rating": first_key(state, "starRating"),
        "pdp_is_superhost": bool(card.get("isSuperhost")) if "isSuperhost" in card else None,
        "pdp_guest_favorite": bool(qual.get("isGuestFavorite")) if "isGuestFavorite" in qual else None,
        "pdp_host_name": card.get("name"),
        "pdp_host_id": card.get("userId"),
        "pdp_host_uid": uid_num(card.get("userId")),           # nackte Zahl -> Netzwerk-Verknuepfung
        "pdp_host_total_reviews": card.get("ratingCount"),     # Operator-Gesamt-Bewertungen (z.B. Carmen 686)
        "pdp_host_rating": card.get("ratingAverage"),
        "pdp_host_title": card.get("titleText"),               # 'Superhost' | 'Business' | ...
        "pdp_cohosts": cohosts,                                # [{uid, name}, ...] Assistenten/Partner
        "pdp_years_hosting": years_hosting,
        "pdp_host_started_year": host_started_year,            # neue Hosts: "Started hosting in YYYY"
    }


# Host-Karten-Felder (PassportCardData) fallen GEMEINSAM aus, wenn die Karte transient nicht laedt.
# Dann ist d[host_*]=None -> ein blosses l.update(d) wuerde den letzten GUTEN Host plattmachen
# (genau die "fehlen jetzt mehrere Hosts"-Regression). SELBSTHEILUNG (wie bei occ): einen bekannten
# Host nie mit None ueberschreiben.
HOST_KEYS = ("pdp_host_name", "pdp_host_id", "pdp_host_uid",
             "pdp_host_total_reviews", "pdp_host_rating", "pdp_host_title")


def merge_pdp(l, d):
    for k, v in d.items():
        if k in HOST_KEYS and v is None and l.get(k) is not None:
            continue   # guten Host behalten, transienten Karten-Ausfall ignorieren
        l[k] = v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market")
    ap.add_argument("--max", type=int, default=80)
    a = ap.parse_args()

    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    if a.market not in comp:
        sys.exit(f"{a.market}: keine Scrape-Daten.")
    L = [l for l in comp[a.market]["listings"] if l.get("in_market_radius")][:a.max]
    print(f"{a.market}: PDP-Anreicherung fuer {len(L)} in-radius-Inserate (~{PACE_S}s/Stk) ...")
    ok, entire, rooms, supers = 0, 0, 0, 0
    seen = {}
    for l in L:
        rid = l["id"]
        if rid in seen:                 # Duplikate (Sweep+Liste) nur einmal abrufen
            merge_pdp(l, seen[rid]); continue
        d = fetch_pdp(rid); time.sleep(PACE_S)
        if not d:
            continue
        seen[rid] = d
        merge_pdp(l, d)
        ok += 1
        if d["pdp_is_entire"]: entire += 1
        elif d["pdp_room_type"]: rooms += 1
        if d["pdp_is_superhost"]: supers += 1
    # BOM-frei schreiben (Python utf-8, kein BOM) — PowerShell-Set-Content hatte mal BOM reingebracht.
    with open(fa.OUT_FILE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(comp, fh, ensure_ascii=False, indent=2)
    print(f"  {ok} angereichert · {entire} ganze Wohnungen · {rooms} Zimmer (eigene Kat.) · {supers} Superhosts")


if __name__ == "__main__":
    main()
