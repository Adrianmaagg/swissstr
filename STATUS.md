# SwissSTR — STATUS (die eine Wahrheit)

> **Dies ist der EINE verbindliche Projektstand.** Bei Widerspruch mit `README.md`, `CHANGELOG.md` oder alten Docs in `docs/_legacy/` gilt **diese Datei**. Letzte Pflege: 2026-06-18 (v0.9.198 — **Modularisierung 5/7 durch**: theme.css/format.js/netzwerk.view.js/cohort.js/map.js zentral, alle output-neutral browser-verifiziert; offen = akquise-Split + cockpit.view, siehe §7).

---

## 1. Was das ist

Ein **Rent-to-Rent-Werkzeug für Adrian selbst**: Wohnungen mieten und als Short-Term-Rental (Airbnb) weitervermieten. Das Tool beantwortet drei Fragen — **Wo lohnt es sich? Wie belastbar sind die Zahlen? Welchen Eigentümer spreche ich an?**

Browser-only, kein Build-Step, kein Framework. Daten als statische JSON in `data/`, refresht durch Python in `tools/`. Deploy: GitHub Pages + Cloudflare.

**Es ist KEIN Investoren-/Käufer-Produkt für Dritte mehr.** (Das war die alte Identität — siehe „Tote Last".)

---

## 2. Live-Rückgrat — der echte Pfad (hier wird gebaut)

Reihenfolge = Adrians Arbeitsfluss. Alle laufen auf der neuen Geld-Engine **STREcon** (`js/economics.js`).

| Seite | Beantwortet |
|---|---|
| **start.html** | WO verdient der beste Betreiber je Gemeinde am meisten? (Einstieg, Karte) |
| **cockpit.html** | Wie tief/belastbar ist dieser eine Markt? (Wettbewerb, Geld, Note) |
| **netzwerk.html** | Wer sind die grossen Spieler, und WIE machen sie es? (Playbook) |
| **akquise.html** | Welches Mietinserat ergibt einen Deal, und was schreibe ich? |

**Einstieg = `start.html`** (Brand/Logo führt überall dorthin).

---

## 3. Werkzeuge (legitime Seitenarme)

| Seite | Rolle |
|---|---|
| **hotel.html** | BFS-HESTA-Hotellerie-Baseline (amtlich, monatlich, getrennt vom STR-Signal) |
| **regulierung.html** | Kantonale Caps / Kurtaxe / Zweitwohnung = Gesetz-Gate |
| **briefing.html** | Tages-Signale aus den Cockpit-Snapshots |
| **datenqualitaet.html** | Vertrauens-Schicht unter dem Cockpit (nur von cockpit.html verlinkt) |
| **investor.html** | KAUF-ROI-Rechner (`js/investor.js`) — anderes Geschäft als R2R-Miete, daher Werkzeug, nicht Hauptpfad |

---

## 4. Tote Last (NICHT hier weiterbauen)

Reste des alten „AirDNA für Käufer"-Produkts. Seit v0.9.167 als Legacy gebannert, Links ins Tote gekappt — aber Dateien bleiben (Deploy-Root + ein Export-Job).

| Datei | Warum noch da |
|---|---|
| **index.html** (689 KB Monolith) | Legacy-Vollversion auf alter `marketEconomics`-Engine. **Produziert noch `data/market-facts.json`**, das `atlas.html` liest → nicht löschbar, bis der Export migriert ist. Banner oben führt zu start.html. |
| **landing.html** | Marketing-Standalone (alte Käufer-Zielgruppe). Demo-Buttons zeigen jetzt auf start.html. |
| **atlas.html** | Lese-Ansicht von `market-facts.json` (rechnet nichts selbst). |

---

## 5. Engines — welche Zahl kommt woher

- **STREcon** (`js/economics.js`) = **die Live-Geld-Engine.** Brutto/Netto/Belegung/Breakeven/Mietanker. Genutzt von start/cockpit/akquise. **Regel: neue Geld-Mathe IMMER hier, nie eine zweite lokale Formel.**
- **marketEconomics** (in `index.html`) = Legacy + Export-Produzent (`market-facts.json` für atlas). Nicht für Neues nutzen.
- **investor.js** = eigener Kauf-Rechner, bewusst vom Tages-Scrape entkoppelt. **OFFEN: seine Deal-Konstanten (Kurtaxe/Airbnb-Gebühr/Reinigung) divergieren von STREcon → zentralisieren** (siehe §7).

---

## 6. Daten-Realität (was WIRKLICH belastbar ist)

- **Breite gratis & echt:** 188 BFS-verifizierte Märkte (HESTA), 108 Konkurrenz-Märkte, 645 Operatoren im Netzwerk. Tier-Markierung im Scraper-Output sauber.
- **Tiefe nur für ~28 Märkte täglich frisch** (Cloud-Scrape). Rest = letzter bekannter Stand (~9 Tage), vor einem echten Deal frisch nachziehen.
- **Cloud-Scrape fragil:** GitHub-Cron feuert 4–5,5 h zu spät, hängt an ungeschütztem öffentlichem Airbnb-Endpoint (Block jederzeit möglich). Erst seit ~2026-06-15 scharf.
- **Bezahltes Bright-Data-Gleis ist gebaut, liegt aber brach** = Reserve.
- **Health-Wächter tot** (`update_health.py` fehlt) → z. B. HESTA-Timestamp eingefroren auf 2015. Daten selbst sind aktuell, nur das Frische-Flag lügt.

---

## 7. Offene Baustellen (priorisiert, Adrian hat den Lead an Claude übertragen)

> **🔧 Detail-Fehler-Backlog: [`ABARBEITUNGSLISTE.md`](ABARBEITUNGSLISTE.md)** — 43 Fehler aus dem 5-Wege-Audit (2026-06-18). ✅ **ABGEARBEITET + re-analysiert, Endstand v0.9.191.** ~20 echte Bugs gefixt (jeder gegen den echten Code angefochten — mehrfach „Befund" als hinfällig erkannt statt blind zu fixen), Rest dokumentiert verworfen. Die Re-Analyse-Runde fand eine **Regression aus dem eigenen K11-Fix** (lead_share > 100 %) + 5 neue Bugs → alle behoben; **#1** (RevPAR data.js 155 vs Engine 72) angefochten → **kein Bug** (Engine-Belegung ist eine Review-Untergrenze, data.js bewusst entkoppelte Baseline; nur Quellen-Label ehrlicher gemacht). Siehe Re-Analyse-Abschnitt in der Liste.

### ➡️ NÄCHSTE PHASE: Modularisierung (auf jetzt verifiziertem Code)

Bugs sind durch → jetzt die **Struktur** (Adrians „klare Module, klare Schnittstellen wie es sich gehört"). Vorbild = die saubere Schicht `js/economics.js` (pure Funktionen, dokumentierte API, kein DOM/State). Das Architektur-Audit fand die grössten Duplikate quer über die HTML-Seiten:

| Duplikat | Vorkommen | Ziel-Modul |
|---|---|---|
| CHF-Formatter (Kern) | 8× | `js/format.js` (SwissFmt) ✅ |
| HTML-Escape | 7× | `js/format.js` ✅ |
| **Profi-/Operator-Definition** | **gedriftet (!)** | `js/cohort.js` (SwissCohort) ✅ — als 2 distinkte Gates aufgelöst (Track-Record vs Belegung) |
| Leaflet-Basemap | 3× | `js/map.js` (SwissMap) ✅ |
| Cockpit-Cross-Filter | 2× | `js/cockpit.view.js` ⬜ |
| CSS-Farb-Tokens | 8× | `assets/theme.css` ✅ |

> Hinweis: „Prozent-Formatter" existierte NICHT als geteilte Funktion (nur inline `+'%'` mit wechselnder Präzision) → bewusst NICHT erfunden (Vorrat-Regel). „Spacing-Tokens" gab es nicht als Variablen (nur gedriftete Inline-Literale) → nicht tokenisiert.

**Reihenfolge (inkrementell, vorher/nachher identisch, kein Big-Bang) — FORTSCHRITT:**
1. ✅ `assets/theme.css` (v0.9.194) — 13 Dark-Tokens zentral über 9 Seiten; index/landing/atlas (Tote Last) bewusst getrennt.
2. ✅ `js/format.js` SwissFmt (v0.9.195) — CHF-Kern 8× + HTML-Escape 7× zentral. Beweisbar output-neutral (empirisch: `toLocaleString('de-CH')` liefert in V8 schon den Apostroph; Äquivalenz-Batterie 0 Mismatches).
3. ✅ `js/netzwerk.view.js` (v0.9.196) — **erstes View-Modul-Muster** (338 Zeilen verbatim raus, byte-exakt); netzwerk.html 517→178 Zeilen. Vorlage für 6+7.
4. ✅ `js/cohort.js` SwissCohort (v0.9.197) — Profi-Drift gelöst. Befund: nicht 3× dieselbe Def, sondern ZWEI Fragen + eine falsche „identisch"-Behauptung in akquise. Jetzt distinkt: `isProfi` (Track-Record: vpm/hostMulti) vs `isBusyForOccBenchmark` (Belegung: occ@30≥40 & rev≥30). Äquivalenz-Batterie 8640×3 = 0 Bool-Mismatches. **⚠ OFFEN für Adrian (Produktentscheid, NICHT verändert): ob akquises Belegungs-Benchmark künftig auf das Track-Record-Gate umstellen soll.**
5. ✅ `js/map.js` SwissMap (v0.9.198) — CARTO-Basemap 3× zentral; start-Tile-Drift (subdomains/Attribution) via Override output-neutral erhalten.
6. ⬜ **akquise → `js/akquise.deal.js` + `js/akquise.agent.js`** — Split nach Deal-Dossier vs Agent (akquise = 2708 Zeilen → erst Boundary-Analyse: welche Funktionen/State gehören wohin, geteilte Deps).
7. ⬜ **cockpit → `js/cockpit.view.js`** (+ der Cross-Filter, der 2× mit akquise geteilt ist).

Jeder Schritt einzeln browser-verifiziert (Äquivalenz-Batterien bei format/cohort, computed-style/Render-Checks, 0 Konsolenfehler) + einzeln committet/gepusht.

**Refactor-Regel:** In-Code-Herleitungen/Kommentar-Blöcke MITNEHMEN, nicht strippen (§8). Jede extrahierte Funktion bleibt pure + per `node --check` geprüft.

1. **Investor-Rechner ↔ Akquise angleichen (nur Miet-Modus).** Kosten-Konstanten in investor.js sind zentralisiert (v0.9.169 `DEAL`-Block, keine Zahl geändert). **Entschieden mit Adrian (2026-06-18):** den RENT-Modus an die R2R-Realität angleichen (STREcon: 3 % Host-Gebühr, Gast trägt Kurtaxe — wie `akquise.html`), umgesetzt als **sichtbarer Filter/Toggle, Default „R2R-Betreiber", wegklickbar auf „Kauf-Investor (14 %)"** (Adrians Muster). Reserviert für Adrians tieferen Investor-Review. **Kauf-Modus bleibt eigen** (bewusst anderes Modell).
2. **Klartext-Sweep** — ADR/RevPAR/NOI/CoC im UI ausschreiben („Preis pro Nacht" statt „ADR"). Glossar-Markup auf die Live-Seiten (heute nur im toten index.html aktiv).
3. **Grade-Dualität auflösen** — `data.js` trägt optimistische Roh-Grades (10× A), der Cube deckelt auf 1× B. Eine Quelle festlegen.
4. ~~**akquise-Konkurrenzzahlen**~~ ✅ **erledigt (K9):** erfundene Inserats-Zahl raus, Badge jetzt „🔴 Konkurrenz-Schätzung: <Level>".

---

## 8. Unverhandelbare Regeln

- **Daten-Tier-Pflicht:** jeder UI-Wert trägt 🟢 BFS / 🟡 MOD / 🔴 MOCK. Nie echt + Mock ohne Markierung mischen.
- **Eine Wahrheit pro Zahl.** Keine zweite lokale Formel für dieselbe Grösse.
- **Keine erfundene Präzision.** „ausgebucht" ≠ „gebucht"; 100 % Belegung = Warnsignal, nicht Bestwert. Schätzung nur mit Range + Konfidenz + ehrlicher Quelle.
- **R2R = nur GANZE Wohnungen** (keine Zimmer/Shared).
- **Lernen an den Prämissen, nicht am Wert** (keine Prognose nachträglich „nachziehen").
- **Nachvollziehbarkeit & Herleitungen = geschützte Basis (Adrians Kernwert, viel Zeit investiert).** Bei jedem Resultat Rechenweg/Annahmen/Quellen/Grenzen zeigen. Die ausgeschriebenen Herleitungen/Methoden sind **Fundament, kein Beiwerk** — sie werden **nie wegrationalisiert oder „vereinfacht", nur erweitert/verfeinert.** Klartext im UI ändert die *Sprache*, nie die *Herleitung*. Kanonische Methodik (nicht überschreiben, nur ergänzen):
  - `docs/economics-engine.md` (Geld-Engine STREcon + Abnahmekriterien) · `docs/pricing-cockpit-methodik.md` · `docs/auslastung-methodik.md` (Belegung = immer Band) · `docs/scraper-contract.md` · `docs/akquise-dossier.md` · `docs/insight-engine.md` · `docs/fachliteratur.md` · `docs/ki-texte.md`
  - **In-Code-Herleitungen** (Kommentar-Blöcke in `js/economics.js`, `js/investor.js`, dem akquise-Dossier) zählen gleichwertig — beim Refactor mitnehmen, nicht strippen.
  - `docs/_legacy/` = **Archiv von Adrians früherem Denken/Begründungen** (u. a. die Ur-Analyse der „eine-Wahrheit"-Divergenz). Historischer Kontext — NICHT löschen, bei Bedarf Begründungen zurück in die aktiven Docs heben.
- **Arbeitsweise:** durchziehen ohne Rückfragen; git nie mit `cd`, immer `git -C`; vor Push `git pull --rebase`; bezahlte Scrapes/Geld = pausieren bis Adrian-Entscheid.

---

## 9. Betrieb

- **Lokal starten:** `swissstr.cmd` → http://127.0.0.1:8766/start.html
- **Repo:** github.com/Adrianmaagg/swissstr (public)
- **Version:** v0.9.198 (`CHANGELOG.md` = volle Historie, `docs/` = Methodik-Specs)
- **Daten refreshen:** `tools/*.py` / Cloud via `.github/workflows/daily-scrape.yml`
