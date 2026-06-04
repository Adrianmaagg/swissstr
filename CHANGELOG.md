# Changelog

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.
Format: [Semantic Versioning](https://semver.org/lang/de/).

## [0.9.37] — 2026-06-04

### Geändert — Wohnort frei eingebbar + Performance-Filter erklärt

Adrian: "hier sollte ich doch mein Einzugsgebiet eingeben können, also dass ich vom Dorf X
komme ... und für was steht hier Mittel Hoch und Tief."

- **Wohnort als Tippfeld mit Autocomplete** statt fixem 25-Städte-Dropdown: tippe deinen
  echten Wohnort (z.B. Baar). Liste = alle Märkte + CH-Gemeinden aus `communes.json`.
  Koordinaten werden zur Laufzeit aufgelöst + in MARKET_COORDS injiziert → Fahrzeit rechnet
  von DEINEM Ort. ✓/✗-Hinweis ob erkannt. Re-rendert Karte, Ranking, „Markt im Fokus".
- **Hoch/Mittel/Tief erklärt:** statt „Tertile des gewählten Metrics" jetzt Klartext —
  Hoch = bestes Drittel, Mittel = mittleres, Tief = unterstes Drittel der gewählten Kennzahl.

### Behoben
- TDZ-Bug: `let COMMUNES` war nach dem Wohnort-IIFE deklariert → `typeof COMMUNES` warf
  ReferenceError und brach den Rest des Scripts ab (Featured-Card hing auf „Lade Daten").
  COMMUNES früh deklariert.

### Hinweis
- Autocomplete deckt aktuell Märkte + 93 Schlüssel-Gemeinden (Bootstrap, inkl. Baar &
  Greenlist). Volle ~2'100-Gemeinden-Abdeckung sobald `fetch_communes.py` durchläuft
  (Wikidata war beim Bau rate-limitet; Monats-Action holt es nach).

## [0.9.36] — 2026-06-04

### Hinzugefügt — „Markt im Fokus" zurück, aber echt + für den User optimiert

Adrian: "es muss nicht raus, aber die Frage ist ob es besser geht, optimiert einfach für den User."

Statt der gelöschten fake-statischen Andermatt-Karte jetzt eine **dynamische, umsetzbare**
Empfehlung:
- Pickt den besten Markt nach geschätztem Cashflow (RevPAR × Auslastung), aber **nur
  regulatorisch saubere** (kein REGULATORY_STOP, kein ZWG-Cap) — kein Supply-Lock-Resort mehr.
- **Personalisiert:** wenn Einzugsgebiet gesetzt → nur erreichbare Märkte, Label „erreichbar ab X".
- Transparente Begründung („Warum: regulatorisch sauber · erreichbar in Xh · Verhandlungs-Hebel").
- Klartext-Labels (RevPAR = Umsatz/verfügb. Nacht, Auslastung = belegte Nächte %), Cashflow als
  🟡 MOD getiert, Auslastung 🟢 BFS. Re-rendert bei Einzugsgebiet-Änderung.
- Unterscheidet sich bewusst vom Hero „Bester Cashflow-Markt" (national, inkl. Resorts):
  diese Karte zeigt den, den man **wirklich umsetzen** kann.

Verifiziert via Preview: pickt Interlaken (A, CHF 54k, sauber) statt Andermatt; Scope wechselt
auf „erreichbar ab Baar" bei gesetztem Einzugsgebiet; keine Konsolenfehler.

## [0.9.35] — 2026-06-04

### Entfernt/Korrigiert — Fake-dynamische Dashboard-Karten + A/B/C/D-Klarheit

Adrian: "wann soll er sich zurücksetzen, es benötigt eine Logik ... Wo Sommer schlägt
Winter zu statisch und Diese Woche im Fokus das selbe und es ist nicht einmal ein guter
Tipp, wenn nicht besser möglich streichen ... was A,B,C,D ist auch nicht klar."

- **„TOP-CASHFLOW HEUTE" → „Bester Cashflow-Markt":** „HEUTE" war irreführend (ändert sich
  nicht täglich). Jetzt mit klarer Logik: höchster geschätzter Jahres-Cashflow aller Märkte,
  aktualisiert mit dem BFS-Daten-Refresh (monatlich). Wert war schon berechnet (Gstaad CHF 61k).
- **„Diese Woche im Fokus" (Andermatt) GESTRICHEN:** komplett hartcodiert, behauptete
  „Wöchentlich", empfahl ausgerechnet einen Supply-Lock-Resort (steht nebendran als Cap-Risiko).
  Redundant zum echten Edge-Ranking → entfernt, Karten-Grid auf 2 Spalten.
- **Saisonalitäts-Chart ehrlich gekennzeichnet:** war scheingenaue CHF-Kurven → jetzt klar als
  „Muster, kein Live-Wert" (typischer Saison-Verlauf der Profil-Typen); echte BFS-Werte im Markt-Detail.
- **A/B/C/D-Grade erklärt:** Legende direkt in der Filter-Leiste — was die Note heisst
  (A Top-Performance … D schwach, aus RevPAR + Nachfrage) UND warum man differenziert
  (A = teuer & reguliert, C/D = günstiger Einstieg, mehr Risiko).

Verifiziert via Preview: alle vier umgesetzt, Top-Cashflow dynamisch befüllt, keine Konsolenfehler.

## [0.9.34] — 2026-06-04

### Geändert — Edge-Score transparent (kein Blackbox-Wert mehr, §12)

Adrian: "was soll das 24 bedeuten ganz rechts? Das muss klar sein, ergibt sich aus Punkt a, b, c."

Die nackte Zahl war eine Blackbox. Jetzt zeigt jede Zeile die **Zusammensetzung**:
- Pro Markt unter dem Score: `Nachfrage +20 · Hebel +4 · Optimismus −X` → die Summe = der Score.
- Mini-Kopfzeile beschriftet die rechte Spalte: „Edge-Score = Nachfrage + Hebel − Optimismus".
- Fussnote ausgeschrieben: Nachfrage (BFS-Logiernächte-Wachstum YoY, ±20), Hebel
  (Leerstand ≥1.5% = +4 / ≤0.5% = −3), Optimismus (Abzug bei zu hoher modellierter Auslastung).
  Beispiel „24 = Nachfrage +20 + Hebel +4" direkt dabei.

Verifiziert: Rheinfelden zeigt 24 mit „Nachfrage +20 Hebel +4", keine Konsolenfehler.

## [0.9.33] — 2026-06-04

### Behoben — Investor-Calc P&L-Wasserfall verschwand

Adrian: "Der Wasserfall verschwindet komplett." Ursache: Chart.js mit
`maintainAspectRatio:false` ohne fixe Parent-Höhe → Canvas wuchs auf ~1680 px und
zerschoss das Layout (timing-abhängig). Fix: Canvas in Container mit fixer Höhe (260 px).
Verifiziert: Canvas stabil 260 px nach Navigation + Slider-Update, keine Konsolenfehler.

### Geändert — Ranking-Tabelle: alle Märkte, mehr Sortierungen, Klartext-Labels

Adrian: "jede Schweizer Stadt soll dabei sein ... filtern nach RevPAR, ADR und OCC ...
Abkürzungen dürfen da sein aber man soll direkt sehen von was man redet."

- **Alle 197 Märkte** statt Top-10 (scrollbarer Container 560 px, sticky Header).
- **Sortier-Toggle erweitert:** RevPAR · ADR · Auslastung · Notfall-Score (vorher nur RevPAR + Notfall).
- **Klartext unter jeder Spalte:** RevPAR → „Umsatz/verfügb. Nacht", ADR → „Ø Preis/Nacht",
  Auslastung → „belegte Nächte %", Note → „A–F gesamt". Titel zeigt Metrik ausgeschrieben + Anzahl.

## [0.9.32] — 2026-06-04

### Korrigiert — Reinigungskosten: Aufenthaltsdauer treibt Anzahl Wechsel

Adrian: "bei der Reinigung der Berechnung die stimmt definitiv nicht ... wenn man jeden
3 Tg jemand neues hat macht das x ... sie ist zu tief."

Der Fehler: fixer „4-Nächte-Schnitt" → zu wenige Reinigungen. Bei Ø 3 Nächten sind es
~85/Jahr (statt ~64), bei Ø 2 → ~128. Plus: das Modell tat so, als decke die Gast-Putzgebühr
die Kosten immer 1:1 (Netto null) — versteckt den realen Drag bei vielen Wechseln.

- **Neuer Slider „Ø Aufenthaltsdauer (Nächte)"** in der Custom-Earn-Card → treibt
  `Reinigungen = belegte Nächte ÷ Ø-Aufenthalt`. Default 3 (STR-realistisch statt 4).
- **Reinigungen/Jahr sichtbar** + **Putz-Netto** (kassierte Gebühr − echte Putzkosten);
  zeigt rot „du zahlst drauf", sobald die echte Putzkraft mehr kostet als der Gast zahlt.
- Putzkraft-Slider max 200 → **250** (CH-Reinigung inkl. Wäsche realistisch höher).
- Die 3 fixen Szenarien ebenfalls von 4 → 3 Nächte (waren zu optimistisch).
- Fließt automatisch in Cashflow, CoC und Break-even.

### Verifiziert
Preview: Slider treibt Count (Ø2→128, Ø3→85, Ø7→37); bei Putzkraft 180 > Gast-Gebühr 110
fällt Cashflow Zermatt von 34'163 auf 24'541 (Putz-Netto −8'960). Keine Konsolenfehler.

## [0.9.31] — 2026-06-04

### Hinzugefügt — Edge-Ranking + Backtest-Kalibrierung + Leerstand-Pipeline

Drei zusammenhängende Bausteine: Cross-Markt-Sicht des Anomalie-Detektors, ein echter
Phase-5-Backtest und die dritte Daten-Pipeline (Leerstand, doch via SDMX gelöst).

- **`tools/fetch_leerstand.py`** (SDMX gelöst): BFS-Leerwohnungsziffer pro Gemeinde via
  `disseminate.stats.swiss/rest` (Dataflow CH1.LWZ:DF_LWZ_1), gefilterte Slice statt 767-MB-
  Volldump (~530 KB, ~2 s). `data/leerstand.json` (2025): 2'292 Gemeinden. Stdlib-CSV, keine Deps.
- **Frontend:** `loadHesta` hängt `m.leerstand` (%) via BFS-Nummer an. Neuer Anomalie-Befund
  **Mietverhandlungs-Hebel** (Proxy §9): Leerstand ≥1.5 % = Spielraum (Chance), ≤0.5 % =
  angespannt (Risiko) — beide mit Gegen-Check.
- **Cross-Markt Edge-Ranking** (Scout-View): scannt alle BFS-Märkte, sortiert nach transparentem
  Edge-Score (reales Momentum + Hebel − Optimismus-Gap), regulatorisch gekappte ausgeschlossen,
  klickbar → Markt-Detail. Das „Aha" über alle Märkte auf einen Blick.
- **Backtest / Signal-Kalibrierung (Phase 5):** testet das Momentum-Signal retrospektiv
  (Vorjahres-YoY → realisiert Q1-2026 vs Q1-2025, rein reale BFS-Daten). **Ergebnis ehrlich:
  51 % Trefferquote (n=140) → das Signal ist kaum besser als Zufall, und die UI sagt das auch.**
  Macht die unmessbare Signal-Güte erstmals messbar (Kern von Phase 5).
- **`refresh-data.yml`**: `fetch_leerstand.py` im monatlichen Refresh (fallback-sicher).

### Hinweis

- Verifiziert via Pipeline-Run + Preview: Leerstand 2'292 Gemeinden (Zermatt 0.59 %,
  Solothurn 1.24 %, Zürich 0.10 %), Ranking 12 Märkte klickbar, Kalibrierung 51 % gerendert,
  keine Konsolenfehler.
- Die ehrliche 51 %-Kalibrierung bestätigt: Momentum ist ein schwaches Signal — der Edge-Score
  bleibt qualitativ zu lesen, kein Franken-Versprechen. Kein Confidence-Inflation.

## [0.9.30] — 2026-06-04

### Hinzugefügt — Phase 2: Anomalie-Detektor (Modell vs. Realität, MVP)

Der erste „Insight-Engine"-Baustein, der reale BFS-Signale gegen das modellierte STR-Modell
stellt. **Diagnostisch (Ist-Zustand), keine Prognose** — Edge-Kandidaten, keine Wahrheiten.

- **`detectAnomalies(m)`** prüft pro Markt vier Divergenzen, jede mit Tier + Konfidenz +
  adversarialem Gegen-Check:
  1. **Optimismus-Gap** — modellierte STR-Occ vs. reale BFS-Hotel-Occ (≥15 pp = Warnung).
  2. **Nachfrage-Momentum** — reale HESTA-Logiernächte YoY 2024→2025 (🟢 BFS, ±5 %).
  3. **Arbitrage-Spanne** — modelliertes STR-Brutto vs. Kanton-Kaltmiete (🔴 MOCK, LOW Konf.).
  4. **Regulierungs-Gate** — ZWG-Cap / REGULATORY_STOPS kappt jede Chance.
- **Verdikt §16-konform:** Grün NUR bei realem Nachfrage-Rückenwind ohne Regulierungs-Cap;
  hohe Chance + tiefe Konfidenz wird nie grün. Panel im Markt-Detail unter dem Liveness-Warner.
- Methoden-Fussnote macht den Daten-Mix (MOCK vs. BFS) transparent.

### Verifiziert
- Über alle Markttypen: Zermatt/Davos ⚖️ (Arbitrage + reg-limitiert), Winterthur 🟡
  (Optimismus-Gap), Basel/Neuchâtel/Fribourg/Chur 🟢 (Nachfrage-Rückenwind). 28 grüne
  Verdikte, 85 Momentum-Befunde, keine Konsolenfehler.

### Verschoben — BFS-Leerstand-Pipeline (bewusst NICHT gebaut)

Die BFS-Leerwohnungsdaten (Gemeinde-Ebene) sind auf die neue SDMX-Plattform stats.swiss
(`DF_LWZ_1`) migriert; der Daten-Endpoint liess sich nicht zuverlässig auflösen. Eine geratene/
fragile Pipeline würde gegen die Pipeline-Regel (reproduzierbar, keine ungeprüften Deps)
verstossen — daher transparent verschoben statt halbfertig geliefert.

## [0.9.29] — 2026-06-04

### Hinzugefügt — BFS-Mietpreis-Pipeline: Kaltmiete-Reality-Anchor am Miet-Input

Zweite A/B-Pipeline. Macht die Miet-Seite der Arbitrage-Rechnung datenfest und füllt die
Reality-Check-Lücke (§14): ADR & Auslastung hatten Markt-Benchmarks, der Mietzins bisher nicht.

- **`tools/fetch_mietpreise.py`**: holt „Durchschnittlicher Mietpreis nach Zimmerzahl und
  Kanton" (BFS-Asset je-d-09.03.03.01) via dam-api.bfs.admin.ch, parst die XLSX (neuestes
  Jahr-Sheet), schreibt `data/mietpreise.json`. Stdlib + openpyxl, fallback-sicher, Sanity-Checks.
- **`data/mietpreise.json`** (Jahr 2024): 26 Kantone × Zimmerzahl 1–5, Netto-Kaltmiete CHF/Mt.
- **Frontend:** `loadHesta` lädt die Mietpreise; `computeRentBenchmark` interpoliert pro
  Wohnungsgröße (z.B. 3.5Z = Ø rooms 3+4); unter dem Miet-Input erscheint der **BFS-Kaltmiete-
  Anchor** (🟡 MOD) mit Abweichungs-Ampel (>30 % gelb, >50 % rot, §14).
- **Ehrlich gekennzeichnet:** Es ist ein KANTONS-Durchschnitt — Resort-/City-Mikrolagen
  weichen stark ab (z.B. Zermatt 2'200 = +62 % ggü. VS-Schnitt 1'360). Der Inline-Hinweis
  „Kantons-Ø — Resort/City weicht ab" steht direkt dabei; ersetzt NICHT die Default-Miete.
- **`refresh-data.yml`**: `fetch_mietpreise.py` im monatlichen Refresh (fallback-sicher).

### Hinweis

- `computeDefaultRent` (revpar-basiert) bewusst unverändert — der Benchmark ist additiv,
  damit der Resort-Premium im Default erhalten bleibt.
- Verifiziert via Pipeline-Run + Preview: 26 Kantone, Benchmark rendert, Ampel korrekt
  (Zermatt +62 % rot, Winterthur +1 % grün, Bern ohne Miete = nur Info), keine Konsolenfehler.

## [0.9.28] — 2026-06-04

### Hinzugefügt — Roadmap B: ARE-Zweitwohnungen-Pipeline (ZWG-Cap-Layer)

Erste neue Daten-Pipeline seit den Bootstrap-Quellen — bringt regulatorische Realität
(Zweitwohnungsgesetz) als echtes Signal pro Markt ins Tool.

- **`tools/fetch_zweitwohnungen.py`**: holt das ARE-Wohnungsinventar (Layer
  `ch.are.wohnungsinventar-zweitwohnungsanteil`) via geo.admin.ch STAC-API, parst die
  offizielle XLSX-Tabelle, schreibt `data/zweitwohnungen.json`. Stdlib + openpyxl,
  fallback-sicher, Sanity-Checks, `_health.json`-Update.
- **`data/zweitwohnungen.json`** (Release 2026-03): 2'110 Gemeinden, **331 mit
  Zweitwohnungsanteil ≥20%**, **326 offiziell restricted** (ARE-Status). Beide Zahlen
  bewusst dokumentiert — die Abweichung (Sonderverfahren) wird NICHT geglättet.
- **Frontend:** `loadHesta` hängt `m.zwg` (pct, restricted) via BFS-Gemeindenummer an;
  `assessSTRLiveness` zeigt bei restricted-Gemeinden ein **ZWG-Cap-Signal** (🟡 medium):
  präzise als Proxy für regulatorische Sensibilität — kein direktes Verbot für
  Rent-to-Rent von Bestandswohnungen, aber Sensibilitäts- + Zusatzregel-Indikator.
- **`refresh-data.yml`**: `pip install openpyxl` + `fetch_zweitwohnungen.py` in den
  monatlichen Refresh aufgenommen (fallback-sicher mit `|| echo`).

### Hinweis

- Verifiziert via Pipeline-Run + Preview: 2'110 Gemeinden gefetcht, BFS-Mapping korrekt
  (Zermatt 51.86%, Davos 58.94%, St. Moritz 53.36%, Verbier→Val de Bagnes 54.12% restricted;
  Zürich 9.04% nicht), Signal rendert in Liveness-Warner, keine Konsolenfehler.
- Quelle 3-0 verifiziert (Deep-Research v0.9.25): „ARE Wohnungsinventar auf opendata.swiss,
  jährlich" + „331 Gemeinden >20% per 31.03.2026".

## [0.9.27] — 2026-06-04

### Hinzugefügt — Rechts-Layer: Untermiete-Caveat + Tessin-Präzisierung

Recht ist der Filter VOR der Ökonomie — der fundamentale Go/No-Go für Rent-to-Rent, der bisher
komplett fehlte. Verifiziert via Deep-Research (80 Claims bestätigt / 15 widerlegt).

- **Untermiete-Rechts-Caveat** in der Earn-Card (nur bei Miete > 0, 🟡 MOD): 3 Punkte —
  (1) Zustimmungspflicht Art. 262 OR, (2) Aufschlag begrenzt (BGE 119 II 353, kein Fixdeckel,
  Möblierungs-/Service-Zuschlag legitim), (3) Untermiet-Reform 24.11.2024 abgelehnt → altes Recht gilt.
  Quellen: SVIT Kommentar 2024, Jud/Steiger Jusletter 2017. Klar als „keine Rechtsberatung" markiert.
- **`REGULATORY_STOPS` Tessin präzisiert:** gewerblicher Vermieter ab < 4 Betten (verifizierte
  Korrektur — NICHT 6), max. 90 Tage/Jahr, Registrierungspflicht seit 1.2.2022.
- Neuer Glossar-Term `untermiete` (Art. 262 OR) mit Formel + BGE-Beispiel + Caveat.

### Hinweis

- Verifiziert via Preview: Caveat rendert (Zermatt), Glossar-Link aktiv, kein NaN, keine
  Konsolenfehler, Gold-Box-Styling korrekt (rgba statt Tailwind-Opacity inline).
- Kein Eingriff in Berechnungslogik — reiner Rechts-/Anzeige-Layer.

## [0.9.26] — 2026-06-04

### Hinzugefügt — Insight-Engine Phase 0: Cash-on-Cash + Break-even-Auslastung

- **Custom-Earn-Card** zeigt zwei neue Kennzahlen (🟡 MOD):
  - **Cash-on-Cash**: Jahres-Cashflow ÷ eingesetztes Kapital. Bei Rent-to-Rent = Mietkaution
    (3 Monatsmieten, Art. 257e OR) + Setup-Möblierung (größenskaliert, geschätzt). Inkl. Payback-Jahre.
  - **Break-even-Auslastung**: Occ, ab der Cashflow = 0 — linear aus dem bestehenden Modell
    abgeleitet (Deckungsbeitrag/Nacht). Ampel grün/gelb/rot ggü. erwarteter Auslastung, „nie" wenn >100 %.
- Kapital-Herleitung transparent unter den Kennzahlen, Tier-markiert.
- Neuer Glossar-Term `breakeven`; `coc`-Caveat um R2R-Kontext ergänzt.

### Dokumentation

- `docs/insight-engine.md` — 5-Phasen-Architektur (Anwender → Mustererkennung → Anomalie →
  Hypothese → Härtung → Lernschleife), Trennung diagnostisch/Kalibrierung/Prognose, Daten-Reihenfolge,
  Tool-als-Gedächtnis-Konzept, verifizierte Rechts-Befunde.
- `docs/fachliteratur.md` — verifizierte Quellenliste (Deep-Research, 80 Claims bestätigt / 15 widerlegt)
  inkl. der 4 Rechts-Korrekturen (Untermiet-Reform gescheitert, kein 30–40 % Gewinndeckel,
  Tessin < 4 Betten, FPRE monatlich).

### Hinweis

- Verifiziert: index.html lädt, keine Konsolenfehler, neue Kennzahlen Tier-markiert.
- Kein Eingriff in bestehende Berechnungslogik — CoC/Break-even leiten sich aus vorhandenen
  Werten ab; einzige neue Annahme ist das eingesetzte Kapital (dokumentiert + getiert).

## [0.9.25] — 2026-05-25

### Hinzugefügt — Deep-Research-Befunde integriert (verifizierte Quellen)
Recherche-Output: 110 Sub-Agents, 27 Quellen, 25 Behauptungen geprüft, 18 bestätigt, 7 widerlegt.

**Neue EMPLOYERS (Forschungs-/Bildungs-Cluster):**
- **Villigen**: PSI Paul Scherrer Institut · 2'200 MA + ~2'500 externe Gastforscher/Jahr · nur 53+11+4 Betten on-site (psi.ch/en/guesthouse) → strukturelle Übernachtungs-Lücke
- **Dübendorf**: Empa (1'000 MA), Eawag (500 MA), Innovationspark Zürich (1'500 MA) · 40 Apartments/116 Räume an Seidenstrasse 14/18/24 unter ETH-Priorität (empa.ch/web/s608/guesthouses)

**Neue SUBURBS_OF Solothurn** (Siedlungsstrategie Kanton SO, Primärquelle):
- Balsthal (Regionalzentrum Thal)
- Oensingen (Regionalzentrum Gäu)
- Dornach (Regionalzentrum Dorneck)
- Breitenbach (Regionalzentrum Thierstein)

**Regulatorische Stop-Datenbank `REGULATORY_STOPS`** in Liveness-Warner — höchste Priorität:
- Tessin gesamtkantonal seit 2022-02 (Registrierungspflicht + 90-Tage-Regel) → Lugano, Bellinzona, Locarno, Mendrisio, Paradiso
- Stadt Luzern seit 2025-01 (STR-Reglement)
- Davos + Klosters seit 2021-03
- Arosa (Tourismusabgabe-Registrierung)
- Sigriswil seit 2024-11 (Planungszone 24 Mt nach +75% Listings-Wachstum)

Pro Eintrag: `since` + `note` + `source` (alle Primärquellen aus sab.ch / stadtluzern.ch / dkinfo.ch). Render im Liveness-Warner: ⛔ Banner mit Quelle.

**SUBURBS_OF Zug-Korrektur**: Hypothese „Cham/Risch/Steinhausen/Hünenberg = sekundäre Zentren mit messbarer Zentrumsbildung" wurde adversarial mit 0-3 widerlegt (3 Verifikations-Voten). Notes korrigiert auf neutral „Pendler-Wohngemeinde" + Caveat-Hinweis im Note-Text. Suburb-Einträge bleiben (Pendler-Funktion belegt), aber „Zentren"-Anspruch entfernt.

**Coords.js erweitert** um Villigen + 4 Solothurner Regionalzentren.

**Roadmap nicht-integriert (offene Recherche):**
- BFS PASTA (Parahotellerie-Statistik) — Frage in Recherche nicht vollständig verifiziert
- BFS Wohnungsleerstand — Frage nicht vollständig verifiziert  
- BFS Mietpreisindex — Frage nicht vollständig verifiziert
- ARE Wohnungsinventar (opendata.swiss) — Pipeline könnte 331 Cap-Gemeinden integrieren (verifiziert verfügbar)
- Spital-Patienten-Familien-Bedarf außer Uni-Spitäler — nicht beantwortet

### Verifiziert
- Lugano/Bellinzona/Mendrisio/Locarno/Paradiso → Reg-Stop-Banner sichtbar
- Stadt Luzern → Reg-Stop-Banner
- Davos + Klosters → Reg-Stop-Banner
- Sigriswil → Reg-Stop-Banner
- Solothurn → Suburb-Liste mit Balsthal/Oensingen/Dornach/Breitenbach
- Dübendorf → Empa + Eawag in Großarbeitgeber-Liste (3'000 MA total)
- Zug-Suburbs → Caveat-Note „adversarial 0-3 widerlegt" sichtbar
- Baden → keine Reg-Stop-Warnung (Liveness-Warner behält Business-City-Logik)

## [0.9.24] — 2026-05-25

### Hinzugefügt — Phase C: Brave Search API für vollautomatische Konkurrenz-Recherche
Adrian: „he dann machen wir C" — entschieden für den vollautomatischen Pfad statt OSM-Erweiterung.

Komplette Pipeline gebaut analog zu `fetch_communes.py`:

**Backend `tools/fetch_competitors.py`:**
- Pro Markt 3 Brave-Search-Queries: „Business Apartments [Markt]" · „möblierte Wohnung [Markt]" · „Coworking [Markt]"
- Country=ch, lang=de, max 10 Results/Query
- Filter: Aggregatoren raus (Wikipedia, TripAdvisor, Homegate, etc.)
- Dedup nach Domain (gleiche Domain in mehreren Queries = 1 Eintrag)
- Max 8 Konkurrenten pro Markt
- Rate-Limit: 1 query/sec (Brave Free-Tier-Compliance)
- Robustes Error-Handling: bei API-Abriss bleibt letzte Snapshot intakt
- Updated `_health.json.competitors_brave` mit last_success + queries_used

**Bootstrap `data/competitors.json`** mit 5 Märkten (Baden/Zürich/Luzern/Bern/Basel) im neuen Schema — wird beim ersten Refresh-Run ersetzt.

**Frontend Integration:**
- `loadCompetitors()` lädt parallel zu loadHealth/loadCommunes/loadHesta
- `getCompetitorsFor(name)` merged hardcoded COMPETITOR_LISTS (kuratierte Notes haben Priorität) mit Auto-Detection (ergänzt um neue Anbieter via Domain-Dedup)
- UI zeigt zwei Sektionen wenn beide vorhanden: „Kuratierte Anbieter (mit Notes)" + „🤖 Auto-detektiert via Brave Search"
- Badge zeigt Source-Count: `● kuratiert 5 + auto 3`

**Pricing & Skalierung:**
- Brave Free-Tier: 2'000 Queries/Monat → 60 Märkte × 3 Queries = 180/Monat → kostenlos
- Base-Tier $3/1000 Queries falls Skalierung auf alle 197 Märkte = 591 Queries/Mt

**Workflow erweitert:**
- `.github/workflows/refresh-data.yml` ruft `fetch_competitors.py` monatlich auf
- Env-Variable `BRAVE_SEARCH_TOKEN` als GitHub-Secret

**Setup-Aufgabe für Adrian (manuell, 5 Min):**
1. Brave-Account erstellen: https://brave.com/search/api/
2. API-Token kopieren
3. GitHub Repo Settings → Secrets and variables → Actions → New repository secret
4. Name: `BRAVE_SEARCH_TOKEN`, Value: [Token einfügen]
5. Workflow manuell triggern: Actions → Refresh BFS Data → Run workflow
6. Beim nächsten 5. des Monats läuft es automatisch

**Daten-Tier:**
- Bootstrap data/competitors.json = 🟡 MOD (kuratiert)
- Nach erstem Brave-Run = 🟢 verified (echte API-Results)
- Hardcoded COMPETITOR_LISTS bleibt als Sicherheits-Fallback (Notes haben höhere Qualität als Snippets)

## [0.9.23] — 2026-05-25

### Hinzugefügt — Konkurrenz-Recherche pro Markt (Quick-Search + kuratierte Liste)
Adrian: „Diese arbeit muss für jeden ort gemacht werden als die analyse individuell mit abfragen" (mit Screenshot von Google-Suchresultat „Business Apartments Baden" mit konkurrierenden Anbietern: 1905 Baden, Konnex, Trafo Hotel, GLANDON Apartments).

Im Konkurrenz-Analyse-Block neuer Sub-Block „🔍 Konkurrenz-Recherche":

**1) Kuratierte Top-Konkurrenten** für 5 Bootstrap-Märkte (Baden aus Adrians Screenshot, plus Zürich/Luzern/Bern/Basel als manuelle Recherche):
- **Baden**: 1905 Baden, Konnex, Trafo Hotel, GLANDON Apartments (direkter Wettbewerber), Dein Baden Tagungsräume
- **Zürich**: VISIONAPARTMENTS, The Lyceum, Citizen M, Aparthotels Adagio
- **Luzern**: GLANDON, VISIONAPARTMENTS, B2 Boutique Hotel
- **Bern**: BERNAPARTMENTS, Casa Hotels, VISIONAPARTMENTS
- **Basel**: VISIONAPARTMENTS, Pure Apartments, Aparthotels Adagio

