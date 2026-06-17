# SwissSTR — STATUS (die eine Wahrheit)

> **Dies ist der EINE verbindliche Projektstand.** Bei Widerspruch mit `README.md`, `CHANGELOG.md` oder alten Docs in `docs/_legacy/` gilt **diese Datei**. Letzte Pflege: 2026-06-18 (v0.9.167).

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

1. **Deal-Konstanten zentralisieren** — Kurtaxe/Airbnb-Gebühr/Reinigung in eine Quelle (`DEFAULT_COSTS`), investor.js zieht von dort. investor.html-Kurtaxe ist heute nachweislich falsch (2 % vom Umsatz statt CHF/Nacht). + Guard-Check gegen hartcodierte Geld-Zahlen.
2. **Klartext-Sweep** — ADR/RevPAR/NOI/CoC im UI ausschreiben („Preis pro Nacht" statt „ADR"). Glossar-Markup auf die Live-Seiten (heute nur im toten index.html aktiv).
3. **Grade-Dualität auflösen** — `data.js` trägt optimistische Roh-Grades (10× A), der Cube deckelt auf 1× B. Eine Quelle festlegen.
4. **akquise-Konkurrenzzahlen** — erfundene „3 Inserate am Markt" entweder ehrlich rechnen oder als 🔴 tieren.

---

## 8. Unverhandelbare Regeln

- **Daten-Tier-Pflicht:** jeder UI-Wert trägt 🟢 BFS / 🟡 MOD / 🔴 MOCK. Nie echt + Mock ohne Markierung mischen.
- **Eine Wahrheit pro Zahl.** Keine zweite lokale Formel für dieselbe Grösse.
- **Keine erfundene Präzision.** „ausgebucht" ≠ „gebucht"; 100 % Belegung = Warnsignal, nicht Bestwert. Schätzung nur mit Range + Konfidenz + ehrlicher Quelle.
- **R2R = nur GANZE Wohnungen** (keine Zimmer/Shared).
- **Lernen an den Prämissen, nicht am Wert** (keine Prognose nachträglich „nachziehen").
- **Nachvollziehbarkeit:** bei jedem Resultat Rechenweg/Annahmen/Quellen/Grenzen zeigen.
- **Arbeitsweise:** durchziehen ohne Rückfragen; git nie mit `cd`, immer `git -C`; vor Push `git pull --rebase`; bezahlte Scrapes/Geld = pausieren bis Adrian-Entscheid.

---

## 9. Betrieb

- **Lokal starten:** `swissstr.cmd` → http://127.0.0.1:8766/start.html
- **Repo:** github.com/Adrianmaagg/swissstr (public)
- **Version:** v0.9.167 (`CHANGELOG.md` = volle Historie, `docs/` = Methodik-Specs)
- **Daten refreshen:** `tools/*.py` / Cloud via `.github/workflows/daily-scrape.yml`
