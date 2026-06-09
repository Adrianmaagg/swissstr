# Arbeitsweise für dieses Projekt

## Default: durchziehen, nicht fragen

Adrian (der Owner dieses Repos) arbeitet primär am iPhone und will autonomes Durchziehen, keine Mikro-Bestätigungen. Wenn er eine Vision beschreibt oder einen Multi-Step-Plan freigibt:

1. **Wähle selbst** die sinnvollste Reihenfolge der Schritte
2. **Kommuniziere die Wahl** in ≤1 Satz („Mache erst X weil Y, dann Z")
3. **Ziehe durch** — inkl. `git commit` und `git push` auf `main`
4. Liefere am Ende **EINEN Sammel-Status** mit verifizierten Resultaten

Mehrere gleichwertige Optionen sind kein Grund zu fragen — wähle die offensichtlich wertvollste, sag warum, los. Adrian redirektiert mit einem Wort wenn nötig.

**Nur pausieren bei:**
- Destruktive Ops (`git push --force`, `branch -D`, `reset --hard`, irreversible Deletes)
- Echte Geldausgabe oder Lizenz-Verträge
- Adrian sagt explizit „warte" / „nicht"

**Nicht pausieren bei:**
- Welcher Task zuerst
- HTML/CSS-Detail-Entscheidungen
- Commit-Zeitpunkt
- Refactor-Vorschläge
- Welche von mehreren gleichwertigen Sub-Strategien

## Wenn echte Wahl unvermeidbar ist

Stelle EINE Frage mit klarer Default-Option markiert. Wenn keine Antwort kommt nach Klärung anderer Punkte: nimm den Default.

## Sprache und Tonfall

- Deutsch, knapp, konkret
- CH-Idiome (CHF, Apostroph-Tausender, de-CH Locale)
- Keine Floskeln, keine Mutmaßungen über Adrians Zustand
- Keine Bestätigungs-Pingpongs („gut, jetzt mache ich …" — einfach machen)

## Technische Conventions

- Single-File HTML SPA bleibt — kein Build-Step
- CDN-Dependencies erlaubt (Tailwind, Chart.js)
- Daten als statische JSON in `data/`, refresht via `tools/*.py`
- Charts immer `destroy()` + `re-create`
- Browser-Verify vor Commit via Preview-Server
- Commit-Format: Erste Zeile = `vX.Y.Z — Kurzbeschreibung`, dann freie Erklärung, dann `Co-Authored-By: Claude...`

## Daten-Transparenz ist Pflicht

Jeder Wert im UI hat einen Tier-Badge:
- 🟢 **BFS** — verifiziert aus amtlicher Quelle, Quellen-Link
- 🟡 **MOD** — modelliert aus echten Inputs, Methode dokumentiert
- 🔴 **MOCK** — Schätzung, Roadmap-Quelle benannt

Niemals echte Daten und Mock vermischen ohne Tier-Markierung.

## Cube-Assistent v1 — Architektur (dauerhaft so halten)

Maßgebliche Quelle = der Kommentar-Block `CUBE GOVERNANCE ASSISTANT — ARCHITEKTUR` in `index.html`. Schichten (Reihenfolge: Daten → Evidence → Trust → Economics → Strategy):
**Evidence Cube** (Datenintegrität VOR Trust, `calculateOverallEvidenceIntegrity` — 9 Aspekte: Geo-Bleed/Objektart/Saison/Kalender/Host/Qualität/Stay-Length/Preis-Norm/Marktgrenze; rechnet keine Ökonomik, deckelt nur Trust: priceEvidence→Price, demandEvidence→Demand) · **Cube** (operative Rechenwahrheit, `marketEconomics`) · **Raw/Drift** (Rohwerte bleiben Evidenz, `classifyDrift` Low/Medium/High/Critical, Critical ADR/RevPAR deckelt Economics) · **Trust nach Aussageart** (Demand/Price/Economics=min, Gates je Aspekt — schwache Preisbasis entwertet Nachfrage NICHT) · **Pearl** (Kausalität) · **Kahneman** (Bias/Noise) · **Strategy/OODA** (Informationsgewinnungs-Queue + Scraper-Brief aus stärkstem Trust-Engpass) · **Geo-Bleed** (`geoBleed`: Listings im Zielmarkt? Critical → Price-Cap + Radius-Brief) · **Kalender** (`calendarSignal`: occ_method calendar vs reviews).

**Regeln (nicht regredieren):** Trust IMMER aspekt-getrennt; hohe n_preise heiligt keinen unplausiblen/fremdörtlichen Wert (Geo-Bleed/unanchored); Critical Drift blockiert starke Ökonomik; UI beantwortet ZUERST „Was verdient man?"; Scraper-Briefs aus Trust/Geo/Kalender, keine generischen To-dos; Hotel-Baseline (BFS) ≠ STR-Signal (Airbnb) getrennt halten.

**Offen für v1.1:** Geo-Center-Abdeckung erweitern (COMMUNES refreshen statt kuratierter `_MARKET_CENTERS`), Geo-Filter direkt im Scraper (`fetch_airbnb_free.py` blutet bei Namenskollision — Genève→Kentucky, Wädenswil→Kanada), Kalender-Bias-Prüfung (blockierte Eigenbelegung), `redrawEarn` auf `strUnitEconomics` umstellen, Forward-Log/Kalibrierung.
