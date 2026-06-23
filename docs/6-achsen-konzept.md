# SwissSTR — 6-Achsen-Konzept (erarbeitet 2026-06-23)

> Achse 1 (Glaubwürdigkeit) ist abgeschlossen (Penetrationstest → `FEHLER-SAMMLUNG.md`). Für die Achsen 2–6 hat je eine fokussierte Analyse die **2–3 schärfsten Hebel** erarbeitet — konkret (Datei:Zeile), entscheidungs-kippend, Vorrat-geprüft (R2R = NUR ganze Wohnungen).
>
> **Methode je Hebel:** erarbeiten → gegenprüfen (adversarial gegen den echten Code) → umsetzen (browser-/daten-verifiziert, commit+push).
> **Status-Legende:** ⬜ erarbeitet · 🔍 gegengeprüft · ✅ umgesetzt

---

## 🏆 Quer durch alle Achsen — die 2 Kronjuwelen

Beide hängen direkt an der gerade fertigen Achse 1 — die saubere Datenbasis ist an zwei Stellen **ungeschützt**:

1. **Die „tote" Engine lebt heimlich (A6.1 + A5-Frische + Achse-1-C).** `data/market-facts.json` (Jahres-Prognose-Anker, `occ_band`/Saison) wird von `cockpit.view.js:570` **und** `akquise.view.js:285` gelesen, aber **nur** durch `window.exportMarketFacts()` im 689-KB-Legacy-`index.html` (alte `marketEconomics`-Engine) erzeugt — die CI refresht es nicht (`daily-scrape.yml`: 0 Treffer; Datei friert auf 12.06. ein). „index.html ist stillgelegt" (STATUS §4) ist faktisch falsch: das Backbone hängt dran. → Engine-Naht nach `tools/` migrieren, DANN beerdigen.

2. **Ein Kalender-Ausfall nullt still die occ (A5.1).** `compdata.py:149` schützt nur gegen „0 Inserate", nicht gegen „occ alle null". Der Kalender-Endpoint (`fetch_calendar`) fällt SEPARAT von Suche/PDP aus → recs voll, jede occ `None` → die block-bereinigte Achse-1-Auslastung wird ohne Alarm mit `null` überschrieben. → occ-Befüllungs-Guard. **[höchster Sicherheitswert, S]**

---

## Achse 2 — Entscheidungs-Nutzen
*Liefert die Seite Einsicht, die eine Entscheidung kippt — oder nur ein Readout?*

- **2.1 R2R-Spielraum als Cockpit-KPI** ⬜ — RANG 1, **S**
  LÜCKE: Die 4 KPIs (`cockpit.view.js:218-222`) sind reine Readouts; der einzige R2R-entscheidende Wert `rentHeadroomPct` (economics.js:201-216) ist 1 Klick tief pro Einzel-Inserat vergraben (`:295-310`). HEBEL: KPI „davon Superhost" (reiner Zähler) ersetzen durch „R2R-Spielraum (Median)" = wieviel % über Marktmiete bei null bleibst, farbcodiert. KIPPT: „gehe ich in diesem Markt überhaupt auf Akquise?" — bei negativem Headroom trägt der Markt KEIN R2R, egal wie hübsch die Auslastung. Engine kann es heute.
