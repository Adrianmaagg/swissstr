#!/usr/bin/env python3
"""Echte Auslastung 'wie Adrian schaut': echtes Datum + echte Aufenthaltsdauer ->
was ist BUCHBAR (nur ganze Wohnungen, Mindestnaechte beachtet). Plus Buchungs-Kurve
ueber mehrere Check-in-Vorlaufzeiten = wie weit im Voraus der Markt bucht.

Der 6-Monats-Kalenderdurchschnitt UNTERSCHAETZT die Ist-Auslastung (ferne Monate noch
ungebucht = Vorlaufzeit). Diese hier ist die ehrliche Nachfrage-Staerke fuer einen Termin.

Aufruf:  py -3.12 tools/availnow.py Kriens                 (Buchungs-Kurve)
         py -3.12 tools/availnow.py Kriens --in 1 --nights 3   (ein Termin)
"""
import sys, os, json, urllib.parse, urllib.request, gzip, datetime, argparse
sys.path.insert(0, os.path.dirname(__file__))
import fetch_airbnb as fa
import fetch_airbnb_free as ff


def cal_days(listing_id):
    now = datetime.datetime.now(datetime.timezone.utc)
    variables = {"request": {"count": 5, "listingId": str(listing_id), "month": now.month, "year": now.year}}
    ext = {"persistedQuery": {"version": 1, "sha256Hash": ff.CAL_SHA}}
    qs = urllib.parse.urlencode({"operationName": "PdpAvailabilityCalendar", "locale": "en",
        "currency": "CHF", "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps(ext, separators=(",", ":"))})
    url = f"https://www.airbnb.com/api/v3/PdpAvailabilityCalendar/{ff.CAL_SHA}?{qs}"
    req = urllib.request.Request(url, headers={"X-Airbnb-API-Key": ff.AIRBNB_PUBLIC_KEY,
        "User-Agent": ff.UA, "Accept": "application/json", "Accept-Encoding": "gzip"})
    try:
        r = urllib.request.urlopen(req, timeout=25); raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
        data = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        return None
    months = ff._dig(data, "data", "merlin", "pdpAvailabilityCalendar", "calendarMonths") or []
    out = {}
    for m in months:
        for d in (m.get("days") or []):
            dt = d.get("calendarDate")
            if dt:
                out[dt] = {"avail": bool(d.get("available")),
                           "checkin_ok": bool(d.get("availableForCheckin")),
                           "minN": d.get("minNights")}
    return out


def bookable_count(cals, checkin_offset, nights):
    """Wie viele Inserate sind fuer Check-in heute+offset, N Naechte, buchbar."""
    ci = datetime.date.today() + datetime.timedelta(days=checkin_offset)
    want = [(ci + datetime.timedelta(days=i)).isoformat() for i in range(nights)]
    total, book, minblock = 0, 0, 0
    for cal in cals:
        if cal is None:
            continue
        total += 1
        if not all(cal.get(d, {}).get("avail") for d in want):
            continue
        if not cal.get(want[0], {}).get("checkin_ok", True):
            continue
        if (cal.get(want[0], {}).get("minN") or 1) > nights:
            minblock += 1; continue
        book += 1
    return total, book, minblock


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market")
    ap.add_argument("--nights", type=int, default=3)
    ap.add_argument("--in", dest="offset", type=int, default=None, help="Tage bis Check-in (ein Termin)")
    a = ap.parse_args()

    comp = json.load(open(fa.OUT_FILE, encoding="utf-8"))
    if a.market not in comp:
        sys.exit(f"{a.market}: keine Scrape-Daten.")
    L = [l for l in comp[a.market]["listings"]
         if l.get("in_market_radius") and l.get("is_entire") is True]
    print(f"{a.market} — ganze Wohnungen im Kreis, {a.nights} Naechte. Lade Kalender ({len(L)}) ...")
    cals = []
    for l in L:
        cals.append(cal_days(l["id"])); ff.time.sleep(0.55)

    offsets = [a.offset] if a.offset is not None else [1, 14, 30, 60, 90]
    print(f"\n  {'Check-in in':<14}{'Pool':>5}{'buchbar':>9}{'Auslastung':>12}")
    for off in offsets:
        total, book, minblock = bookable_count(cals, off, a.nights)
        occ = round((1 - book / total) * 100) if total else 0
        when = "morgen" if off == 1 else f"+{off} Tage"
        bar = "#" * (occ // 5)
        print(f"  {when:<14}{total:>5}{book:>9}{occ:>10}%  {bar}")
    print("\n  Auslastung JETZT (kurzfristig) = ehrliche Nachfrage-Staerke; faellt nach hinten = Vorlaufzeit.")


if __name__ == "__main__":
    main()
