# Changelog

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.
Format: [Semantic Versioning](https://semver.org/lang/de/).

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
