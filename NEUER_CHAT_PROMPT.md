# SwissSTR — Continuation-Prompt (Stand v0.9.66 · 2026-06-05)

> Copy-paste alles ab `--- BEGIN ---` in einen neuen Chat.

--- BEGIN ---

# KONTEXT
Adrian (CH, kein Dev, iPhone-first, 7 J. Airbnb-Superhost). **SwissSTR** = `C:\Users\adria\Claude\swissstr`, github `Adrianmaagg/swissstr`, live `adrianmaagg.github.io/swissstr`. Single-File `index.html` + `tools/*.py` + `data/*.json`.
**CLAUDE.md + Memory beachten:** durchziehen ohne Rückfragen, `git commit`+`push` auf `main`, de-CH/CHF, Daten-Tier 🟢BFS/🟡MOD/🔴MOCK (nie Fake-„echt"), Browser-Verify vor Commit, Commit-Format `vX.Y.Z — …`.

# WAS LÄUFT (echte Airbnb-Daten via Bright Data)
- **Tägliche Windows-Aufgabe „SwissSTR-Airbnb-Fokus" 06:00** → `tools/run_focus_daily.ps1`: scrapt Fokus-5 (Baden·Meggen·Kriens·Horw·Emmen) → `--aggregate` → `--reviews`. Token in `swissstr/.env` (`BRIGHTDATA_API_KEY`, gitignored).
- **Schichten:** Roh + Zeitreihe in OneDrive (`Claude Cowork/03_Projekte_Aktuell/SwissSTR_Daten/`, `history/airbnb/{markt}.jsonl` mit `avail_dates` pro Inserat/Tag). Serving klein in Git: `data/airbnb-competitors.json` · `-trends.json` · `-insights.json`.
- **`marketEconomics` = EINZIGE Rechen-Engine.** Auslastung = **Kalender-Belegung** (`available_dates`, nächste 90T nicht-frei) via `marketRealStats` → speist alle Profit-Zahlen. **Geo-Bucketing** per listing-`location` (neutralisiert Airbnb-Karten-Zoom-Bleed).
- **UI:** Konkurrenz-Röntgen (Markt-Detail) + **STR-Radar**-Header-Seite + Verfügbarkeits-View (frei 7/30T nach Grösse) + Review-ABSA („loben/fehlt/Dein Edge") + Buchungs-Dynamik (rechnet ab 2. Datenpunkt).
- Pipeline-Befehle: `python tools/fetch_airbnb.py --fetch|--ingest|--snapshot|--aggregate|--reviews`.

# ERSTE AUFGABE
Prüfen ob der 06:00-Lauf durchlief: `data/raw/run_focus.log` ansehen · OneDrive `history/airbnb/*.jsonl` auf 2. Datenpunkt prüfen · im **STR-Radar**-Trendblock erscheinen jetzt **gebuchte Nächte · Lead-Time · Δ Auslastung**. Falls nicht gelaufen: `powershell -ExecutionPolicy Bypass -File tools/run_focus_daily.ps1`.

# OFFENE TODOs (priorisiert)
1. **Nacht-Preis (2-Stufen-Abruf:** erst freie Tage holen, dann Preis) → ADR/RevPAR/Preis-nach-Grösse + „bestes Geschäft" in CHF. (BD liefert sonst nur Aufenthalts-Total/leer.)
2. **Amenities** (BD-Feld) speichern → Business-Fit + Konfig-Lücken.
3. **Breite Discovery** (mehr Orte → auto-Geo-Bucketing).
4. **Prognose** (BFS-Saison-Form × Airbnb-Level + Kalibrierung), sobald Zeitreihe ≥ ein paar Punkte.
5. **heimstatt** (separates Repo `Adrianmaagg/heimstatt`): iPhone-Cockpit, Homegate/ImmoScout/Flatfox Miet-Inserate (Custom-Scraper, kein fertiger BD-Collector), .env/Live-IMAP, Anschreiben-Composer.

# OPS-NOTIZEN
- PowerShell-Skripte **ASCII-only** (PS 5.1 liest ANSI → Sonderzeichen brechen Quotes).
- Ordner **„Claude Cowork" NICHT umbenennen** (App-Datei-Wurzel).
- Preview: Parent `C:\Users\adria\Claude\.claude\launch.json` hat `swissstr-verify` (Port 8766, --directory swissstr).
- Bright Data: Such/Scrape gratis 5'000/Mt · Collector $1.50/1'000 Datensätze. Token nie in Commits/Screenshots.
- AirDNA = bewusst RAUS (Adrian-Entscheid).

--- END ---
