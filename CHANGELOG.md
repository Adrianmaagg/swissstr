# Changelog

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.
Format: [Semantic Versioning](https://semver.org/lang/de/).

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