Jeder Eintrag: Name + direkter URL-Link + Kategorie + Notiz mit USP/Positionierung.

**2) Quick-Search-Buttons** mit pre-filled Google-Queries (8 Varianten):
- 🏢 Business Apartments [Markt]
- 🏠 möblierte Wohnung [Markt]
- ☕ Coworking [Markt]
- 🏨 Hotel [Markt] Booking preisvergleich
- 🔑 airbnb [Markt]
- 🏘️ Hausverwaltung [Markt]
- 🌐 site:linkedin.com „travel manager" [Markt] (nur bei Großarbeitgebern > 1000 MA)
- 🏥 Spital [Markt] Patientenbüro Unterkunft (nur bei Spital in Employers)

1 Klick öffnet Google-Suche mit perfekter Query — Adrian muss nicht selbst Query formulieren.

**Verifizierte Anwendung:**
- **Baden**: 5 kuratierte Anbieter + 8 Quick-Search (inkl. Spital wegen Kantonsspital Baden + LinkedIn wegen ABB 6500 MA)
- **Zermatt**: keine kuratierte Liste + 6 Quick-Search (keine Spital/LinkedIn weil keine Großarbeitgeber in EMPLOYERS)

**Roadmap-Hinweis im UI:**
- **Phase B**: OSM-Erweiterung um `tourism=apartment`, `office=coworking`, `tourism=guest_house` → Auto-Liste pro Markt aus OSM-POIs
- **Phase C**: Brave Search API ($3/1000 Queries, 2000 gratis/Mt) → vollautomatische Per-Markt-Recherche analog `fetch_communes.py` mit Health-Tracking

