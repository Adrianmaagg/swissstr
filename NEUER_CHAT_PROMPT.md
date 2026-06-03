# Continuation-Prompt für neuen Chat — SwissSTR v0.9.25

Copy-paste folgenden Block in den neuen Chat:

---

## SwissSTR — Continuation v0.9.25

**Repo:** github.com/Adrianmaagg/swissstr (lokal: `C:\Users\adria\Claude\swissstr`)
**Live:** Cloudflare Pages swissstr.pages.dev + GitHub Pages adrianmaagg.github.io/swissstr/
**Preview lokal:** Port 8767 via `.claude/launch.json` (Python http.server)

## Was das Tool ist

Single-File HTML SPA (~5'200 Zeilen `index.html`), Vanilla JS + Tailwind/Chart.js CDN, kein Build-Step. Daten-Snapshots in `data/*.json`, Auto-Refresh via GitHub Action am 5. jedes Monats.

197 Schweizer Märkte, 188 BFS-verifiziert via HESTA STAT-TAB. Tool ist Adrian's Daten-First-Investment-Framework für sein Rent-to-Rent STR-Geschäft.

## Adrian's harte Regeln

1. **Wir raten nicht.** Schätzungen nur mit Range (Min/Median/Max) + Konfidenz HIGH/MED/LOW + ehrlicher Quelle ("Plausibilitäts-Schätzung Branchen-Konsens" statt erfundene Studien)
2. **Daten-Tier-Pflicht:** 🟢 BFS verifiziert / 🟡 MOD modelliert / 🔴 MOCK Schätzung. Niemals mischen ohne Markierung.
3. **Reality-Check** Custom-Slider gegen BFS-Markt-Schnitt, Warn-Banner bei >30% Abweichung
4. **Adversarial verifizieren** vor Tool-Integration (siehe v0.9.25: 7/25 Behauptungen 0-3 gekillt)
5. **Durchziehen ohne Bestätigung** bei klaren Aufträgen, commit + push direkt
6. **Deutsch, knapp, konkret**, CH-Idiome (CHF, Apostroph-Tausender, de-CH)
7. **Kein Esoterik** (keine Beziehungs-/Lokal-Vorteils-Strategie). Daten-First.

## Module die im Tool sind

- KPI-Bar mit Drill-Charts (Saisonalität klickbar mit KPI-Filter)
- **Use-Case-Tags** ✈️🏢🎓🏥🎿🌊♨️👨‍👩‍👧 (deriveUseCases aus BFS+OSM+ALOS+Saisonalität)
- **STR-Liveness-Warner** mit REGULATORY_STOPS-DB (Tessin/Stadt Luzern/Davos/Klosters/Arosa/Sigriswil — verifiziert via sab.ch/Primärquellen)
- **Markt-Chancen-Scout** (EMPLOYERS-DB inkl. Villigen PSI + Dübendorf Empa/Eawag + Persona-Hotel-Vergleich + Channel-Empfehlungen)
- **Konkurrenz-Analyse** (Pareto Top-10%/Median/Bottom-30% + Channel-Map mit B2B-Direct + kuratierte Anbieter + Brave-Search-Pipeline)
- **Suburban Arbitrage** (Mutterstadt→Vororte kuratiert mit Notes) inkl. Solothurn (Balsthal/Oensingen/Dornach/Breitenbach)
- **Smart Suburb Detector** (Wikidata-basiert, autoSuburbsFor)
- **Optimierungs-Forecast** (6 Hebel mit Range/Konfidenz/Achievability, explizit als MOCK gelabelt)
- **Custom-Earn-Card** mit Markt-Basis-Reality-Check + Pass-Through (Kurtaxe) + Plattform-Toggle Host-only/Split + Setup-Presets Business/Familie/Wellness
- **Heimat-Filter** (Standort + Fahrtzeit-Radius, Notfall-Score in Top-Tabelle)
- **Daten-Health-Layer** mit _health.json + Status-Banner + Modal

## Daten-Pipelines (alle mit _health.json-Tracking)

- ✅ `tools/fetch_hesta.py` BFS HESTA monatlich
- ✅ `tools/fetch_origins.py` BFS Origins jährlich
- ✅ `tools/fetch_osm_pois.py` Overpass quartalsweise (manche Märkte mit Lücken)
- ✅ `tools/fetch_communes.py` Wikidata monatlich
- ⚠ `tools/fetch_competitors.py` Brave Search API — **Token noch nicht in GitHub Secrets gesetzt** (Setup: brave.com/search/api/ → BRAVE_SEARCH_TOKEN)

## Verifizierte Befunde aus Deep-Research v0.9.25

3-0 oder 2-1 bestätigt (Quellen: sab.ch Nov 2025, psi.ch, empa.ch, so.ch Siedlungsstrategie, are.admin.ch, sotomo.ch/ZugerKB):
- Villigen-PSI strukturelle Forscher-Lücke
- Dübendorf-Empa/Eawag ETH-Prioritäts-Engpass
- Solothurner Regionalzentren als unter-bediente Märkte
- 331 CH-Gemeinden mit >20% Zweitwohnungsanteil per 31.3.2026 (Cap aktiv)
- ARE Wohnungsinventar auf opendata.swiss als XLSX **jährlich** (nicht quartalsweise!)
- Keine zentrale CH-STR-Datenbank existiert (Bundesrat lehnt ab in Interpellation 23.3373)
- Inside Airbnb CH-Coverage = nur Vaud auf Gemeindeebene
- Sigriswil Planungszone Nov 2024 für 24 Mt → blockiert

Adversarial 0-3 widerlegt (NICHT als Wahrheit verwenden):
- Cham/Risch-Rotkreuz/Steinhausen/Hünenberg „sekundäre Zentren" (jetzt im Tool als Caveat gelabelt)
- Berner Oberland Bönigen/Brienz-Cluster
- ARE quartalsweise (eigentlich jährlich)
- Stadt Bern Kanton = AirDNA-Nutzer (nur Stadt, nicht Kanton)

## Roadmap offen (für nächste Session)

**Priorität 1 — Datenquellen die deep-research nicht verifiziert hat:**
- BFS PASTA (Parahotellerie) — Tabellen-IDs unbekannt, Pipeline `fetch_parahotellerie.py` analog fetch_hesta.py
- BFS Wohnungsleerstand — Pipeline für Mietwohnungs-Verfügbarkeit pro Gemeinde
- BFS Mietpreisindex — für Cashflow-Realismus
- ARE Wohnungsinventar (opendata.swiss XLSX) — 331 Cap-Gemeinden in Tool integrieren

**Priorität 2 — Algorithmen-Layer:**
- **Ensemble-Multi-Signal-Score** (Personal-Investment-Score 0-100 pro Markt, 12+ Signale gewichtet kombiniert, Konfidenz-Intervall aus Anzahl konsistenter Signale) — Phase 1 noch nicht gebaut. **Wunderwaffe** laut Adrian.
- **Inferenz-Engine** (multi-Variable Ableitung von STR-Occ/STR-ADR aus Hotel-Daten mit expliziten Formeln + Constraint-System + Sensitivitäts-Heatmap + Targeted-Scrape-Buttons)

**Priorität 3 — Folge-Recherche:**
- Zweite Deep-Research-Runde für PASTA-Tabellen-IDs konkret + Spital-Patienten-Familien-Bedarf außer Uni-Spitäler

**Nicht-Roadmap (entschieden):**
- AirDNA-Integration → NEIN (Adrian: "AirDNA lügt sich Sachen zusammen, mehrere Monate studiert")
- Brave-Search-Token-Setup → Adrian's manuelle Aufgabe (5 Min im GitHub)
- Mass-Scraping (Airbnb, Booking direkt) → rechtlich grau ohne robuste Health-Pipeline → NEIN
- Anschreiben-Generator im Tool → Adrian baut das in separatem Tool

## Commit-Format

```
vX.Y.Z — Kurzbeschreibung

[freie Erklärung mit technischer Substanz, ggf. Adrians Originalwortlaut]

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## Erster Schritt nach Lesen

Frag Adrian was er als nächstes will von:
- (A) Zweite Deep-Research für offene Quellen (PASTA/Leerstand/Mietpreis/Spitäler) — ~15 Min Compute
- (B) ARE Wohnungsinventar Pipeline (`fetch_zweitwohnungen.py`) bauen — Cap-Status für 331 Gemeinden im Tool sichtbar — ~4-6h Bau
- (C) Ensemble-Multi-Signal-Score MVP (Personal-Score auf Karte sortiert) — ~3-4h Bau
- (D) Inferenz-Engine prototype für 1 Markt — algorithmisch STR-Occ/ADR aus Hotel-Daten mit Konfidenz

---

## Was lokal in deinem Repo noch zu tun ist

1. `MORGEN_TODO.md` — alte Notiz vom 25.5., enthält noch GitHub Privacy + Cloudflare-Setup-TODOs. **Prüfen ob Repo schon private gemacht wurde + Cloudflare Access aufgesetzt**, dann löschen.
2. `NEUER_CHAT_PROMPT.md` (diese Datei) — nach Übergang in neuen Chat löschen.
