# SwissSTR — Continuation-Prompt (Stand v0.9.79 · 2026-06-07)

> Copy-paste alles ab `--- BEGIN ---` in einen neuen Chat.

--- BEGIN ---

# KONTEXT
Adrian (CH, kein Dev, iPhone/Windows, 7 J. Airbnb-Superhost). Ziel: **Rent-to-Rent (R2R)** —
Wohnungen langfristig mieten, moebliert kurzzeit weitervermieten. **SwissSTR** =
`C:\Users\adria\Claude\swissstr` (github `Adrianmaagg/swissstr`, **jetzt PRIVAT** -> lokal via
`swissstr.cmd`, `http://127.0.0.1:8766/index.html`). Single-File `index.html` (~7900 Z, Anzeige-Layer,
kein Build) + `tools/*.py` + `data/*.json`. `marketEconomics` = EINZIGE Rechen-Engine. Daten-Tier
🟢BFS/🟡MOD/🔴MOCK an jedem Wert. **CLAUDE.md + Memory beachten:** durchziehen ohne Mikro-Rueckfragen,
commit+push `main`, de-CH (kein ß), Browser-Verify vor Commit, Commit `vX.Y.Z — …`.

**WICHTIG — Agent nutzen:** Es gibt den Subagenten **`swissstr-architekt`** (`~/.claude/agents/`).
Vor groesseren Schritten/Commits als Gegen-Check einsetzen: Praemissen-Check zuerst, Pyramide/MECE,
kuratieren statt anhaeufen, R2R-Brille, KEINE erfundenen Werte/Scores, "Tests gruen != real gesehen".

# WAS LAEUFT (diese Session gebaut)
- **Oekonomie echt:** Nacht-Preis -> ADR/RevPAR; echte Airbnb-ADR ins Markt-Detail **kalibriert**
  (BFS-Saisonform x echtes Niveau); STR/Hotel entmischt (Zimmer/Superhost = "STR, nicht Hotel").
- **Perlen-Radar (R2R)** im STR-Radar: 4 Chancen-Komponenten je 0–25 (Nachfrage=Auslastung ·
  Luecke=knappes aber gebuchtes guests-Segment · Ertrag=RevPAR · Konkurrenz=wenig Profi) = Basis,
  x R2R-Spread-Tor (Resort 0.35/duenn 0.5/ok 0.9/stark 1.0). Transparent (jede Punktzahl offen).
- **Daten-Quellen 2-gleisig:**
  - **BD-Pfad (bezahlt, scharf):** `fetch_airbnb.py --fetch` (URL-Liste, Fokus-5 taeglich 06:00)
    + `--discover "<Ort>"` (Standort -> ~100 Inserate inkl. **Kalender/available_dates** = echte Auslastung)
    + `--aggregate` + `--reviews`. -> Kalender-Belegung = SOTA "Booking Pace".
  - **GRATIS-Pfad (neu):** `fetch_airbnb_free.py "<Ort>, Switzerland" --market <Ort>` — parst Airbnb-
    Suchseite (`data-deferred-state-0`), holt **Listings + Preis + Rating + Groesse OHNE BD/Proxy/Block**.
    Auslastung = Review-Velocity-Proxy (gröber 🟡), Kapazitaet aus Zimmern geschaetzt. Speist Zeitreihe
    -> aggregate -> Perlen-Radar. Bisher gescannt: Zug/Luzern/Zuerich/Cham/Zofingen/Olten/Schwyz/Stans.
- **Akquise (in STR, Tab "Akquise"):** gespeist vom **lokalen Heimstatt-Agenten** (`C:\Users\adria\Claude\
  heimstatt`, Cockpit-API `127.0.0.1:8782`, CORS). Inserate finden (Link-Check · IMAP-Suchagent) ->
  R2R-Score -> Anschreiben (5 Varianten, Mock gratis / echter Claude per Key) -> Anbieter-CRM/Verzeichnis ->
  Outbox. **Verwaltungssuche** via BD-Web-Suche. **Loop einmal real geschlossen** (Test-Mail an
  adrian.maag@hotmail.com, SMTP 250). **IMAP angeschlossen** (strhometo@gmail.com App-Passwort in
  `heimstatt/.env`, gitignored; Suchabo Emmen/Emmenbrueck aktiv; py3.7-IMAP-Bug gefixt).

# BRIGHT-DATA-KONTO (Geld!)
$31.66 Test-Guthaben (30 Tage), darin **4'522 Scraper-Records** + ~21'000 Web-Suchen. Keine
Zahlungsmethode -> **pausiert wenn leer, keine Ueberraschungs-Rechnung.** Strategie (Adrian bestaetigt):
**Breite GRATIS (free-Scraper), Tiefe gezielt BD** (scharfer Kalender nur fuer die Gewinner). Gratis-Tier
(5'000/Mt) deckt nur Web-Suche/Markdown, NICHT die strukturierten Airbnb-Kalenderdaten.

# OFFENES FEEDBACK VON ADRIAN (PRIORITAET — beim naechsten Schritt umsetzen)
1. **Nur GESAMTE Unterkunft.** Rooms/Shared rausfiltern (R2R = ganze Wohnung). Im `fetch_airbnb_free.py`
   (room_type-Filter auf entire home/apt) UND in der Anzeige. Aendert Signale spuerbar.
2. **Perlen-Radar entruempeln (Progressive Disclosure).** Heute zu ueberladen. Pro Markt nur **EINE
   Klartext-Zeile + Score**; volle Komponenten-Rechnung erst auf Klick.
3. **Actionability — der Kern.** Das Tool muss **WO + WAS** konkret sagen, nicht nur Score. Die **Luecke
   IST die Antwort** -> als Satz: *"Kriens — hol dir eine 3–4-Personen-Wohnung (ganze Einheit): nur 3 im
   Markt, 79% gebucht."* Mit Punkt 1 wird "was" praezise (Zimmer/Personen entire).
4. **Stichprobe der Fokus-5 ist nur ~10** (hardcoded URL-Liste) = zu klein/unrepraesentativ. Verbreitern
   (Discovery ~100) ODER Fokus auf Gratis-Scan (~40+).
5. **Trends/Buchungs-Dynamik + ADR/RevPAR-Bloecke sind GUT** — Adrian einig, behalten.

# META-STRUKTUR (das "Aussen", weiter offen)
Roter Faden fehlt: 3 Tabs beantworten dasselbe "WO" (Marktuebersicht + STR-Radar + Scout = nicht MECE);
Markt-Detail = Gemischtwarenladen. Ziel: **1 Kernaussage -> 3 MECE-Themen (WO lohnt's / WAS springt raus /
WIE holst du's) -> Tiefe**, Daten = Fundament (kein Tab). Answer-First + Progressive Disclosure.

# ERSTE AUFGABE
Im `swissstr-architekt`-Modus: Feedback-Punkt 1+3 zuerst (Gesamt-Unterkunft-Filter + actionable
Perlen-Satz) — das macht den groessten Sprung von "Score" zu "wo + was investiere ich". Dann 2 (entruempeln).

# OPS
- PowerShell-Skripte ASCII-only. "Claude Cowork"-Ordner nicht umbenennen. Preview swissstr-verify Port 8766,
  Heimstatt-Agent 8782 (`heimstatt/agent/cockpit.cmd`). `node --check`/`py_compile` vor Commit.
- BD-Token in `swissstr/.env`, IMAP/SMTP in `heimstatt/.env` (beide gitignored).