## [0.9.22] — 2026-05-25

### Hinzugefügt — Konkurrenz-Analyse-Modul (Pareto + Channel-Map)
Adrian: „Ich denke das ist wie eine Prozessanalyse. Die gemacht werden muss. Zu Punkt 3 was gibt es für Konkurrenz? Das Tool muss das können. Man muss dann vielleicht auch andere Kanäle nutzen — hier kommt mir wieder mein Green Belt in den Sinn für Six Sigma."

Adrians DMAIC-Framing integriert. Neuer Block im Markt-Detail mit zwei Komponenten:

**1) Pareto-Verteilung der Listings:**
- Top 10% verdienen = avgRevenue × 3.5
- Median (50%) = avgRevenue × 0.85
- Bottom 30% verdienen = avgRevenue × 0.4
- avgRevenue = m.revpar × 365 × STR-Adjust

**STR-Adjust-Faktor** basierend auf Liveness-Risk:
- HIGH-Risk: 35% (Hotel-Occ massiv überoptimistisch für STR)
- MED-Risk: 65%
- LOW-Risk: 85% (Hotel-Occ als guter STR-Proxy)

**2) Channel-Map mit 10 kuratierten Kanälen:**
- **Standard** (Airbnb, Booking.com, Vrbo, Interhome, HomeToGo) — gesättigt = Bottom-50%
- **Eigener Channel** (Direktbuchung-Website) — 100% Marge bei Repeat-Kunden
- **B2B-Direct** (LinkedIn HR-Outreach, Klinik-Patientenbüro, Uni-Housing-Office) — nur bei passenden Großarbeitgebern angezeigt
- **B2B-Platform** (HRG, BCD, Egencia) — nur bei Multinational-Konzernen sichtbar

Channel-Filter dynamisch: zeigt nur relevante Kanäle pro Markt (z.B. Klinik-Kanal nur wenn Spital in EMPLOYERS, Uni-Kanal nur bei Hochschul-Standorten).

**Verifizierte Beispiele:**
- **Baden** (HIGH-Risk Business-Stadt): Top-10% CHF 39k · Median CHF 9k · 9 Channels relevant (inkl. LinkedIn ABB-Outreach + Klinik Kantonsspital + Corporate-Tools)
- **Zermatt** (LOW-Risk Touri-Resort): Top-10% CHF 257k · Median CHF 62k · 6 Channels (Standard + Direktbuchung)
- **Engelberg**: Top-10% CHF 170k · Familie + Resort-Channels

**Konkurrenz-Strategie-Insight im Banner:** „Nicht in die Pareto-Mitte gehen wo 60% der Listings nur Ø verdienen. Top 10% positionieren (Superhost + Multi-Channel + Pro-Setup) oder klare Nische bedienen (Crew/medizinisch/Familie 6+)."

### Hinzugefügt — Glossar „DMAIC" + „Konkurrenz-Analyse"
Neue Glossar-Einträge dokumentieren:
- **DMAIC** als Tool-Framework mit konkretem Baden-Beispiel pro Phase (Define/Measure/Analyze/Improve/Control)
- **Konkurrenz-Analyse** mit Pareto-Formel, STR-Adjust-Faktoren und Strategie-Empfehlung

## [0.9.21] — 2026-05-25

### Hinzugefügt — Markt-Chancen-Scout (Persona-Hotel-Vergleich + Großarbeitgeber)
Adrian: „Frage über alles muss ich solche probleme nun finden oder können wir auch etwas entwickeln das genau das tut? Ein trick den ich hatte um die preise etwas zu kalkulieren war: Ichversetzte mich in die lage eines Familienvaters und suchte nach angeboten. Ich wollte doch meiner Familie etwas bieten. Also schaute ich mir zuerst die Hotels an und mit entsetzen stellte ich fest ich bezahle für ein ganz einfaches hotel für 4 personen den betrag x. Ich wusste gleichzeitig was ich als airbnb anbot und machte ihm einen besseren deal als das Hotel — das funktionierte sehr gut. Das selbe würde auch funktionieren als typ der business mässig zu ABB muss."

Adrians Methode als Algorithmus implementiert. Neuer Block im Markt-Detail oberhalb der Earn-Card.