- **2.2 „Stille Perle" auf echte 30-Tage-Velocity** ⬜ — RANG 2, **S–M**
  LÜCKE: `briefing.py:169` definiert Perle über Lebenszeit-reviews + occ30≥70 (Code gibt Schwäche selbst zu, `:39`); in Weggis erfüllen **23 Inserate gleichzeitig** = Rauschen, ~15 davon `pickup.nb=0` (voller Kalender, null neue Buchung = geblockt). HEBEL: Velocity-Gate `per_listing[id].nb>0` + money_score auf `× recent_nb`. KIPPT: welchen Eigentümer Adrian morgen anschreibt („ausgebucht ≠ gebucht").
- **2.3 Kalender-Tiefe als Markt-Verdikt** ⬜ — RANG 3, **M**
  LÜCKE: `cal_longest_block_days` 100% / `min_nights` 99% befüllt, aber nur Zelltext/Filter — kein Markt-Verdikt. HEBEL: Median-min_nights + Dauerblock-Anteil je Markt → „⚠ 1-Nacht-Markt, 40% Dauerblock". KIPPT: meidet Adrian einen Markt mit hoher Schein-Auslastung (occ aus Blocks, nicht Buchungen).

## Achse 3 — Akquise-Loop
*Schließt der Loop Inserat → Deal-Dossier-Vorschlag an Adrian?*

- **3.1 Zwei Brief-Maschinen vereinen** ⬜ — RANG 1, **S**
  LÜCKE: Welt A (`dossFillPitch`, `akquise.view.js:1141` + `LETTER_TEMPLATES`, alle 5 Varianten, typ-richtig) endet im toten Clipboard (`copyLetter:644` → toter localStorage-Key); Welt B (Agent-Composer, 2 Varianten, Mock) füllt allein die Outbox/CRM. Der gute Brief erreicht den Funnel NIE. HEBEL: Button „→ in Outbox" an der Pitch-Zone → `/api/outbox/save` mit dem Dossier-Pitch. KIPPT: der belegte, typ-richtige Brief wird das versendete + nachverfolgte Artefakt (Dedup/Funnel lernen).
- **3.2 Merkliste-Handoff selektiert den Lead nicht** ⬜ — RANG 2, **S**
  LÜCKE: `briefing.html:255` `pfAkqBtn` statisch; `akqLeadBoardInit` ruft kein `akqSelectLead` → gemerkte Leads im Board, aber keiner selektiert → Dossier leer auf Default-Kriens. HEBEL: jüngsten Merkliste-Lead auto-selektieren. KIPPT: „Merken" wird ein echter Handoff bis zum gefüllten Dossier.
- **3.3 Lage-Insights nur für Kriens** ⬜ — RANG 3, **M**
  LÜCKE: `AKQ_LOCATION` (`akquise.view.js:671`) hat genau 1 Eintrag (Kriens); 29 Fokus-Seegemeinden zeigen Pauschal-Platzhalter. HEBEL: AKQ_LOCATION um die Gemeinden erweitern, in denen real Leads auftauchen (je mit Quelle, wie Kriens). KIPPT: belegte Lage-Argumente im Brief/Gespräch (kein Geldrechner allein).

## Achse 4 — Bedienbarkeit
*Findet Adrian in ≤3 Klicks, ohne „was sah ich gerade?" (Laptop-only)*

- **4.1 Horizont-Fenster bricht beim Seitenwechsel ab** ⬜ — RANG 1, **S**
  LÜCKE: start speichert `start_h`, cockpit lädt `let H='30'` hardcodiert (`cockpit.view.js:32`, liest start_h nie) und persistiert H gar nicht → jeder Markt-Wechsel resettet auf 30. HEBEL: geteilter Key `swissstr_h` (lesen+setzen in cockpit, start umstellen). KIPPT: spart Wiederhol-Klicks + verhindert, dass Adrian unbemerkt andere Zahlen liest als die, die ihn herführten (Achse-1-Bruch).
- **4.2 Cockpit kein Rückweg zur Karte + start kein Nav-Anker** ⬜ — RANG 2, **S**
  LÜCKE: einziger Rückweg = Wortmarke (`cockpit.html:234`, nicht als Button erkennbar); start.html ohne `.on`-Nav-Marker + Brand kein Link. HEBEL: „Karte" als fixer erster Nav-Eintrag überall + `← Karte`-Chip im Cockpit-Kopf. KIPPT: kein „wie zurück zur Liste?"-Raten.
- **4.3 Nav-Sets driften zwischen Seiten** ⬜ — RANG 3, **S**
  LÜCKE: `positionierung.html` nur in netzwerk-Nav; briefing-Nav-Reihenfolge weicht ab → wandernder Eintrag. HEBEL: EINE kanonische Nav-Reihenfolge in allen 5 Backbone-Dateien; positionierung aus globaler Nav raus (s. 6.3). KIPPT: Muscle-Memory statt Nav-Absuchen.

## Achse 5 — Robustheit / Betrieb
*Läuft der Scrape verlässlich, überlebt er Block/Ausfall, ohne die Achse-1-Basis still zu verderben?*

- **5.1 occ→null-Guard in compdata** ⬜ — RANG 1, **S** — *(Kronjuwel 2, s. oben)*
  HEBEL: vor dem Schreiben occ-Befüllung zählen; <30% befüllt UND letzter Stand hatte mehr → NICHT überschreiben (sys.exit). Mirror des `if not recs`-Guards, eine Achse tiefer.
- **5.2 Health-Banner blind für Airbnb-Scrape** ⬜ — RANG 2, **S–M**
  LÜCKE: `_health.json` hat keinen Airbnb-Eintrag; Banner (`index.html:7918`) rechnet nur über BFS → meldet „frisch", auch wenn alle cockpit-*.json 9 Tage alt sind (Cron-Ausfall). `update_health.py` referenziert aber fehlt. HEBEL: `daily-scrape.yml`-Marker-Schritt setzt `airbnb_scrape`-Eintrag (last_success nur bei occ-ok), NICHT in NON_CRITICAL. KIPPT: macht Cron-Ausfall sichtbar (Banner-Lebenslüge weg).
- **5.3 Cloud-IP-Block läuft grün durch** ⬜ — RANG 3, **S**
  LÜCKE: `daily-scrape.yml:37-54` hängt `|| true` an jeden Schritt, Commit `if: always()` → 0/30 Märkte frisch endet trotzdem grün. HEBEL: finaler Schritt ohne `|| true`: zählt heute-frische Märkte, 0 → `exit 1` (Lauf rot = Block-Detektor im Actions-Tab). KIPPT: Block wird maschinell ablesbar.

## Achse 6 — Fokus / Substanz
*Baut jede Zeile R2R-Substanz, oder ist es Vorrat/tote Last? (kürzen & schärfen)*

- **6.1 Tote Engine speist heimlich das Backbone** ⬜ — RANG 1, **M** — *(Kronjuwel 1, s. oben)*
  HEBEL: den vom Backbone gebrauchten Teil von `exportMarketFacts()` (occ_band + Saison) als `tools/`-Skript aus BFS/HESTA nachbauen (`build_season_proxy.py` zieht die Anker schon) + in `daily-scrape.yml` einhängen. ERST danach ist index.html ehrlich beerdigbar. KIPPT: „index.html stillgelegt?" wird von nein→ja; schließt zugleich eine Achse-1-Restwunde (occ_band aus alter Engine).
- **6.2 atlas.html wird beworben, widerspricht aber dem Backbone** ⬜ — RANG 2, **S**
  LÜCKE: 7 Live-Seiten-Footer werben „Alle 188 Märkte im Atlas →" (`start.html:159` u.a.); atlas rechnet alte Engine (`:579`), zeigt die C-Wurzel-Zahlen (Vitznau 38% vs 77% live), kein Legacy-Banner. HEBEL: die Footer-Atlas-Links entfernen (oder auf STREcon-Liste umbiegen); atlas nach 6.1 beerdigen/bannern. KIPPT: einziger beworbener Absprung aus dem sauberen Backbone in widersprechende Zahlen weg.
- **6.3 positionierung.html = SHP-Marken-Marketing, nicht Adrians Werkzeug** ⬜ — RANG 3, **S–M**
  LÜCKE: positioniert die Marke SwissHomePartner gegenüber Eigentümern (`:63/93/123`), Fremd-Nav (`:53-57`), nur von netzwerk verlinkt, STATUS §7 nennt sie selbst „überzeichnet". HEBEL: aus dem Backbone-Set lösen → in die SHP-Landing-Welt (`heimstatt/eigentuemer.html`), netzwerk-Link kappen (deckt auch 4.3). KIPPT: klärt „ist SwissSTR Adrians Cockpit oder SHPs Schaufenster?".

---

## Umsetzungs-Reihenfolge (Wert × niedriges Risiko zuerst)

1. **5.1 occ-Guard** — schützt die Achse-1-Basis, backend-only, S. *(zuerst)*
2. **4.1 Horizont-Key** + **3.2 Merkliste-Auto-Select** + **4.2/4.3 Nav** — billige, sofort spürbare Bedien-/Loop-Wins (alle S).
3. **2.1 R2R-Spielraum-KPI** + **3.1 Brief-Maschinen** — höchster Entscheidungs-/Akquise-Wert (S, aber Verhalten ändernd → vor Umsetzen adversarial gegenprüfen).
4. **6.1 Engine-Migration** — das strukturelle Kronjuwel (M, eigener sorgfältiger Zyklus); danach **6.2** atlas-Links + **6.3** positionierung.
5. **5.2/5.3** Betriebs-Sichtbarkeit, **2.2/2.3** Velocity/Kalender-Verdikt, **3.3** Lage-Insights — nachgelagert.

Jeder Hebel: Prämisse am Code gegenprüfen → umsetzen → verifizieren → commit. Stand hier nachführen (⬜→🔍→✅).
