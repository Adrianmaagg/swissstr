# SwissSTR — STATUS (die eine Wahrheit)

> **Dies ist der EINE verbindliche Projektstand.** Bei Widerspruch mit `README.md`, `CHANGELOG.md` oder alten Docs in `docs/_legacy/` gilt **diese Datei**. Letzte Pflege: 2026-06-19 (v0.9.211 — **Modularisierung 7/7 + Kapselung Stufe 2** (View-Module IIFE, akquise gemergt) **+ Daten-Vertrauen/Dogfood/Konkurrenz**: Frische-Ampel ehrlich, HESTA-2015-Lüge weg, InsideAirbnb-Kalibrierung sichtbar (Profi-Konkurrenz-Blindstelle), 2 Dogfood-Bugs gefixt. Alles browser-verifiziert. Offen: 3-Kohorten-Divergenz + positionierung-Schärfung, siehe §7).

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

### ✅ PHASE DURCH: Modularisierung (7/7, auf verifiziertem Code, output-neutral)

Bugs sind durch → jetzt die **Struktur** (Adrians „klare Module, klare Schnittstellen wie es sich gehört"). Vorbild = die saubere Schicht `js/economics.js` (pure Funktionen, dokumentierte API, kein DOM/State). Das Architektur-Audit fand die grössten Duplikate quer über die HTML-Seiten:

| Duplikat | Vorkommen | Ziel-Modul |
|---|---|---|
| CHF-Formatter (Kern) | 8× | `js/format.js` (SwissFmt) ✅ |
| HTML-Escape | 7× | `js/format.js` ✅ |
| **Profi-/Operator-Definition** | **gedriftet (!)** | `js/cohort.js` (SwissCohort) ✅ — als 2 distinkte Gates aufgelöst (Track-Record vs Belegung) |
| Leaflet-Basemap | 3× | `js/map.js` (SwissMap) ✅ |
| Cockpit-Cross-Filter | 2× (adaptiert) | gekapselt in `cockpit.view.js` bzw. `akquise.view.js` ✅ — bewusst getrennt (andere Datenquelle/Gate), kein gemeinsames Modul |
| CSS-Farb-Tokens | 8× | `assets/theme.css` ✅ |

> Hinweis: „Prozent-Formatter" existierte NICHT als geteilte Funktion (nur inline `+'%'` mit wechselnder Präzision) → bewusst NICHT erfunden (Vorrat-Regel). „Spacing-Tokens" gab es nicht als Variablen (nur gedriftete Inline-Literale) → nicht tokenisiert.

**Reihenfolge (inkrementell, vorher/nachher identisch, kein Big-Bang) — FORTSCHRITT:**
1. ✅ `assets/theme.css` (v0.9.194) — 13 Dark-Tokens zentral über 9 Seiten; index/landing/atlas (Tote Last) bewusst getrennt.
2. ✅ `js/format.js` SwissFmt (v0.9.195) — CHF-Kern 8× + HTML-Escape 7× zentral. Beweisbar output-neutral (empirisch: `toLocaleString('de-CH')` liefert in V8 schon den Apostroph; Äquivalenz-Batterie 0 Mismatches).
3. ✅ `js/netzwerk.view.js` (v0.9.196) — **erstes View-Modul-Muster** (338 Zeilen verbatim raus, byte-exakt); netzwerk.html 517→178 Zeilen. Vorlage für 6+7.
4. ✅ `js/cohort.js` SwissCohort (v0.9.197) — Profi-Drift gelöst. Befund: nicht 3× dieselbe Def, sondern ZWEI Fragen + eine falsche „identisch"-Behauptung in akquise. Jetzt distinkt: `isProfi` (Track-Record: vpm/hostMulti) vs `isBusyForOccBenchmark` (Belegung: occ@30≥40 & rev≥30). Äquivalenz-Batterie 8640×3 = 0 Bool-Mismatches. **⚠ OFFEN für Adrian (Produktentscheid, NICHT verändert): ob akquises Belegungs-Benchmark künftig auf das Track-Record-Gate umstellen soll.**
5. ✅ `js/map.js` SwissMap (v0.9.198) — CARTO-Basemap 3× zentral; start-Tile-Drift (subdomains/Attribution) via Override output-neutral erhalten.
6. ✅ **akquise → `js/akquise.deal.js` + `js/akquise.agent.js`** (v0.9.200) — Split nach Concern an der HEIMSTATT-AGENT-Naht: deal.js (1252 Z.) = Dossier-Engine, agent.js (773 Z.) = Loop + Orchestrierung + Boot. Abhängigkeit agent→deal (deal lädt zuerst). akquise.html 2706→681 Z. Beide Module geparst (`new Function`) + Render + Cross-Modul-Aufruf (Lead-Urteil→dossOffer) verifiziert. **→ In Stufe 2 (v0.9.206) wieder zu `js/akquise.view.js` gemergt + gekapselt; deal/agent waren nicht wirklich trennbar (geteilter State).**
7. ✅ **cockpit → `js/cockpit.view.js`** (v0.9.201) — 511 Z. verbatim raus, cockpit.html 826→314 Z. Cross-Filter-Befund: cockpit (DATA.listings/isProfi) und akquises portierte Variante (AKQ_COCKPIT_OCC/isBusyForOccBenchmark) sind ADAPTIERT, nicht identisch → bewusst getrennt (gemeinsames Modul wäre verhaltens-riskant auf 2 Live-Flächen).

**✅ ALLE 7 DURCH (v0.9.194–201, gepusht).** Die Live-Seiten sind jetzt Markup + Includes. Jeder Schritt einzeln browser-verifiziert (Äquivalenz-Batterien bei format/cohort, computed-style/Render-Checks, 0 Konsolenfehler) + einzeln committet/gepusht.

#### ✅ Stufe 2: View-Module GEKAPSELT (v0.9.204–206, gepusht)
Stufe 1 war nur **Externalisierung** (eigene Datei, aber Funktionen weiter global = Knoten nur umgezogen). Stufe 2 = echte **Wand**: jedes View-Modul in eine IIFE → kein interner Name leakt mehr global. Je Modul verifiziert (interne Namen jetzt `undefined` auf window, ALLE Interaktionen durchgeklickt, 0 Konsolenfehler):
- ✅ `js/netzwerk.view.js` (v0.9.204) — IIFE, 0 Exporte (keine Inline-onclick); render/boot/opCard/NET jetzt privat.
- ✅ `js/cockpit.view.js` (v0.9.205) — IIFE, 0 Exporte; render/load/barChart/pass/isProfi jetzt privat.
- ✅ `js/akquise.view.js` (v0.9.206) — **deal.js + agent.js WIEDER ZU EINEM Modul gemergt + gekapselt.** Befund: die beiden waren nie trennbar (geteilter veränderlicher State `_dossPitchVariant`/`AKQWORK`, bidirektionale Aufrufe; vor Schritt 6 = EIN Inline-Skript) → getrennte IIFEs hätten desynchronisiert. EINE IIFE = Verhalten exakt wie das bewährte alte Inline-Skript, nur dicht. Öffentliche API = genau die **18 Handler**, die Inline-/generierte onclick brauchen; ~120 interne Funktionen + State jetzt privat. (Schritt-6-Split damit bewusst korrigiert — die „2 Concerns" sind ein gekoppeltes Modul.)

**Module final (7):** `assets/theme.css` + `js/{format,cohort,map,netzwerk.view,cockpit.view,akquise.view}.js`. View-Module echt gekapselt (Wand + benannte Schnittstelle), Helfer (SwissFmt/Cohort/Map) ohnehin namespaced.

**Bewusst offen (Produktentscheide, NICHT autonom gefällt):** (a) akquise-Belegungs-Gate vs Track-Record (Schritt 4); (b) gemeinsames Cross-Filter-Modul für cockpit + akquise.view (heute getrennt, adaptiert).

**Refactor-Regel:** In-Code-Herleitungen/Kommentar-Blöcke MITNEHMEN, nicht strippen (§8). Jede extrahierte Funktion bleibt pure. (Syntax-Gate: `node` war nicht installiert → stattdessen `new Function(src)`-Parse + Browser-Load.)

1. **Investor-Rechner ↔ Akquise angleichen (nur Miet-Modus).** Kosten-Konstanten in investor.js sind zentralisiert (v0.9.169 `DEAL`-Block, keine Zahl geändert). **Entschieden mit Adrian (2026-06-18):** den RENT-Modus an die R2R-Realität angleichen (STREcon: 3 % Host-Gebühr, Gast trägt Kurtaxe — wie `akquise.html`), umgesetzt als **sichtbarer Filter/Toggle, Default „R2R-Betreiber", wegklickbar auf „Kauf-Investor (14 %)"** (Adrians Muster). Reserviert für Adrians tieferen Investor-Review. **Kauf-Modus bleibt eigen** (bewusst anderes Modell).
2. **Klartext-Sweep** — ADR/RevPAR/NOI/CoC im UI ausschreiben („Preis pro Nacht" statt „ADR"). Glossar-Markup auf die Live-Seiten (heute nur im toten index.html aktiv).
3. **Grade-Dualität auflösen** — `data.js` trägt optimistische Roh-Grades (10× A), der Cube deckelt auf 1× B. Eine Quelle festlegen.
4. ~~**akquise-Konkurrenzzahlen**~~ ✅ **erledigt (K9):** erfundene Inserats-Zahl raus, Badge jetzt „🔴 Konkurrenz-Schätzung: <Level>".

### 🔬 Aufgedeckt im Dogfood/Konkurrenz-Lauf (2026-06-19, v0.9.208–211) — ✅ behoben + ⚠ offen

- ✅ **#1 Daten-Frische ehrlich** (v0.9.208): `SwissFmt.freshness` = Ampel auf cockpit/start/datenqualitaet; HESTA-fetched_at-Lüge 2015→2026-05-25 + `fetch_hesta.py`-Quelle.
- ✅ **#4 Kalibrierung sichtbar** (v0.9.209): InsideAirbnb-Quervergleich als „Methoden-Vertrauen"-Panel auf datenqualitaet. Befund: **Free-Scrape sieht keine Host-Daten → Profi-Konkurrenz wir 0 % vs real 61 %** (auf netzwerk als Untergrenze sichtbar, v0.9.211). Echte P&L-Kalibrierung steht aus.
- ✅ **Dogfood-Bugs** (v0.9.210): cockpit „occ_band-Floor 38.2–null %"→„ab 38.2 %"; netzwerk earnPill „≈ CHF 0/Mt" ausgeblendet (est rundet auf 0).
- ⚠ **OFFEN — Urteils-Frage für Adrian: 3 divergente Markt-Schlagzeilen.** Derselbe Markt zeigt über die Seiten verschiedene Belegung/Preis (Vitznau: start 63 %/286, cockpit 71 %/236, akquise 60 %/331), weil **3 Kohorten** (alle / Track-Record-Profi / Belegungs-Benchmark — vgl. cohort.js-Gates). Je verteidbar, aber unversöhnt + unbeschriftet = Glaubwürdigkeits-Lücke. **Optionen:** EINE Kohorte kanonisch ODER jede Zahl mit ihrer Kohorte beschriften.
- ⚠ **OFFEN — positionierung.html (Adrians Strategie, NICHT autonom verändert):** die „Garantiemiete-Lücke" ist überzeichnet — Zwischennutzung (Sharedlock) + Master-Lease (Limehome) besetzen die Festmiete-Achse bereits; SHP-Edge = **lokal + datenbelegt**, nicht ein leeres Eck. Zudem ruht die Platzierung auf dem (bekannt unvollständigen) Konkurrenzbild.

### 📌 Adrians Themen-Queue (2026-06-19 — „eins nach dem andern", nicht vergessen)

1. ✅ **3-Kohorten-Divergenz aufgelöst** (v0.9.215–216, mit Adrian-OK). `SwissCohort.marketHeadline` = Median@30 der Profi-Kohorte = EINE Wahrheit; start + cockpit zeigen jetzt identisch (Vitznau **77 %/CHF 236**), cockpit Mittelwert→Median (bleibt filter-reaktiv), akquise bleibt objekt-spezifisch (beschriftet). + erster **„woher?"-Beleg**: start „Profi-Median (N)" + Hover, cockpit-KPI-Title (Brille 2/Skeptiker).
2. **Datenqualität-Tiefe** — wie gut ist die erzeugte Datenqualität wirklich (über das Trust-Panel hinaus prüfen).
3. **Scrape-Notfallszenario** — wenn der Free-Scrape aussetzt: **B (kurzfristig) = Daten von Bright Data** (Gleis ist gebaut, liegt brach) · **C (langfristig) = neues Setup**. Resilienz-Plan.
4. **Methodik sichtbar („wie wird das belegt?")** — erster Beleg an der Markt-Schlagzeile gesetzt (v0.9.216). **Offen: voller expandierbarer „woher?"-Layer pro Signal** (Klartext-Satz + Formel/Stichprobe/Tier/Grenze auf Klick). Herleitung existiert in Code/Docs → Wiring. **+ Multi-Brillen-Dogfood** (Eigentümer/Jurist/Zahlen-Prüfer aus `docs/review-brillen.md` systematisch anwenden — bisher nur Skeptiker gelaufen).
5. **Positionierung erweitern** — nicht nur R2R-Betriebsmodelle, sondern auch **Tools/Daten-Anbieter (AirDNA u. a.)** in die Platzierung aufnehmen.

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
- **Version:** v0.9.216 (`CHANGELOG.md` = volle Historie, `docs/` = Methodik-Specs · `docs/review-brillen.md` = Review-Personas)
- **Daten refreshen:** `tools/*.py` / Cloud via `.github/workflows/daily-scrape.yml`