**Datenstruktur GROSSARBEITGEBER**: hardcoded für 17 wichtigste CH-Standorte mit Firma + Sektor + Mitarbeiterzahl + km zum Zentrum + Notiz. Beispiele:
- Baden: ABB (6'500), Axpo (1'500), GE Power (1'200), Kantonsspital (2'700)
- Kloten: Flughafen ZRH (1'900) + Swiss/LH (9'000) + Swissport (4'000)
- Basel: Roche (12'000), Novartis (11'000), Unispital (8'000)
- Bern: Bundesverwaltung (38'000), Swisscom (7'000), Inselspital (11'000)
- Zug: Glencore, Roche Pharma, Crypto-Valley-Cluster

**4 Personas** mit Hotel-Aufschlag-Modell und Apartment-USP:
- 💼 **Business-Reisender** (Mo-Fr): Hotel ab CHF 110, Apartment-USP Wochenpaket+Küche
- 👨‍👩‍👧‍👦 **Familie 4 Personen**: Hotel × 1.70 (Familienzimmer-Aufpreis ab CHF 200), Apartment 2 SZ+Waschmaschine
- 💑 **Paar Wellness**: Hotel × 1.30 (ab CHF 150), Apartment Romantik+Spa-Korb
- ✈️ **Flugcrew/Logistik**: Hotel ab CHF 90, Apartment Direktverträge mit Airlines

**Pro Persona berechnet**: was kostet ein Hotel realistisch (BFS-ADR × Persona-Multiplier), was kannst du anbieten (-25% Diskont), klares USP gegen Hotel, **konkrete Sichtbarkeit-Channels** (Booking.com Business, Airbnb Familien-Filter, LinkedIn HR-Outreach, Crew-Direktverträge etc.).

**Verifizierte Klassifikation:**
- **Baden** → ABB (6'500 MA) + 3 Personas (Business + Familie + Wellness wegen Thermalbad)
- **Kloten** → Aviation-Cluster (~15'000 MA) + Business + Crew (Crew-Persona triggert nur bei Flughafen-Distanz < 15 km)
- **Engelberg** → Familie + Wellness (Lifte > 5 → Resort-Setup)
- **Bad Ragaz** → Wellness Only (Thermalbad-Pattern)

**Daten-Tier-Transparenz:**
- 🟢 Arbeitgeber-Liste kuratiert aus öffentlichen Firmen-Websites
- 🟡 Hotel-Preise BFS-ADR × Persona-Aufschlag-Modell
- 🔴 Personas Branchen-Heuristik (whenSuitable-Logic)

## [0.9.20] — 2026-05-25

### Hinzugefügt — STR-Liveness-Warner (Hotel-Daten ≠ STR-Daten)
Adrian: „ich habe mir Baden angeschaut da gibt es nicht wirklich ein angebot auf airbnb. Ich habe mir jetzt eine unterkunft angeschaut die hat in einem ganzen Jahr 4 bewertungen der Kalender ist aber offen wie es mir scheint. Ich sehe ehrlich gesagt ein sehr hohes risiko. Jedoch du sagst etwas andres."

**Field-Check zeigte systematischen Bug:** Tool benutzt BFS-Hotellerie-Auslastung (41% Baden) als Proxy für STR-Auslastung. Das funktioniert in Touri-Resorts, ist aber in Business-Märkten systematisch zu optimistisch. Adrians Baden-Listing: 4 Reviews/Jahr → ~5-10% reale STR-Occ, nicht 41%. Differenz Faktor 4-6×.

Neuer roter/gelber Warn-Banner im Markt-Detail oberhalb der Earn-Card. Triggert bei:
- **Listings < 100** → HIGH (Markt zu klein)
- **Listings < 250** → MED
- **City-Profile aber nicht Premium** (Zürich/Genève/Basel/Lausanne/Bern/Luzern) → HIGH (Geschäftsreisende übernachten in Hotels, keine STR-Demand)
- **Hotel-Occ ≥ 40% + City + nicht Premium** → HIGH (Mismatch Hotel-STR-Demand)
- **Wenige OSM tourism_info-POIs** → MED

Banner enthält **konkrete Sanity-Check-Anleitung**:
1. 3-5 vergleichbare Listings auf Airbnb/Booking öffnen
2. Reviews-Anzahl letzte 12 Monate zählen
3. Kalender-Verfügbarkeit prüfen
4. Realistische STR-Occ berechnen: `(Reviews × 1.5 × 3 Nächte) ÷ 365`
5. Diese Realität in Custom-Karte eintragen statt Markt-Schnitt

Verifizierte Klassifikation:
- **Baden** → HIGH (3 Signale: Listings 165, Business-Stadt-Profile, Hotel-STR-Mismatch)
- **Olten** → HIGH (gleicher Pattern)
- **Zermatt / Zürich / Luzern** → keine Warnung (Premium-Touri/Premium-Stadt)

Roadmap: Inside Airbnb-Pipeline würde Reviews-pro-Listing-Statistik liefern → empirische STR-Occ statt Heuristik.

## [0.9.19] — 2026-05-25

### Hinzugefügt — Reality-Check für Custom-Slider gegen BFS-Markt
Adrian: „Worst 60'000 ist crazy high finde ich. Eine gute wohnung in Luzern mach ich einen tagesschnit von 145chf * 365 tage ergibt 53'000chf. Ich würde sagen in Luzern möglich weshalb sollt edas in Baden möglich sein?"

Adrian hatte recht — sein Custom-Input (Baden 4.5Z, ADR 200, Occ 60%) lag bereits **+57% über dem BFS-Markt-Schnitt** für 4.5Z in Baden, bevor irgendein Optimierungs-Hebel aktiviert wurde. Das war im Tool nicht transparent. Jetzt sichtbar:

**Custom-Slider zeigt unter jedem Slider** den Markt-Schnitt aus BFS + Delta-Prozent:
- ADR-Slider: „Markt-Schnitt 4.5Z: CHF 200 · +0% ggü Markt" (grün)
- Occ-Slider: „Markt-Schnitt 4.5Z: 38% · +57% über Markt — sehr optimistisch" (rot)
- Wenn Delta > 30%: Reality-Check-Banner: „⚠ Deine Annahmen liegen deutlich über dem Markt-Schnitt. Top-10% Listings möglich, aber nicht der Default-Fall."

**Optimierungs-Forecast bekommt Markt-Basis-Box** parallel zur Custom-Annahme:
- Links grün: 📊 Markt-Basis (BFS-modelliert) mit Optimierungs-Median
- Rechts: 🎛️ Deine Custom-Annahme mit Delta-Prozent
- Bei > 30% Abweichung: rote Border + Warn-Label

Verifiziert Baden 4.5Z:
- Markt-Basis: ADR 200, Occ 38% (BFS) → **CHF 32'350 brutto/Jahr**
- Adrian's Custom: ADR 200, Occ 60% → **CHF 50'950** (+57%)
- Jetzt sichtbar: das hohe Worst-Case-Stack-Resultat war Folge der optimistischen Basis-Annahme, nicht des Hebel-Modells.

Apfel-mit-Apfel für Adrian's Luzern-Anker:
- Baden 4.5Z Markt: CHF 32k brutto
- Luzern 3.5Z Markt: ~CHF 55k brutto (BFS Luzern Occ ~60% × ADR ~215 × 365)
- Luzern objektiv 70% stärker als Baden — Tool zeigt das jetzt im Markt-Basis-Vergleich

## [0.9.18] — 2026-05-25

### Hinzugefügt — Optimierungs-Forecast mit Range + Konfidenz (🔴 MOCK explizit gelabelt)
Adrian: „wenn ich es mir genauer anschauen möchte. Es könnte noch tiefer gehen. Eine 4 1/2 zimmer wohnung ist 60% ausgebucht kostet 200. Wie würde es aussehen wenn ich Superhost werde?" — gefolgt von Risiko-Filter: „wir raten nicht. Es geht um echte Investitionen anhand des Tools" und Pattern-Klärung: „wenn wir Schätzungen machen sagen wir das und sagen auch wie stark es variieren kann wie genau dass predictiv sein wird."

Neuer Block unter der Earn-Card mit 6 Optimierungs-Hebeln. **Strikt als 🔴 MOCK markiert** (Plausibilitäts-Schätzung, keine empirischen CH-Daten).

Pro Hebel Range statt Punkt-Schätzung:
| Hebel | ADR-Range | Occ-Range | Konfidenz | Median erreichbar |
|---|---|---|---|---|
| ⭐ Superhost-Status | +5–18% | +10–30% | MED | 40% der Hosts |
| 📸 Pro-Fotos | +2–12% | +5–18% | MED | 70% |
| 📈 Dynamic Pricing | +5–22% | +0–10% | MED | 55% |
| 🌟 4.8★+ Rating | +2–10% | +3–15% | LOW | 50% |
| 🌐 Plattform-Diversifizierung | +0–5% | +5–25% | MED | 75% |
| ✏️ Listing-Optimierung | +1–7% | +3–12% | LOW | 80% |

**Stack-Forecast** zeigt 3 Szenarien:
- Worst Case (alle Min-Werte stacked + Diminishing Returns)
- Median (Erwartungswert)
- Best Case (alle Max-Werte stacked)

Plus **Achievability-Prozent**: multiplikativ aus Pro-Hebel-Wahrscheinlichkeiten — verhindert Illusion dass alle Hebel parallel auf Median erreicht werden können.

Verifiziert an Baden 4.5Z, ADR 200, Occ 60% (Adrian's konkretes Beispiel):
- IST: CHF 43'800 Brutto/Jahr
- Stack Superhost + Pro-Fotos:
  - Worst: CHF 60'884 (+39%)
  - Median: CHF 74'292 (+70%)
  - Best: CHF 94'055 (+115%)
  - Wahrscheinlichkeit Median: 28% (40% × 70%)

**Ehrliche Quellen-Angabe pro Hebel**: „Plausibilitäts-Schätzung · Branchen-Konsens" statt erfundene Cornell/AirDNA-Zitate. Bei Klick auf MOD/MOCK-Badges öffnet sich neuer Glossar-Eintrag „Schätz-Modus" mit Tier-System-Erklärung.

Globaler Warn-Banner über dem Modul: „⚠ Schätzung, keine empirische Datenbasis — verwende für Investitions-Entscheidungen nur mit eigenem Sanity-Check."

Roadmap: Inside Airbnb-Pipeline (CH-Städte gratis CSV) würde Superhost-Lift auf empirische Werte heben → 🟡 MOD-Hochstufung möglich.

### Hinzugefügt — Glossar „Schätz-Modus" (Tier-System dokumentiert)
Neuer Eintrag erklärt 🟢 BFS / 🟡 MOD / 🔴 MOCK mit konkreten Beispielen pro Tier. Klickbar via neue „ⓘ Schätz-Modus"-Badges im Optimierungs-Forecast.

## [0.9.17] — 2026-05-25

### Hinzugefügt — Smart Suburb Detector (Auto-Klassifikation aus CH-Gemeinde-Liste)
Adrian: „es geht mir ja da drum das das system smart ist um solche sachen selbständig zu finden. und ja es ist richtig das wir nicht bauen wenn das risiko zu hoch ist."

Hardcoded SUBURBS_OF skaliert nicht. Jetzt liest das Tool die vollständige CH-Gemeinde-Liste und findet Vororte automatisch.

**Backend**: `tools/fetch_communes.py` holt alle ~2'131 CH-Gemeinden mit Koordinaten + Einwohnerzahl + Kanton via Wikidata SPARQL (Q70208 = Schweizer Gemeinde). Schreibt `data/communes.json` und updated `_health.json`. Robustes Error-Handling: bei API-Abriss bleibt letzte erfolgreiche Snapshot intakt, Status auf error → Banner gelb/rot.

**Bootstrap**: `data/communes.json` initial mit 90 wichtigen CH-Gemeinden (Mutterstädte + bekannte Vororte) befüllt für sofortige Funktion. Wird beim ersten echten Refresh-Run durch vollständige Wikidata-Liste ersetzt.

**Frontend**: Neue Funktion `autoSuburbsFor(motherCityName, radiusKm=15, limit=12)`:
- Alle Gemeinden in Luftlinien-Radius
- Ausgeschlossen: Gemeinden mit ≥40% der Mutterstadt-Einwohner (= eigene Stadt)
- Suburban-Score = log(Population) / max(km, 0.5) — bevorzugt nahe + signifikante Gemeinden
- Top-N sortiert nach Score

Verifizierte Auto-Detection:
- **Luzern**: findet Kriens (2.5 km), Emmen (3.2), Horw (3.6), Ebikon (4.3), Adligenswil (4.3) + zusätzlich Risch/Rotkreuz (13.8 km) das nicht in der kuratierten Liste war
- **Zürich**: Wallisellen, Opfikon, Dübendorf, Schlieren, Kloten (alle korrekt im 15-km-Radius)
- **Bern**: Köniz, Ostermundigen, Muri, Belp

**UI**: Neuer Block „🤖 Auto-detektierte Vororte — Smart Suburb Detector" oberhalb des kuratierten SUBURBS_OF-Blocks. Auto-Gemeinden die zusätzlich kuratierten Kontext haben sind grün markiert + „✓ kuratiert mit Kontext"-Label.

**Aktualisierungs-Garantie** (Adrian's Risiko-Filter):
- GitHub Action `refresh-data.yml` ruft `fetch_communes.py` monatlich auf
- `data/_health.json.sources.communes_wikidata` trackt last_success / status / Frequenz
- Bei Wikidata-Abriss: last_success bleibt stehen → Tage-Alter steigt → Banner gelb (>35d) / rot (>65d)
- Frontend fällt elegant zurück: wenn `communes.json` nicht ladbar → Auto-Block versteckt, kuratierte SUBURBS_OF bleibt

## [0.9.16] — 2026-05-25

### Hinzugefügt — Daten-Health-Layer (Adrian's Aktualitäts-Garantie)
Adrian: „wenn etwas monatlich publiziert wird ist das okay aber das muss getrkt werden wenn es dort einen abriss gibt die daten müssen immer autonom gezigen werden ach einem monat um das tool aktuel zu behalten ansonsten ist es nicht gut. wir sollten auch kein risiko eingehen wenn wir das nicht sicher stellen können."

Zentrale `data/_health.json` mit Status pro Datenquelle (BFS HESTA, BFS Origins, OSM POIs, Markt-Koordinaten, Steuersätze, Suburbs). Pro Eintrag: last_success, expected_frequency (monthly/continuous/yearly/static), period_covered, status (ok/warn/error), Quelle-URL, Note.

Frontend `loadHealth()` → `renderHealthBanner()`:
- Header-Pille statt „BFS-Snapshot lädt…": **🟢 Daten frisch · Stand 2026-05-15** / 🟡 Refresh überfällig / 🔴 Daten veraltet
- Klick öffnet Detail-Modal mit Status pro Quelle, Tage-Alter, Frequenz, Schwellwerte
- Bei warn/error: zusätzlicher gelber/roter Banner über der Karte
- Schwellwerte: monthly < 35d OK, < 65d Warn, > 65d Error · continuous < 14d OK · yearly < 400d OK · static immer OK

Roadmap: GitHub Action `refresh-data.yml` schreibt _health.json bei jedem erfolgreichen Refresh-Run. Bei Fehler bleibt last_success stehen → Banner geht automatisch auf gelb/rot.

### Hinzugefügt — Karten-Filter „nach Use-Case"
8 Buttons über der Karte: ✈️🏢🎓🏥🎿🌊♨️👨‍👩‍👧. Multi-Select. Nicht-passende Marker auf 15% Opacity. Kombiniert mit Tier-Filter und Heimat-Filter. Filter-Info-Zeile zeigt aktive Filter: „Use-Case: 🏢 Business-Standort + ✈️ Airport-Hub".

### Hinzugefügt — Notfall-Score in Top-Tabelle
Neuer Sortier-Toggle: „nach RevPAR" (Default) vs „🚨 Notfall-Score" (RevPAR ÷ Fahrtzeit²). Letzteres bevorzugt nahe + gute Märkte und ist nur aktivierbar wenn Heimat-Standort gesetzt. Spalten zeigen zusätzlich 🚗-Fahrtzeit + Score. Title-Header passt sich an.

### Hinzugefügt — Earn-Card Setup-Presets
3 Setup-Varianten (Business/Familie/Wellness) als auto-vorgeschlagene Earn-Card-Werte:
- **Business**: ADR × 1.15, Occ × 1.05, CleanCost × 1.10, TV-Abo CHF 15
- **Familie**: ADR × 1.10, CleanCost × 1.20 (mehr Bettwäsche), TV-Abo CHF 45 (Kinder-Streaming)
- **Wellness**: ADR × 1.20, Occ × 0.95, CleanCost × 1.15 (Bademantel-Wäsche)

Jeder Setup-Tip-Block bekommt einen „🎛️ Preset in Earn-Card übernehmen →"-Button. Klick füllt `_earnCustom` mit den preset-gewichteten Werten relativ zur Markt-Baseline und scrollt zur Earn-Card.

### Hinzugefügt — SUBURBS_OF +4 Städte (Winterthur, St. Gallen, Lugano, Zug)
17 neue Vororte mit Koordinaten + Notes + Regulierungs-Status:
- **Winterthur**: Wülflingen, Töss, Wallisellen, Effretikon
- **St. Gallen**: Gossau, Herisau, Wittenbach, Rorschach
- **Lugano**: Paradiso, Massagno, Manno (Tecnopolo), Mendrisio (FoxTown)
- **Zug**: Baar, Cham, Steinhausen, Rotkreuz (Crypto-Valley / Roche / ABB)

Plus erweiterte `MARKET_COORDS` für Distanz-Berechnung auch bei Vororten.

### Verbessert — Resort-Tag-Klassifikation
Bug: Adelboden, Wengen wurden nicht als Resort getaggt weil OSM-aerialway-Count fehlt oder zu niedrig ist. Fix: Resort-Tag jetzt auch via Family-Whitelist oder profile=winter, mit klarem „OSM-POI-Daten fehlen" Hinweis im Why-Text. Adelboden + Wengen jetzt korrekt 🎿 Resort + 👨‍👩‍👧 Familie.

### Vereinheitlicht — Datenfrische-Indikator
Alte parallele Logik (BFS HESTA period_end → dataFreshness) entfernt. Alle Status-Anzeigen laufen über DATA_HEALTH. period_end aus HESTA wird in DATA_HEALTH.sources.bfs_hesta.period_covered gespiegelt.

## [0.9.15] — 2026-05-25

### Hinzugefügt — Familie + Wellness Use-Case-Tags
Adrian: „wo findet familie statt wo findet wellness statt ganz wichtige frage die zu verbinden sind mit den signalen"

Zwei neue Klassifikatoren in `deriveUseCases`:
- **♨️ Wellness-/Thermal-Markt HIGH** via Name-Pattern (Bad/Bagni/Bains, Leukerbad, Vals, Scuol, Ragaz, Yverdon, Zurzach, Saillon) ODER Tag „Thermalbad". Verifiziert: Bad Ragaz, Leukerbad, Vals, Yverdon, Baden — alle HIGH.
- **👨‍👩‍👧 Familien-Destination HIGH/MED** via Whitelist (22 etablierte Familien-Resorts) ODER (family_score > 70 + aerialway ≥ 5 oder Spielplatz ≥ 4 + lifestyle_score < 80 — nicht Party-Markt). Verifiziert: Saas-Fee, Engelberg, Davos = HIGH. Lenk, Adelboden, Wengen = MED.

Beide bekommen Setup-Tips:
- **Familie**: 4.5Z+, 2 Schlafzimmer, Stockbett, Hochstuhl, Geschirrspüler. Längere Stays 5–7 Nächte, weniger Wechsel, +10–15% ADR mit Skipass-Paket.
- **Wellness**: Thermalbad-Voucher als Welcome, Bademantel + Hausschuhe, Tee-Bar. Zielgruppe 50+. 3–4 Nächte Mi–So, +CHF 30–50/N, hohe Repeat-Rate.

### Hinzugefügt — Suburban Arbitrage: Vororte-Map
Adrian: „du kannst bern, luzern listen aber die sind ja eigentlich out of the game... hier wäre jedoch spannend welche umkreise sind nicht betroffen. ich weiss zum beispiel das horw neben luzern nicht betroffen ist das es ein bahnhof gibt mattenhof ist am bauen … was müsste gegeben sein das du das auch findest"

Neue Datenstruktur `SUBURBS_OF` mit kuratierten Vororten zu 6 Großstadt-Clustern (Luzern, Bern, Zürich, Genève, Basel, Lausanne) — total ~30 Vororte. Pro Vorort: Koordinaten, km zum Zentrum, ÖV-Anbindung, Autobahn-Distanz, Entwicklungs-Notiz, Regulierungs-Status.

Beispiel Luzern → **Horw** (Mattenhof-Entwicklung, Hochschule Luzern, S-Bahn 10 min, Autobahn 1.5 km, keine Cap-Beschränkung), Kriens (Mall of Switzerland), Emmen (Seetalplatz), Ebikon (Mall + Roche), Adligenswil (Schindler).

UI-Block in der Markt-Detail-Card:
- **Wenn aktiver Markt eine Mutterstadt ist** → „🏘️ Suburban Arbitrage — Vororte von [Stadt]" mit Grid aller Vororte (Bauprojekte, ÖV, Regulierung)
- **Wenn aktiver Markt ein Vorort ist** → grüner Banner „[Markt] = Vorort von [Stadt]" mit Direkt-Link zur Mutterstadt
- **Sonst** (Resorts wie Zermatt) → kein Block

Die These dahinter: Stadt = teuer + reguliert. Vorort = ähnliche Demand (Pendler, Konferenzen, Touri-Stop), aber tiefere Kaufpreise, weniger Konkurrenz, oft mildere Regulierung (z.B. Luzern hat 90-Tage-Cap, Horw nicht).

Verifizierte Klassifikationen: Luzern → Suburb-Block mit Horw/Mattenhof. Bern → Köniz/Belp. Kloten → „Vorort von Zürich" mit Crew-Übernachtungs-Hinweis. Zermatt → kein Block (echter Resort-Markt, keine Arbitrage-Logik).

## [0.9.14] — 2026-05-25

### Hinzugefügt — ALOS + Sommer/Winter-Ratio als Demand-Signale
Adrian: „gibt es auch gute beispiele von denen man lernen kann die irgendjemand wird die daten gesammelt haben und wie du es richtig sagst business buchen eher weniger am weekend. Die frage ist hier was sind die richtigen signale"

Das Tool nutzt jetzt zwei zusätzliche BFS-Signale die wir hatten aber ignorierten:

**1) Average Length of Stay (ALOS)** = `bfs.nights_12m ÷ bfs.arrivals_12m` aus Hotel-HESTA. Industrie-Standard-Klassifikation:
- ALOS < 1.8 = **Business** (Crew, Frühflug, 1-Nacht-Stops)
- ALOS 1.8–2.5 = **Citytrip** (Wochenend-Kurztrip)
- ALOS 2.5–4.5 = **Mixed** (Familien-Ferien)
- ALOS > 4.5 = **Resort** (Skiwoche, Sommer-Ferien)

Live-Werte aus Tool: Kloten 1.38 · Bern 1.73 · Zürich 1.83 · Lugano 1.91 · Engelberg 2.11 · Genève 2.16 · Zermatt 2.43 · Verbier 2.71 · Saas-Fee 2.77. Reihenfolge stimmt mit Branchen-Realität überein.

**2) Sommer-Winter-Ratio** = `mean(seasonality[Jun-Aug]) ÷ mean(seasonality[Dez-Feb])`:
- > 1.4 = **sommer-dominiert** (See, Stadt, Wander)
- < 0.7 = **winter-dominiert** (Ski-Resort)
- 0.7–1.4 = **ganzjährig** (Business, Mixed)

Live-Werte: Verbier 0.57 (Winter) · Zermatt 0.89 (ausgewogen wegen Sommer-Bergsteigen) · Kloten 1.31 (ganzjährig) · Bern 1.80 · Bellinzona 2.58 · Lugano 3.06 (Sommer-getrieben).

Beide Signale in `computeSiteSignals(m)` integriert + im UI sichtbar (🛏️ ALOS-Zeile + ☀️/❄️ Sommer/Winter-Zeile in der Use-Case-Card).

### Verbessert — Use-Case-Tag-Logik strenger
Kloten wechselt von Business MED auf HIGH wegen ALOS-Signal (kurze Stays). Resort-Tag dominiert jetzt korrekt: Engelberg/Zermatt zeigen nicht mehr Doppel-Tag (Resort + Citytrip). Citytrip-Tag nur gesetzt wenn weder Business noch Resort klassifiziert.

### Hintergrund — gold-standard Signale der Hospitality-Industrie
| # | Signal | Branche-Standard | Wir nutzen? |
|---|---|---|---|
| 1 | Day-of-Week-Index | Mo–Do vs Fr–So | ❌ BFS nur monatlich |
| 2 | ALOS | <1.8 Business · >2.5 Resort | ✅ NEU in v0.9.14 |
| 3 | Booking Lead Time | <14d Business · >30d Leisure | ❌ kostenpflichtige Daten |
| 4 | Saisonalitäts-Spread | flach=Business, peak=Resort | ✅ in v0.9.13 |
| 5 | Gäste-Origin-Mix | US/UK/Asien=Business · DE/FR/IT=Touri | ✅ in v0.9.13 |
| 6 | Sommer/Winter-Inversion | Stadt/See vs Ski | ✅ NEU in v0.9.14 |
| 7 | Channel-Mix GDS/OTA | Corporate vs Leisure | ❌ keine offene Quelle |
| 8 | Hotel-Bed-Dichte/Einwohner | Tourismus-Intensität | 🟡 BFS hat es, noch nicht integriert |

## [0.9.13] — 2026-05-25

### Hinzugefügt — Standort-Signale & Use-Case-Tags pro Markt
Adrian: „was mich auch beschäftigt ich könnte nähe flughafen kloten wohnungen haben die würde ich dann für buisness einrichten. Was müsste passieren das du solche sachen wie he ich kloten benötigt buisness übernachtung, der standort benötigt x, das brauch ich"

Neuer Banner in der Markt-Detail-Card oberhalb der KPIs: „🎯 Standort-Signale & Use-Cases". Aktiviert eine Use-Case-Klassifikation pro Markt aus existierenden BFS- und OSM-Daten — ohne neue API.

Berechnete Signale (`computeSiteSignals(m)`):
- **Flughafen-Distanz** (Haversine zu ZRH/GVA/BSL/LUG/BRN)
- **Hauptbahnhof-Distanz** (Zürich HB / Bern HB / Basel SBB / Genève / Lausanne / Luzern)
- **Business-Gäste-Mix** = % US + UK + Indien + China + Japan + Korea + Israel + UAE
- **Touri-Gäste-Mix** = % DE + FR + IT + AT + NL + BE
- **Saisonalitäts-Spread** (max/min des BFS-Monatsvektors) + Flatness-Score
- **Markt-Reife** = nights_12m ÷ listings (Hotel-Nächte pro STR-Listing)
- **OSM-Counts**: aerialway, hotels, hospitals, restaurants
- **Research-Hub** Set (ETH/EPFL/Uni-Standorte)

Abgeleitete Tags (`deriveUseCases(m, s)`):
- ✈️ **Airport-Hub HIGH** wenn Flughafen < 15 km
- 🏢 **Business-Standort HIGH/MED** wenn US/UK/Asien-Gäste > 20% UND Saison flach (Ratio < 1.5×)
- 🎓 **Bildungs-/Forschungs-Cluster** für Zürich/Lausanne/Bern/Basel/Genève/St. Gallen/Fribourg/Neuchâtel/Lugano
- 🏥 **Klinik-Cluster** wenn OSM hospital > 0 UND nights_12m > 50k
- 🎿 **Resort-Tourismus** wenn OSM aerialway > 10
- 🌊 **Sommer-/See-Tourismus** wenn profile=summer UND aerialway < 5
- 🏠 **Generischer Markt** als Fallback

Verifizierte Klassifikation:
- **Kloten** → ✈️ Airport HIGH (2.8 km ZRH) + 🏢 Business MED (25% US/UK/Asien, Saison 1.5× flach)
- **Zürich** → ✈️ + 🏢 + 🎓
- **Zermatt / Verbier / Davos / Engelberg** → 🎿 Resort HIGH
- **Lugano** → ✈️ + 🎓 + 🌊
- **Baden** → 🏥 Klinik-Cluster

Business-Setup-Tip-Block erscheint automatisch wenn 🏢 Tag aktiv: „Schreibtisch + WLAN als Pflicht, weniger Deko, kein TV-Schwerpunkt · +15–20% ADR ggü. Touri-Setup, kürzere Stays (1–2 Nächte statt 4), Mo–Do höher als Wochenende."

Plus: 6 fehlende Flughafen-Vorort-Koordinaten in `js/coords.js` ergänzt (Kloten, Opfikon, Rümlang, Wallisellen, Bülach, Dübendorf).

## [0.9.12] — 2026-05-25

### Hinzugefügt — Heimat-Filter: max Fahrtzeit ab Wohnort
Adrian: „Engelberg ist noch ein mögliches einzugsgebiet. das heisst dort habe ich noch die kontrolle. Ich kann ins auto steigen und bin im notfall in einer stunde dort. ich würde das aber nicht für das wallis machen mit 3.-4 stunden fahrt."

Neuer Filter direkt unter der Karte: **🏠 Mein Einzugsgebiet**. Dropdown mit ~20 Schweizer Städten (gruppiert nach Region) + Slider **max Fahrt** von 0.5h bis 4h (Schritt 15min).

Wie es rechnet (Heuristik, transparent gelabeled):
- Haversine-Distanz aus `MARKET_COORDS` (Luftlinie km)
- × 1.4 Strassen-Faktor (CH-Topologie, Pässe)
- ÷ 75 km/h Mix Autobahn + Landstrasse
- Verifizierte Werte ab Zürich: Engelberg 1h 10min (real ~1h 5min), Davos 2h 10min (real 2h 15min), Zermatt 3h 2min (real 3h 30min), Verbier 3h 15min (real 3h 15min)

Verhalten:
- Marker ausserhalb Radius werden auf 15% Opacity gedimmt und sind unklickbar
- Heimat-Pin als schwarzer Punkt mit gestricheltem Ring + Label 🏠 [Name] auf der Karte
- Filter-Info-Zeile: „X/81 Märkte sichtbar · 🏠 Zürich · max 2h"
- Markt-Detail-Subtitle erweitert: „… · 🚗 ~1h 10min ab Zürich"
- Karten-Tooltip beim Hover über Marker zeigt zusätzlich „🚗 ab [Heimat]: 1h 10min"
- Kombiniert mit Tier-Filter (Performance + Distanz gleichzeitig)
- Persistenz via `localStorage.swissstr_home` — Wahl überlebt Reload

Verifizierte Beispiele ab Zürich: 1h = 15 Märkte (Zentralschweiz inkl. Engelberg) · 1h 30min = 29 · 2h = 43 (mit Davos/Andermatt) · 4h = alle 81.

## [0.9.11] — 2026-05-25

### Hinzugefügt — Karten-Transparenz: was steckt hinter den Zahlen?
Adrian: „was ist das sind das daten von hotelübernachtung Airbnb beides. was ist es genau"

Unter der Hauptkarte „Top Schweizer STR-Märkte" neuer Quellen-Block mit 4 Zeilen (Badge + KPI + Quelle):
- 🟢 BFS — **Auslastung** = Hotellerie HESTA (188/197 Märkte verifiziert)
- 🟡 MOD — **ADR · RevPAR** = modelliert pro Markt-Profil, kein Airbnb/Booking-Scraping
- 🟡 MOD — **Listings** = STR-Schätzung (HESTA zählt nur Hotels)
- 🟢 BFS — **Saisonalität · Gäste-Mix** = HESTA Logiernächte Monatsvektor

Plus Footnote: „relative Reihenfolge der Märkte verlässlich · absolute CHF-Werte ±20% Schätzung". Klare Roadmap angedeutet: ADR/RevPAR gehen auf 🟢 sobald BFS Parahotellerie-Preise publiziert oder ein STR-Scraper läuft.

### Hinzugefügt — Karten-Filter Hoch/Mittel/Tief
Adrian: „zweitens könnte man es auch filtern zwischen hoch mittel und tief. wenn mann will"

Neue Filter-Toolbar zwischen Metric-Toggle und Karte: 4 Buttons (Alle · 🔴 Hoch · 🟡 Mittel · ⚪ Tief). Tertile werden dynamisch aus den Werten des **aktiven Metrics** (RevPAR/ADR/Auslastung/Grade) berechnet. Multi-Select möglich — z.B. Hoch+Mittel zeigt nur die oberen 2/3.

Nicht-gewählte Marker werden auf 15% Opacity gedimmt und sind unklickbar (pointer-events off). Metric-Wechsel rechnet die Tertile neu (z.B. von „RevPAR Hoch" auf „Auslastung Hoch" — andere Marker bleiben sichtbar).

Beispiel: 81 Marker total · Filter „Hoch" auf RevPAR → 28 sichtbar (≈ oberes Tertil) · Klick „Alle" → alle 81.

## [0.9.10] — 2026-05-25

### Hinzugefügt — Saisonalitäts-Chart klickbar → KPIs filtern
Adrian: „bei saisonal als beispiel will ich den monat anklicken oder mehrere und es soll sich der output oben entsprechend anpassen."

Monats-Bars im Saisonalitäts-Chart sind jetzt klickbar (Multi-Select). Beim Klick werden RevPAR / ADR / Auslastung oben auf die ausgewählten Monate gefiltert. Nicht-ausgewählte Bars werden gedimmt (25% Opacity), ausgewählte bekommen schwarzen Rahmen. Ein „× Filter zurücksetzen"-Button erscheint sobald mindestens ein Monat selektiert ist; Markt-Wechsel resettet automatisch.

Beispiel Engelberg: Default RevPAR 157 / ADR 245 / Occ 46% → Filter Feb+Jul → RevPAR 184 / ADR 312 / Occ 59% (Hochsaison-Peak). Delta-Zeile zeigt „Filter: Feb·Jul (2/12)" statt YoY-Wert.

Implementierung: `_seasonSelectedMonths` State, `onClick`-Handler in Chart.js options, neue `recomputeKpisForSeason(m)`-Funktion. Saisonalitätsprofil (BFS oder Profil) wird auf gewählte Indizes gemittelt und mit `m.adr` / `occOf(m)` multipliziert.

### Korrigiert — Konfidenz-Glossar: Verbesserungs-Pfad statt Konkurrenz-Vergleich
Adrian: „etwas darfst du nicht vom konkurenzprodukt reden. aber mein hauptpunkt ist du sagst was das problem ist also wenn du das kennst kannst du es grundsätzlich auch beheben. das heisst wenn der user spezifisch wird mit dem was er hat kannst du auch genauer werden richtig? das muss auch so aufgezeigt werden."

Konfidenz-Modal umgeschrieben in `js/glossary.js`:
- AirDNA-Erwähnung entfernt aus `caveat`
- `longDe`: klare Botschaft Markt-Ebene (±30–50%) vs. konkrete Wohnung (±10–15%)
- Neues `improve`-Feld mit 6-Punkte-Liste was der User selbst tun kann um die Spanne zu schrumpfen: ADR aus Listings mitteln, Saisonalität-Filter, exakter Mietzins, Putzkraft anpassen, Plattform-Modus wählen, Wohnungstyp setzen
- Faustregel: „jeder konkrete Input ersetzt eine Modell-Annahme. Je mehr du selbst weißt, desto enger die Spanne."

Renderer in `openGlossary()` um grünen `improve`-Block ergänzt (analog zu `caveat`/`example`).

## [0.9.9] — 2026-05-25

### Korrigiert — Pass-Through-Logik in Earn-Card
Adrian: „checke ob der preis pronacht so stimmt das der gast die putzfrau noch on top bezahlt das ist ein riesen unterschied. […] es gibt ja auch noch die möglichkeit die steuern für airbnb dem gast zu übertrage die dinge müssen zu 100% klar sein auch in der aufstellung klar aufgezeigt sein."

**1) Kurtaxe ist Pass-Through, nicht Kostenposten.** Bisher wurde Kurtaxe (2% von grossNights) aus dem NOI abgezogen — das war falsch. Der Gast zahlt sie separat oben drauf, der Host führt sie 1:1 an die Gemeinde ab → kein Netto-Effekt auf den Cashflow.

Fix in `compute()` und `customCompute()`:
- `noi = grossTotal − platformFee − mgmt − cleanCost − opex` (Kurtaxe NICHT abgezogen)
- Kurtaxe-Wert bleibt im return-Objekt für Anzeige

Beispiel Davos 3.5Z @ ADR 244 / Occ 67%: Cashflow vor Fix 10'206 − 847 = 9'359 → jetzt korrekt 10'206 (+847).

**2) Plattform-Gebühren-Toggle Host-only vs Split.** Neuer Toggle in der Custom-Card:
- **Host-only 14%** (Default, CH-üblich): Plattform-Gebühr komplett vom Host
- **Split 3% + 14%**: 3% Host + 14% Gast oben drauf (Airbnb-Option, in CH selten)

Davos-Beispiel: Cashflow Host-only 37'702 → Split 46'925 (+9'223 weil 11% weniger Plattform-Gebühr beim Host).

**3) MWSt-Hinweis-Banner ab CHF 100k Jahresbrutto.** Eingeblendet sowohl in den 3 Szenario-Karten als auch in der Custom-Card-Berechnung sobald `grossTotal > 100'000`. Hinweis auf 3.8% reduzierten Satz für Beherbergung + Beispiel-Betrag pro Jahr.

**4) Pass-Through visuell markiert.** Neue Sektion „↔ Durchlaufende Posten (nicht im Cashflow)" mit neutralfarbenem Background, ↔-Icon, Hinweis „Gast zahlt extra · Host führt 1:1 an Gemeinde ab". Putzgebühr/Putzkraft jetzt mit Marge-Differenz im Hint (z.B. „Marge 0 CHF" bei guestClean=cleanCost).

Custom-Card-Footer-Hinweis aktualisiert: „STR-Versicherung CHF 600 · Kurtaxe ist ↔ Pass-Through (Gast zahlt, Host führt ab — nicht im Cashflow)" — vorher lautete der Hinweis fälschlich „Kurtaxe 2% — kann der User nicht beeinflussen".

## [0.9.8] — 2026-05-25

### Hinzugefügt — Custom-Karte: einstellbare Kosten-Slider
Adrian: „es gibt dinge die fix sind die kommen so rein wie tax. Putzfrau soll auch einstellbar sein also all die dinge an denen ich etwas machen kann wie tv abo usw."

Custom-Karte um 4 zusätzliche Slider erweitert (Stellschrauben des Hosts):
- **Putzkraft pro Reinigung** (50–200 CHF, default je nach Wohnungstyp)
- **TV / Streaming / Spotify** (0–100 CHF/Mt, default 35) — neu!
- **Verbrauchsmaterial / Jahr** (500–5'000 CHF)
- **Verwaltung %** (0/5/15/25 — Self bis Full PM)

Klare Trennung im UI:
- 🎛️ **Deine Stellschrauben** (Sektion mit den 4 Slidern)
- ● **FIX** (Hinweis unten): Plattform-Gebühr 14% · Kurtaxe 2% · STR-Versicherung 600 — kann nicht geändert werden

Live-Recompute bei jedem Slider-Move. Beispiel verifiziert: TV von 35→100 CHF/Mt = +780 CHF/Jahr Kosten → Cashflow exakt um 780 niedriger.

## [0.9.7] — 2026-05-25

### Verbessert — Hero-Stats von trocken zu Catcher
Adrian: „diese info soll ein catcher sein. sie sollen einem geil darauf machen geld verdienen zu wollen."

Vorher: 4 trockene KPIs (2'413 Hotelbetriebe · 207'186 Betten · 39.1% Auslastung · 36.4M Logiernächte). Klang nach Statistik-Amt, nicht nach Geldverdienen.

Jetzt:
- **Hero-Zahl: „~10.1 Mrd CHF/Jahr Brutto"** — 5xl, rot, dominant
- 💰-Wasserzeichen im Hintergrund der Karte
- **+3.1% YoY** aus echtem Trendsetter-Durchschnitt
- 3 Sub-KPIs in Reihe: 50M Logiernächte · 23.1M Touristen-Ankünfte · 39.1% Auslastung
- Hinweis „Spitze: Zermatt 70.1%" unter Hotel-Auslastung
- **🏆 TOP-CASHFLOW-Karte** (gold-umrandet, klickbar):
  - „Gstaad · CHF 61k / Jahr / Wohnung möglich"
  - „BE · 52.7% Auslastung · RevPAR CHF 319"
  - → öffnet direkt Markt-Detail
- Marktvolumen-Berechnung: Hotel-Logiernächte × Branchen-ADR (220) + Parahotellerie-Schätzung (14M × 150)

Macht direkt Lust auf Markt-Detail-View. Klick auf TOP-CASHFLOW = einklick zum Markt.

## [0.9.6] — 2026-05-25

### Fixes — Karten-Kreisgröße nach gewählter Metrik
Adrian: „wenn ich Auslastung wähle sollte der grösste Kreis dort sein wo die Auslastung am höchsten ist".

- Korrekt — vorher war Kreis-Größe immer `m.listings`, egal welche Metrik gewählt
- Jetzt: bei „Auslastung" sind Zermatt (70%), Grindelwald (66%), Interlaken (64%) die größten Kreise
- Bei „RevPAR" sind Gstaad/Verbier/St. Moritz die größten — etc.
- Legende aktualisiert: „Kreis-Größe = gewählte Metrik (Top = größter Wert)"

### Hinzugefügt — „🎯 Exklusiv für dich"-Empfehlungs-Engine
Adrian: „cool wäre wenn du exklusiv für mich sagen kannst wo ich was haben sollte".

- **Prominenter Gold-Button** im Hero unter dem Suchfeld
- **Profil-Modal** mit 6 Achsen:
  - Setup-Budget (< 8k / 8–15k / 15–30k / 30k+)
  - Risiko-Toleranz (Konservativ / Balanced / Aggressiv)
  - Konzept-Präferenz (Business / Familie / Couple / Wellness / Sport / Mid-Term — multi-select)
  - Region (Stadt / Berge / See — multi-select)
  - Modus (Mieten / Kaufen)
  - Steuer-Sensitivität (Egal / Bevorzugt tief)
- **Scoring-Algorithmus** durchläuft alle 188 BFS-verifizierten Märkte
- **Top-5-Empfehlungen** mit Match-Score und 4 Begründungen pro Markt
- **Klick auf Empfehlung** → öffnet direkt das Markt-Detail
- Beispiel-Profil „Business + Mid-Term + Stadt + Tief-Steuer" → 🥇 Zug · 🥈 Zürich · 🥉 Genève

## [0.9.5] — 2026-05-25

### Hinzugefügt — Konfidenz-Indikator + konsistente Begriffe
Adrian: „man soll auch sagen wie genau das es ist wie du sagst plus minus 30-50% daneben. Was ich noch weiter finde die herleitung wenn sie sin mache müssen her wie auch die kürzungen das muss durchgängig sein oder du schreibst es aus was es ist wenn es sinn macht mit kürzel."

- **Konfidenz-Banner** prominent unter den Szenario-Karten:
  - „Absolute Werte ±30–50% daneben möglich"
  - 🟢 Verlässlich für relative Vergleiche, Sensitivität, Break-Even
  - 🟡 Mittel für Größenordnung
  - 🔴 Schwach für exakten Franken-Wert einer konkreten Wohnung
- **Klick auf „Konfidenz"** öffnet Glossar-Modal mit voller Methodik-Erklärung
- **Begriffe konsistent ausgeschrieben mit Kürzel-Erklärung in Klammern**:
  - „<span class='glossary-term' data-term='mgmt'>Verwaltung</span> 5%" (statt nur „Mgmt")
  - „<span class='glossary-term' data-term='nk'>Nebenkosten</span> (Strom/Wasser/Internet)" (statt nur „NK")
  - „Versicherung (<span class='glossary-term' data-term='str'>STR</span>-spezifisch)" (mit STR-Erklärung)
  - „Netto-Operating-Income (<span class='glossary-term' data-term='noi'>NOI</span>)" (vor Wohnungskosten)
  - „<span class='glossary-term' data-term='kurtaxe'>Kurtaxe</span> ~2% (wird an Gemeinde durchgeleitet)"
- **Glossar erweitert** um 5 neue Einträge: Mgmt, NK, STR, Putzgebühr, Konfidenz
- Alle Glossar-Terms in Earn-Card klickbar — Modal erklärt Definition + Formel + Beispiel

## [0.9.4] — 2026-05-25

### Hinzugefügt — Earn-Card: Custom-Szenario + Jahr/Monat-Toggle
- **4. Karte „🎛️ Eigene Berechnung"** mit zwei Slidern (ADR + Auslastung) zum Experimentieren
- Default-Werte aus „Solid"-Szenario, User kann frei anpassen
- Custom-Karte rechnet live mit allen Kosten + Mietzins durch
- **Jahr/Monat-Toggle** oben rechts neben Mietzins-Input
- Wechselt **alle 4 Karten** synchron zwischen Jahres- und Monats-Darstellung
- Vergleichszeile unter dem Cashflow zeigt jeweils die andere Periode („/Monat" wenn Jahr aktiv, „/Jahr" wenn Monat aktiv)
- Adrians Frage zur Lesart („CHF 7'484/Jahr = CHF 624/Monat?") jetzt direkt sichtbar via Toggle

## [0.9.3] — 2026-05-25

### Verbessert — Earn-Potential mit Wohnungs-Größen-Toggle
Adrian: „je nach Größe variiert das — bei einem Studio etwa 70 mit Bettwäsche und bei 2 1/2 90.– usw."

- **Toggle-Bar** über den Szenario-Karten: 1Z Studio / 2.5Z / 3.5Z / 4.5Z / 5.5Z+
- **Putzkosten** skalieren mit Wohnungsgröße (Adrians Werte): Studio 70 / 2.5Z 90 / 3.5Z 110 / 4.5Z 130 / 5.5Z+ 150 CHF pro Reinigung inkl. Bettwäsche
- **Verbrauchsmaterial** + **Strom/Wasser/Internet** skalieren ebenfalls leicht mit Größe
- **Default-Mietzins** passt sich automatisch an: Studio CHF 450 → Premium-Chalet CHF 1'500+
- **Putzgebühr-Logik**: Gast zahlt = was du an Putzfrau zahlst (Standardpraxis — wird 1:1 weitergeleitet)
- ADR + Auslastung skalieren auch mit Wohnungstyp

Beispiel Baden Studio (1Z) bei CHF 450 Miete: 4.5★ Median → +CHF 1'966 / Jahr.
Beispiel Baden Premium (5.5Z+) bei CHF 1'500 Miete: 4.5★ Median → ganz anderer Wert sichtbar.

## [0.9.2] — 2026-05-25

### Verbessert — Earn-Potential komplett überarbeitet
Adrian: „bei 45 % ausgebucht und 96.– pro Nacht verdiene ich keine 5000 — die Zahl ist so nichtssagend"

Korrekt. Probleme der alten Matrix:
- Endbeträge ohne Aufschlüsselung (woher kommen die CHF 5k?)
- Mietzins/Hypothek ignoriert (NOI fälschlich als „verdienen" verkauft)
- Putzgebühr-Logik unklar (ist die im ADR drin?)
- Zu komplex (20 Zellen ohne Erklärung)

Komplett umgebaut:
- **3 klare Szenarien** (Realistisch / Solid / Superhost) statt 5×4-Matrix
- **Stage-by-Stage-Aufschlüsselung** pro Karte: Mieteinnahmen + Putzgebühren = Brutto → minus Plattform/Mgmt/Putzkraft/Kurtaxe = NOI → minus Mietzins/Hypothek = echter Cashflow
- **Mietzins/Hypothek-Input** oben rechts — User trägt Mt.-Wert ein, alle 3 Karten rechnen live
- **Default-Mietzins** automatisch passend zum Markt (40% des STR-Brutto-Monats)
- **Putzgebühr-Klärung explizit**: Gast zahlt 80 CHF pro Aufenthalt extra (Standard Airbnb-Praxis), du zahlst Putzfrau 90 CHF
- **Monatlicher Cashflow** unter dem Jahres-Betrag (≈ CHF X/Monat) — direkt umrechenbar
- **Ampel-Farbe** auf Cashflow: grün ≥ 5k, schwarz ≥ 0, rot < 0

Baden Beispiel mit CHF 800/Mt Miete:
- 4.0★: −184 CHF/Mt (Verlust — zu teuer gemietet)
- 4.5★: +214 CHF/Mt
- 4.8★ Superhost: +624 CHF/Mt
→ User sieht sofort wo die Schmerzgrenze ist.

## [0.9.1] — 2026-05-25

### Hinzugefügt — Ad-hoc-Markt-Generierung (Jonen-Fix)
- Suche nach Ort der nicht in BFS-Datensatz ist (z.B. „Jonen"): jetzt zusätzlich zum „Vielleicht meintest du" ein gold-umrandeter Button **„📊 Analyse für [Ort] trotzdem generieren"**
- Klick → OSM Nominatim Geocoding für Lat/Lon
- Kanton wird aus Nominatim-Adresse abgeleitet
- Werte werden vom geografisch nächsten BFS-Markt übernommen (mit Abschlag auf Auslastung/RevPAR)
- Markt wird dynamisch in `markets[]` eingefügt — alle Tool-Features (Detail-View, Strategien, Brief-Generator) funktionieren
- **Alles mit 🔴 MOCK-Badge** + Banner-Hinweis welcher Referenz-Markt verwendet wurde
- Beispiel: „Jonen" → AG erkannt → Werte aus Baden (52 km Distanz) übernommen

## [0.9.0] — 2026-05-25

### Hinzugefügt — Agent-Interface (Pattern-Matching)
- Hauptsuche erkennt nun **Intents** in natürlicher Sprache, nicht nur Markt-Namen
- 11 Pattern-Familien: Familie / Cashflow / Steuer / Trend / Hidden Gem / Regulierung / Premium / Dual-Season / Mieten / Kauf / Vergleich
- „Frag mich"-Modus: tippe „wo lohnt sich Familien-STR?" → Action-Card mit Erklärung + Button öffnet direkt passende Scout-Strategie
- „wohnung in Sursee" → kombiniert mit Markt-Match → Markt-Detail-Vorschlag

### Hinzugefügt — Wohnungsfindung Phase 1
- **`js/loopholes.js`** mit rechtlichen Schlupflöchern pro Stadt (Luzern Gewerbe, Genève Mid-Term, VS/GR Bestandsobjekte vor 2012, Zürich Bestandsschutz)
- **Schlupfloch-Sektion im Markt-Detail** — zeigt CAP-Regel + Schlupfloch + Risiko-Level + worauf bei Inseraten achten
- **Brief-Generator-Modal** (✉️ Button im Markt-Detail) mit 3 Varianten:
  - Persönlich bekannte Person (Adrian's Markus-Stil)
  - Erstkontakt formell
  - Premium-Eigentümer Stabilitäts-Pitch
- Brief-Generator füllt automatisch:
  - Stadt-spezifischen Schlupfloch-Block (Luzern → Gewerbe-Argument)
  - Track-Record-Zahl (200+ Übernachtungen anpassbar)
  - Persönlicher Aufhänger (frei)
  - Wohnungs-Typ
- Aktionen: **In Zwischenablage kopieren** + **Per Email öffnen** (mailto-Link) + Live-Re-Generation
- Tracking via localStorage: wer wurde angeschrieben (`swissstr_outreach`)

### Verbessert — Konkurrenz-Analyse durch echtes Feature ersetzt
- Mock-Listings „Mountain Lodge", „Apartment Altstadt" etc. komplett raus (waren algorithmisch generiert)
- Neue Sektion **„💰 Was du wirklich verdienst — pro Wohnungs-Typ"**: Matrix 5 Zimmertypen × 4 Bewertungs-Tiers mit jährlichem Nettoertrag CHF
- Macht den Bewertungs-Hebel sichtbar: Studio Grindelwald CHF 18k bei 3.5★ → CHF 65k bei 5★

### Hinzugefügt — Lifestyle/POI-Daten (Phase 1)
- `tools/fetch_osm_pois.py` zieht POIs (Restaurants, Bars, Skilifte, Apotheken, Spielplätze, ÖV) im 1.5-km-Radius pro Markt von OpenStreetMap Overpass API
- `data/osm-pois.json` Snapshot, Resume-fähig
- Aktuelle Coverage: 36 von 81 Märkten (Rest folgt beim nächsten monatlichen Auto-Refresh)
- Markt-Detail zeigt **Lifestyle-/Familien-/Alpin-Score** (0–100) + Counts pro Kategorie

## [0.8.1] — 2026-05-25

### Hinzugefügt — Such-Strategien massiv ausführlicher
- Pro Such-Strategie-Box jetzt: Cashflow-Range CHF/Mt, Setup-Kosten, Break-Even-Monate, Hit-Rate (Anfragen → Antworten), Konkurrenz-Schätzung mit Ampel (tief/mittel/hoch)
- **Inserat-Tipps** als ausklappbares Detail (3 Bullets pro Strategie — was im Mietvertrag suchen, Lage-Kriterien, Stockwerkeigentum)
- **Verhandlungs-Tipp** pro Strategie (z.B. Studio: 20-30% Cashflow-Anteil anbieten · Premium: 3-Jahres-Vertrag mit Indexierung)
- Cashflow-Modell gefixt: Studio Grindelwald +CHF 500–800/Mt, Familie +700–1'200, Premium +1'000–1'650 (vorher fälschlich negativ)

### Verbessert — Glaubwürdigkeits-Audit Phase 1
- **„Demo buchen"-Button → „↗ Auf GitHub"** (war Lüge ohne Sales-Backend)
- **„Daten aktualisiert: vor 4 Std."** → echtes `BFS HESTA bis YYYY-MM · N Mt. alt` mit Ampel-Farbe (grün/gelb/rot)
- **Live-Ticker komplett umgebaut** — vorher 6 Mock-Aussagen (Zermatt CHF 237 +4.2% WoW etc.), jetzt aus echten BFS-Daten: Top-5 Hotel-Auslastungen, Top-3 Logiernächte, Trendsetter, BFS-Märkte-Count
- **Hero-Subtitle** ehrlich umgeschrieben: kein Wüest, kein Airbnb-Scraping erwähnt — stattdessen BFS HESTA · Investor-Calc · 8 Scout-Strategien · Tier-Transparenz
- **Hero-Chips** ehrlich: „188 BFS-verifizierte Märkte" statt „ROI mit Wüest-Daten"
- **Sprach-Buttons FR/IT/EN deaktiviert** mit Roadmap-Tooltip (waren reine Deko)
- **„14 Tage gratis testen"** → „Open Source, kostenlos nutzbar" mit GitHub-Link
- **Feature-Tabelle SwissSTR vs. AirDNA** komplett umgebaut: 3 Spalten (AirDNA / SwissSTR heute / SwissSTR Roadmap), 14 Zeilen, ehrlich wo wir führen (BFS-Integration, Rental-Arbitrage, Such-Generator) und wo AirDNA führt (Airbnb-Listing-Daten)
- **Luzern 90-Tage-Cap 312 Listings** mit 🟡 MOD-Badge markiert (Schätzung in Recherche)

### Hinzugefügt — Auto-Refresh-Pipeline
- `.github/workflows/refresh-data.yml` — läuft am 5. jedes Monats + manuell triggerbar
- Ruft `match_bfs.py` + `fetch_hesta.py` + `fetch_origins.py` automatisch ab
- Commit + push als `github-actions[bot]` wenn Daten sich geändert haben
- Datenfrische-Indikator im Header zeigt Alter live

## [0.8.0] — 2026-05-25

### Hinzugefügt — Vollständige BFS-HESTA-Coverage
- **Markt-Universum von 81 auf 197 verdoppelt** (188 BFS-verifiziert, war 72)
- Alle 186 BFS-HESTA-Gemeinden sind jetzt im Datensatz — automatisch generiert via `tools/generate_full_markets.py`
- Neue Märkte: Biel/Bienne, Burgdorf, Köniz, Olten, Sursee, Wil, Le Locle, viele weitere Agglomerationen + alpine Kleingemeinden
- Hotel-Realität jetzt umfassend: 2'413 Hotelbetriebe (war 1'625), entsprechend mehr Logiernächte / Betten / Auslastungs-Daten

### Verbessert — Ehrliche No-Match-UX in der Suche
- Wenn Ort nicht im Datensatz (z.B. „Jonen"): klare Erklärung statt nur „Keine Treffer"
- Erklärungs-Text: warum nicht drin (BFS erfasst nur Gemeinden mit Hotelbetrieben)
- 3 ähnlichste Vorschläge via Levenshtein-Distanz mit Grade-Badges
- Link zu BFS STAT-TAB für eigene Recherche

### Fixes
- `tools/match_bfs.py` und `merge_into_data_js.py` lesen jetzt `js/data.js` (vorher index.html — Refactor-Hangover seit v0.3)

## [0.7.4] — 2026-05-25

### Fixes — Chart.js Canvas-Sizing
Zwei Charts hatten den gleichen Chart.js-Sizing-Bug mit `maintainAspectRatio: false` ohne Wrapper-Div mit fixer Höhe:
- **Revenue-Verteilung** in Markt-Detail: Canvas wuchs auf 2'976 px (komplett verhauen, Bars unsichtbar gross gestreckt). Fix: Wrapper `<div style="position:relative;height:220px">`.
- **Saisonalitäts-Chart Dashboard** („Wo Sommer schlägt Winter"): Canvas auf 32'100 px. Gleicher Fix.

Beide Charts rendern jetzt korrekt in vernünftiger Höhe.

## [0.7.3] — 2026-05-25

### Verbessert — KPI-Drill mit drei Charts statt Tabelle
- **Chart 1 (bestehend):** Saisonalitäts-Linie 12 Monate
- **Chart 2 (NEU):** Bar-Chart ADR/RevPAR + Linien-Chart Auslastung pro Zimmer-Anzahl (Studio bis 5.5Z+). Macht den Trade-off sichtbar: Premium-Wohnungen erzielen höheren Preis, aber niedrigere Auslastung.
- **Chart 3 (NEU):** Bewertungs-Premium nach Sterne-Rating (3.5★ bis 5.0★). Zeigt die Hebelwirkung der Bewertung — Superhost (4.8★) bringt ~+12% ADR und +12 pp Auslastung gegenüber Markt-Ø (4.5★). 3.5★ ist die Schmerzgrenze: −20% Preis, −25 pp Auslastung.
- Tooltip-Annotations zeigen "%-vs-Markt"-Vergleich pro Bar
- Adressiert Adrians UX-Kritik: Bar-Diagramme statt Tabellen, plus die zusätzliche Bewertungs-Dimension

## [0.7.2] — 2026-05-25

### Hinzugefügt — Glossar + Distribution
- **Glossar mit Klick-Erklärungen** (`js/glossary.js`) für 18 Fachbegriffe — ADR, RevPAR, YoY, pp, CoC, Cap Rate, NOI, OpEx, Auslastung, Mietzins-Multiple, Break-Even Occupancy, 10Y Swap, Grade, Logiernächte, Kurtaxe, 90-Tage-Cap, Zweitwohnungs-Cap, Trendsetter
- Jeder Begriff hat: Definition, Formel, Beispiel, Caveat
- UI-Markup `.glossary-term` mit gestricheltem Unterstrich + ⓘ-Symbol, Klick öffnet Modal
- Markiert in: KPI-Boxen Markt-Detail, Top-Tabelle-Header, Investor-Calc-KPIs, Hero-Stats, Verdict-Block (13 Stellen)

### Verbessert — ADR/RevPAR-Klick zeigt Verteilung
- KPI-Drill für ADR/RevPAR zeigt jetzt zusätzlich zur Saisonalitäts-Kurve eine **Verteilung nach Zimmer-Anzahl** (Studio bis 5.5Z+)
- Pro Wohnungstyp: Ø-Wert + Saison-Spannweite (tief → peak)
- Adressiert Adrians Beobachtung: „81 CHF im tiefsten Monat" allein ist oberflächlich — jetzt sichtbar dass ein 1Z-Studio in Verbier im April CHF 49/Nacht kostet vs. CHF 1'761 für ein Premium-Chalet im Februar
- Multiplikatoren basieren auf Schweizer-STR-Heuristik (1Z=0.65× / 3.5Z=1.0× / 5.5Z+=1.85×)

## [0.7.1] — 2026-05-25

### Geändert — Mock-Stats raus
- **Hero-Pill** „Schweiz · 26 Kantone · 78'423 Listings" war Mock — ersetzt durch „Schweiz · 26 Kantone · 72/81 BFS-verifizierte Märkte"
- **Gesamtmarkt-KPI-Box** komplett neu: aus 4 Mock-Werten (Aktive Listings, Ø ADR, Ø Auslastung, Marktvolumen) werden 4 echte BFS-Werte:
  - **1'625 Hotelbetriebe** (Summe über 72 BFS-Märkte)
  - **154'152 Hotelbetten**
  - **Ø 44.4% Hotel-Auslastung** (letzte 12 Mt.)
  - **28.3M Logiernächte/Jahr**
- Klickbarer 🟢-BFS-Badge linkt direkt zur STAT-TAB-Quelle
- Hinweis-Text unter den KPIs: STR-Listing-Zahlen pro Markt bleiben 🟡 MOD (keine offizielle Parahotellerie-API)

## [0.7.0] — 2026-05-25

### Hinzugefügt — Echte Schweiz-Karte
- **TopoJSON-basierte CH-Karte** mit 26 Kantonsgrenzen, 22 Seen, Schweizer Außenkontur — ersetzt den stilisierten SVG-Blob.
  - Datenquelle: [swiss-maps@4.7.0](https://www.npmjs.com/package/swiss-maps) auf jsdelivr CDN, 2026-er Gemeindestand
  - `topojson-client` 3.1.0 für Decoding (CDN, ~5 KB)
  - Cosine-korrigierte Equirectangular-Projektion zentriert auf Kanton-Mittelpunkt-Lat
- **`js/coords.js`** — Lat/Lon-Koordinaten für alle 81 Märkte
- **Marker-Repositionierung** über `project(lon, lat)` statt hartcodierter x/y. Alle 81 Märkte erscheinen jetzt auf der Karte (vorher nur 22 mit x/y).
- **Click-on-Canton** triggered Slicer-Filter — Kanton-Click filtert Karte + Top-Tabelle + Scout-Strategien parallel.
- Lake-Labels für 6 wichtigste Seen (Léman, Zürichsee, Bodensee, Vierwaldstättersee, Lago Maggiore, Lago di Lugano)

## [0.6.0] — 2026-05-25

### Hinzugefügt — Power-BI-Interaktionen
- **KPI-Click-Drill (B)** — Klick auf jede KPI in Markt-Detail (RevPAR, ADR, Auslastung, Listings, Trend YoY) öffnet Modal mit Detail-Chart und Statistiken. Auslastungs-Drill zeigt monatlichen Verlauf aus 27 Monaten BFS-Daten, Listings-Drill öffnet Gäste-Mix-Donut, Trend-Drill zeigt YoY-Vergleich-Linie.
- **Multi-Markt-Vergleich (A)** — Checkbox-Spalte in Top-Tabelle, bis zu 3 Märkte zur Compare-Liste hinzufügen. Compare-Tray am unteren Bildrand zeigt Auswahl, „Vergleich öffnen"-Button startet 13-Zeilen Side-by-Side-Vergleich (Grade, RevPAR, ADR, Auslastung, BFS-Werte, Steuersatz, Trend YoY, Profil, Peak, Tier, Tags).
- **Slicer-Panel im Dashboard (C)** — Multi-Select-Filter für Grade (A/B/C/D), Profile (Winter/Sommer/Dual/Stadt/Events), Daten-Tier (BFS/MOD) und alle 26 Kantone. Filter wirkt auf Karte, Top-Tabelle und Scout-Tab-Counts gleichzeitig.
- Trend-YoY ersetzt 5. KPI in Markt-Detail (war redundant „Annual Rev" — jetzt sichtbarer Wert mit Drill)

## [0.5.0] — 2026-05-25

### Hinzugefügt — 2 neue Scout-Strategien (insgesamt 8)
- **🏦 Steuer-Arbitrage** — filtert Märkte in Tief-Steuer-Kantonen (ZG/SZ/NW/OW/AI/UR) mit RevPAR ≥ 100. Quantifiziert wie viel CHF/Jahr Steuer-Ersparnis gegenüber Genf. Datenquelle: ESTV-Jahresbericht 2024. Aktuelle Treffer: Engelberg (OW), Brunnen (SZ), Zug, Beckenried (NW).
- **📈 Trendsetter-Index** — Z-Score-Anomalie der letzten 3 Monate vs. gleicher Vorjahres-Zeitraum (YoY). BFS HESTA monatliche Logiernächte. Identifiziert „Aufsteiger" 6–12 Monate vor der Konkurrenz. Top-Treffer: Martigny +35.9%, Morges +34.9%, Rapperswil +30.7%, Sion +27.3%.
- `data/tax-rates.json` — Schnappschuss aller 26 Kantone mit marginaler Belastung, Rang, Kategorie und Begründungs-Note
- `trendscore(m)` Helper berechnet zur Laufzeit aus `m.bfs.series`
- `taxFor(m)` Helper liefert Kantons-Steuersatz mit Quellenangabe

### Fixes
- `series`-Feld wurde nicht in `m.bfs` gemerged — fehlte beim loadHesta-Mapping
- Tax-Rates jetzt Teil des async-Load-Trios (hesta + origins + tax)

## [0.4.0] — 2026-05-25

### Hinzugefügt — Mieter-Vision
- **Rental-Arbitrage-Modus** in Investor-Calc — Toggle Kauf/Mieten, eigene Inputs (Monatsmiete, Setup-Investition, Putzkosten), eigener Wasserfall mit Mietzins-Branche, eigenes Verdict-Set (Mietzins-Multiple, Break-Even-Monate)
- **Mini-Businessplan Cost-Breakdown** — sichtbare Aufschlüsselung Setup einmalig + Monatlich fix + Pro-Aufenthalt-Variable + Jahres-Roundup, mit Hinweistexten pro Posten
- **„Worauf achten"-Checkliste pro Markt** — 10 Risiko-Punkte mit Ampel-Logik (grün/gelb/rot): Untervermietungs-Klausel, Tages-Cap, Zweitwohnungs-Cap, Stockwerkeigentum, Kurtaxe, MWSt, STR-Versicherung, Brandschutz, Plattform-Compliance, Gesamt-Risiko
- **Such-Strategien-Generator** — KILLER-FEATURE: pro Markt 2–3 konkrete Such-Strategien (Studio / Familien / Premium) mit klickbaren Homegate.ch + ImmoScout24.ch-URLs, vorgefilterten Suchparametern und Copy-Button für den Such-String. Bei Cap-Märkten (Genf, Luzern) werden automatisch Alternativ-Märkte vorgeschlagen.
- `CLAUDE.md` mit projektspezifischen Arbeitsweise-Regeln (durchziehen, nicht fragen)

## [0.3.0] — 2026-05-25

### Hinzugefügt
- **Datenquellen-View** mit Live-Status-Sektion: was ist 🟢 BFS / 🟡 MOD / 🔴 MOCK, Methodik pro Scout-Strategie, klickbare BFS-Tabellen-Links
- Trennung der statischen Daten in `js/data.js` (markets[], profiles{}, cantonNames{})

### Geändert
- `index.html` von 2013 auf 1911 Zeilen geschrumpft durch Datentrennung
- README erweitert mit Stand-2026-05-25-Vermerk

## [0.2.0] — 2026-05-25

### Hinzugefügt
- **Scout-View** mit 6 algorithmischen Investment-Strategien
  - Cashflow-König (höchste Bruttorendite, ≥ 5.5%, BFS-Auslastung ≥ 60%)
  - Hidden Gem (< 350 Listings, RevPAR > 130 CHF)
  - Regulierungs-sicher (ohne 90-Tage-Cap, ohne kantonale Bremse)
  - Dual-Season (Winter + Sommer doppelt verdienen)
  - Premium Wertanlage (A-Grade in Cap-Kantonen VS/GR/BE-Resorts)
  - **Familien-Gap** — neue Strategie ohne AirDNA-Pendant: Märkte mit Familien-Nachfrage > -Angebot
- **BFS HESTA-Integration** (Bundesamt für Statistik Hotellerie-Statistik)
  - 72 von 81 Märkten verifiziert (89% Coverage)
  - Monatliche Auslastung, Logiernächte, Betten, Hotelbetriebe
  - Echte Saisonalitäts-Vektoren statt generischer Profile
  - Gäste-Herkunftsmix (Top 6 Länder pro Markt aus Tabelle 101)
- **Proof-Tier-System** auf jedem Datenwert
  - 🟢 BFS — verifiziert aus amtlicher Quelle, Quellen-Link
  - 🟡 MOD — modelliert aus echten Inputs, Methode dokumentiert
  - 🔴 MOCK — Schätzung, Quelle als Roadmap benannt
- **Datenquellen + Refresh-Tools** in `tools/`
  - `match_bfs.py` — Mapping SwissSTR-Markt ↔ BFS-Gemeinde
  - `fetch_hesta.py` — HESTA Tabelle 201 Snapshot (Angebot/Nachfrage)
  - `fetch_origins.py` — HESTA Tabelle 101 Snapshot (Herkunftsland)
- BFS-Datenstrip im Markt-Detail mit Quellen-Link zu STAT-TAB

### Geändert
- Saisonalitäts-Chart in Markt-Detail nutzt echte BFS-Monatsdaten statt generischer Profile
- Top-10-Tabelle und Suche zeigen Proof-Tier-Badges
- Cashflow-Berechnung im Scout sauberer (30% OpEx, 2.5% Zins, 25% EK, ohne `beds/(beds+1)`-Hack)

### Entfernt
- `swissstr.html` (byte-identisches Duplikat von `index.html`)

### Fixes
- Chart.js Saisonalitäts-Canvas blieb leer (Wrapper-Div mit fixer Höhe)
- `hashDelta` produzierte Float-Auslastung statt Integer
- Cashflow-Formatierung zeigte keine CHF-Prefix bei negativen Werten

## [0.1.0] — Initial

- Marktübersicht mit stilisierter CH-Karte (SVG-Blob)
- Markt-Detail mit Saisonalitäts-Chart, Revenue-Verteilung, Konkurrenz-Tabelle
- Investor-Calc mit Wasserfall + Sensitivitäts-Matrix
- Regulierungs-View (kantonale Tages-Cap-Matrix)
- Datenquellen-View (statische Übersicht)
- 81 Schweizer Orte als Mock-Datensatz
