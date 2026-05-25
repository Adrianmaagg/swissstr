# Changelog

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.
Format: [Semantic Versioning](https://semver.org/lang/de/).

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
