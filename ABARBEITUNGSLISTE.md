# SwissSTR — Abarbeitungsliste (Detail-Fehler)

> Erstellt 2026-06-18 (Opus) aus einem 5-Wege-Audit aller Live-Seiten + Daten. Methode: angezeigte Werte gegen die Rohdaten nachgerechnet, Links geprüft, gegen die Projekt-Regeln (Tier-Pflicht, occ=Band, eine Wahrheit, keine erfundenen Zahlen) gehalten. Jeder Punkt ist Datei:Zeile-belegt.
>
> **Datenhinweis:** `operator-network.json` wird von Parallel-Läufen neu gebaut — Zahlen vor dem Fix am aktuellen Stand gegenprüfen. Die Operator-Portfolio-Entdopplung (gleiches Inserat in 2 Märkten im *eigenen* Portfolio) ist inzwischen **erledigt** (0 Doubletten); offen ist die **Markt-Pool**-Entdopplung (siehe K11).

## Gemeinsame Wurzeln (ein Fix → mehrere Fehler)

- **W-A · Kurzfenster-Belegung (occ@30/occ@3) wird gekrönt** statt occ@90/Jahresschnitt → **K3, K4** (+ Umsatz seitenweit). Verstößt gegen die eigene Regel „100 % = Warnsignal, kein Kurzfenster krönen".
- **W-B · Kauf-Kostenkonstanten laufen im Miet-Modus** (investor) → **K10, M13, M14, M15**.
- **W-C · drei parallele Ertrags-Engines in akquise** (cfEst 55 % / dossOffer Live-occ+Modell-Preis / dossMoney Live) → **K6, K7, M24**.
- **W-D · Markt-Pool nicht entdoppelt** (netzwerk) → **K11** (+ alle Abdeckungs-/Dominanz-Zahlen).
- **W-E · erfundene / un-getierte Zahlen** → **K9, M18, M26**.
- **W-F · datenqualitaet-Aspekte konstant 100 %** → **K2, M27**.
- **W-G · Grade-Dualität data.js (10× A) vs Cube (0× A)** → **M16**.

---

## Challenge-Runde (2026-06-18) — jeder Befund gegen den echten Code angefochten

> Adrians Regel: nur ändern, wenn im Code wirklich ein *Überlegungsfehler* steckt. Sonst war *der Befund* der Fehler. Ergebnis der 12 🔴:

- ✅ **BESTÄTIGT (fixen):** **K1** (MWSt 7.7→8.1/3.8 = Fakt · *erledigt v0.9.174*), **K2** (datenqualitaet „Reviews vs. Kalender" misst nur Kalender-Präsenz = immer 100 %, Label log → umbenannt · *erledigt v0.9.174*), **K9** (compEst-Zahl ohne Tier → Fake-Zahl raus, 🔴-Marker · *erledigt v0.9.175*), **K10** (investor Rent-Sensitivität nutzt Kauf-Konstanten), **K11** (Markt-Pool-Dedup → in-Gemeinde-Filter, Meggen 41→13/Dominanz 29→100 % · *erledigt v0.9.175*). **K8** (Homegate: `'2.5'.replace('.','')`→`'25'` = „25 Zimmer" — Bug real; Homegate-Query-Format vor Fix verifizieren).
- 🔁 **REFRAMED (real, aber NICHT der naive Fix):** **K6** (dossOffer nutzt Modell-Preis ABSICHTLICH als Schutz gegen den dokumentierten „14k-Bug" — nicht naiv Live-Preis; nur die Guard zwischen dossOffer/dossMoney teilen), **K3** (Briefing occ@30 ist legitim fürs Folgemonats-Brutto — NICHT auf occ@90 wechseln; nur „unbewiesen"-Flag bei occ@90 ≪ occ@30 + ≤5 Bew), **K4** (Default-Fenster = 30 = ok; occ@3-Krönung nur bei bewusster 3-T-Wahl → ⚪ Label „hochgerechnet aus {H}T").
- ❌ **HINFÄLLIG (mein Befund war der Fehler — NICHT ändern):** **K5** (Profi-Gate `hostMulti` ist Adrians dokumentierte bewusste Regel: Lebenszeit-vpm verwässert skalierende Profis wie Kenana → der „Fix" hätte das zerstört), **K7** (cfEst-Strategiekarten = GENERISCHE Such-Vorschläge → Markt-Baseline-occ ist korrekt, kein Live-Objekt), **K12** (Deal-Score = Eigentümer-Ja-Wahrscheinlichkeit, Headroom = Wirtschaftlichkeit = zwei Achsen, kein Rechen-Widerspruch).

> Die 🟡/⚪ unten werden beim Anfassen genauso einzeln angefochten.

## 🔴 Kritisch (falsche Zahlen / Glaubwürdigkeit / kundensichtbar)

- [ ] **K1 · MWSt-Satz faktisch falsch** — `regulierung.html:106` zeigt „MWSt 7.7 %". Seit 2024-01-01 ist der Normalsatz **8.1 %**, der Sondersatz Beherbergung **3.8 %**. Seit ~2,5 J. falsch. *(1-Zeilen-Fix)*
- [ ] **K2 · Datenqualität „Reviews vs. Kalender" immer 100 % „stark"** — `datenqualitaet.html:139` (`cal_occ_raw_pct` ist IMMER gesetzt → 100 % in allen 29 Märkten). Falscher Trust-Booster, schönt den Gesamt-Score. → echt rechnen oder Aspekt streichen. *(gleiche Klasse wie der gefixte :131-Bug)*
- [ ] **K3 · Briefing „Top-Verdiener" krönt Kurzfenster-Spitzen** — `tools/briefing.py:58-64,167`. Spirit Apartments Emmen Rang 3 mit **34'008/Mt** bei occ30=40 %, **occ90=13 %**, 5 Bew. `price×occ30×30` ist Fiktion. → occ90 bzw. min(occ30,occ90) + Stabilitäts-Gate. **(W-A)**
- [ ] **K4 · Startseite „Spitzenverdiener"-Krone + Kohorte von 100 %-Kurzfenster gekapert** — `start.html:233-237`. Bei Fenster=3 T wird occ@3=100 % annualisiert: Lukas **158'775/J** (occ@30 ergibt 8'744/Mt; occ@90=42 %). Kohorte „≥40k/J": Baden **2 (@3) vs 0 (@30)**. Label „≥40k/**Jahr**" aus 3-Tage-Fenster. → Ranking/Kohorte hart auf 30 T, der Fenster-Schalter ändert nur die Anzeige. **(W-A)**
- [ ] **K5 · Profi-Gate ausgehebelt** — `start.html:206-207`, `cockpit.html:318-320`. Der ODER-Zweig `hostMulti` lässt jeden Mehrfach-Betreiber durch, egal wie tot der Kalender: **12 von 18 „verifizierten" in Kriens haben vpm < 2** (Ray 0.36, occ@90=6 %). Button-Label „≥2 Bew/Mt" ist für die Mehrheit unwahr. → Multi-Zweig an Mindest-Velocity koppeln + Label ehrlich.
- [ ] **K6 · akquise: Lead-Board ≠ Geld-Panel für dasselbe Objekt** — `akquise.html:1326-1361` (`dossOffer`) vs `:1428-1446` (`dossMoney`). Kriens: Lead-Board rechnet mit Modell-Nachtpreis **136**, Geld-Panel mit Live **200** → ~32 % auseinander. → `dossOffer` denselben Preis-Vorrang ziehen. **(W-C)**
- [ ] **K7 · akquise: Strategie-Karten rechnen mit statischer occ 55 % statt Live 77 %** — `akquise.html:999-1033` (`cfEst` nutzt `m.occ`). Unterschätzt jeden Live-Markt → zu billige `maxRent`-Budgets (Adrian sucht zu günstig). → über STREcon/Live-occ. **(W-C)**
- [x] **K8 · akquise: Homegate-Such-Links kaputt** — `homegateUrl`: alter Pfad `mieten/wohnung/kanton-X/zimmer-25-35/preis-bis-Y` (Band „25-35" = „25–35 Zimmer", + deutsche Kanton-Slugs auch veraltet). *(erledigt v0.9.177: per Websuche verifiziertes Format `rent/apartment/canton-<slug>/matching-list?ac=<von>&ad=<bis>`; Slugs auf Homegate-Form korrigiert (lucerne/geneva/stgallen/…); Preis-Param ehrlich weggelassen, da nicht stabil verifizierbar.)*
- [ ] **K9 · akquise: erfundene Konkurrenz-Zahl ohne Tier-Badge** — `akquise.html:1034-1043` → `:1118`. „~X Inserate · Konkurrenz tief/mittel/hoch" aus Magic-Konstanten (`typeShare`×0.08), als gemessen getarnt. → echt zählen (Cockpit) oder 🔴 MOCK kennzeichnen. **(W-E)**
- [ ] **K10 · investor: Rent-Sensitivitäts-Tabelle unbrauchbar** — `js/investor.js:222-228`. Nutzt im Miet-Modus die **Kauf**-Konstanten (8 % Reinigung) + **Kauf**-CoC-Schwellen → jede Zelle tiefgrün (540 % CoC). → Rent-eigener Block + Rent-Schwellen (oder auf „Annual Cashflow"/„Multiple" umstellen). **(W-B)**
- [ ] **K11 · netzwerk: Markt-Pools nicht entdoppelt → Abdeckung + „Profi-Dominanz" verzerrt** — `tools/build_operator_network.py:64-98`. Emmen Abdeckung **104** vs real entdoppelt **31** (3,3×); Meggen 41 vs 14. `lead_share` (Profi-Dominanz) dadurch 2-3× zu tief (Meggen 29 % statt ~86 %). → `market_pool` per Inserat-ID (in-Gemeinde bevorzugt) entdoppeln + host-lose Inserate aus dem Lead-Nenner nehmen. **(W-D)**
- [ ] **K12 · akquise: Deal-Score widerspricht der Wirtschaftlichkeit** — `akquise.html:1363-1381` vs `:1469-1483`. Score nur aus Objekt-Flags → „grüner Deal" möglich trotz **−12 % R2R-Spielraum** direkt darunter. → Headroom als Score-Treiber ODER sichtbare Klammer „Score = Eigentümer-Ja-Wahrscheinlichkeit, nicht Wirtschaftlichkeit".

## 🟡 Mittel

- [ ] **M13 · investor: Rent „Netto-Ertrag" = NOI VOR Miete** — `js/investor.js:174`. Zeigt 58'336, echter Cashflow 36'736 (+21'600 = ganze Jahresmiete zu hoch). → `annualCash` oder Label „NOI (vor Miete)". **(W-B)**
- [ ] **M14 · investor: Rent-Break-Even-Occupancy mit Kauf-Nenner** — `js/investor.js:250-251` (8 %-Reinigungsterm). **(W-B)**
- [ ] **M15 · investor: Rent-„Multiple" auf Brutto statt Netto** — `js/investor.js:169` (`gross/12/rent`); Verdikt-Schwellen werten Brutto. → Netto-Monat. **(W-B)**
- [ ] **M16 · investor ↔ atlas: widersprüchlicher Grade** — `js/investor.js:271` liest `m.grade` (data.js, optimistisch) → „Premium-Markt mit Supply-Lock" für Zermatt/Verbier/Andermatt/Saas-Fee, die der Cube (atlas) auf **C/D** deckelt. → Verdikt entschärfen oder gedeckelten Grade nutzen. **(W-G)**
- [ ] **M17 · start↔cockpit: widersprüchliches Netto** — `start.html:186-187`. start erbt Kosten aus `cockpit_price`, ignoriert aber `priceOv`/`occOv` → zwei Netto-Zahlen für denselben Host. → Overrides in eigenen Storage-Key.
- [x] **M18 · Tier-Badges fehlen** **(W-E)** *(erledigt v0.9.179: 🟡 an cockpit-Spalten `Gast/N`/`Host/N` (modelliert; `Preis/N` daneben = gemessen). `Bew./Mt` (vpm) bewusst gelassen — aus echten Zählungen abgeleitet, kein Modellwert; `start.html`-Kohorte separat.)*
- [x] **M19 · netzwerk: Netzwerk-Falschverschmelzung über geteilte Dienstleister** *(erledigt v0.9.181: Service-Co-Hosts (own=0, Co-Host für ≥2 unabhängige Owner) verbinden im Union-Find keine Netze mehr. Vorher/nachher verifiziert: falsches „Lukas"-Netz (2 unabh. Lukas + „Air", 3352 Bew.) aufgespalten; 5 Service-Co-Hosts erkannt; 122→121 Netze.)*
- [x] **M20 · netzwerk: „Premium-Preis +X %" aus Einzel-Ausreißern** *(erledigt v0.9.176: Claim nur ab ≥2 Inseraten, Einzel-Ratio auf 3× geklemmt; Lukas +839 %→weg, max jetzt 200 %)* — `build:217-224`. Lukas „+839 % über Markt" aus 1 Inserat (1061 CHF/Nacht, 3 % Belegung). → nur ab n_units≥2 + Cap + bei occ<10 unterdrücken.
- [ ] **M21 · netzwerk: X-Ray zählt Franchise-Sammelkonten als „extrem big"** — „Julia-Interhome" 522 Inserate / 62 Bew. → für `kind=brand` als „Sammel-Account" kennzeichnen.
- [ ] **M22 · netzwerk: X-Ray-`own_count` ≠ Netzwerk-`own_count`** (94 Operatoren, z. B. Yannick 12 vs 6) — zwei Pipelines in derselben Pill (`netzwerk.html:334`). → eine Quelle.
- [x] **N1 · netzwerk: Ertrags-Pille las sich als Gesamt-Portfolio-Ertrag** (Adrian-Befund am Bild: Secra „1207 Inserate gesamt" neben „CHF 9'079/Mt" — die CHF kommen aber nur aus 1 erfassten Inserat, der Umfang stand nur im Tooltip). *(erledigt v0.9.178: sichtbarer Umfang „· nur N von M erfasst"; eine `earnPill(est, erfasst, gesamt)`-Helper-Funktion statt 2× inline-Duplikat → DRY/klare Schnittstelle.)*
- [x] **M23 · netzwerk: toter Lead-Klassifikator** *(erledigt v0.9.181: `host_title=="Business"` (0 Treffer, Airbnb liefert „Superhost") → `superhost`. Leads 281→335: Superhosts mit <50 Bew/<3 Inseraten werden jetzt korrekt als Profi/Lead erkannt. Docstring mitgezogen.)*
- [x] **M24 · akquise: zwei „maximale Miete"-Zahlen** **(W-C)** *(erledigt v0.9.183: Strategie-Karten rechnen maxRent UND Cashflow jetzt über `dossOffer` = DIESELBE STREcon-Engine wie das Dossier, statt Magic-Kette + 0.71/-400-Modell. Verifiziert: Kriens medium 750→600 (jetzt identisch zum Dossier-Breakeven ~597); Cashflow als STREcon-Range. Call-Sites unverändert, eine Wahrheit.)* — Das ist die W-C-Wurzel: die „drei Ertrags-Engines" sind jetzt eine.
- [x] **M25 · akquise: dritte Zimmer-Heuristik** *(erledigt v0.9.182: Lead-Board nutzt jetzt `STREcon.roomsFromBedrooms(round(capacity/2))` — 4 Pers → 3.5 Zi statt falsch 2 Zi; konsistent mit der dokumentierten Heuristik → korrektes Band/Lukrativitäts-Urteil. Browser-verifiziert.)*
- [x] **M26 · akquise: hartcodierte Aufschläge ohne Tier** **(W-E)** *(erledigt v0.9.182: 🟡-Hinweis am Strategie-Block „Aufschlags-Prozente = grobe Faustregeln, keine gemessenen Werte". Es sind generische Such-Vorschläge, kein Objekt-Messwert → ehrlich gerahmt statt 4× inline getaggt.)*
- [x] **M27 · datenqualitaet Host-Auflösung** **(W-F)** *(erledigt v0.9.179: `:137` von konstant „stark/80" auf echte Quote `% mit erkanntem Host` — Kriens 97 %, variiert je Markt.)* Zweiter Teil `:130` Geo-Share **angefochten → GELASSEN**: niedriger Wert kann „breiter Radius + sauberes Clipping" (gut) ODER unsichere Geo-Zuordnung (schlecht) heissen — nicht eindeutig ein Überlegungsfehler, kein blinder Eingriff.
- [x] **M28 · briefing** *(angefochten v0.9.180)*: Top-10-Operator-Dubletten **waren schon gefixt** (`_dedup_by_host`, 0 Dubletten aktuell). Stille-Perle: **Review-Floor ≥10 ergänzt** (Buchungs-Beleg statt evtl. geblockter 100%-occ; 59→54 Perlen, gut-bewertete bleiben). Voller Recent-Velocity-Gate (≥2 Bew/letzter Monat) braucht review-history-Wiring → **offen**.
- [ ] **M29 · regulierung: „monatlich aktualisiert" unbelegt** — `regulierung.html:72,101,119` + statische `loopholes.js` ohne Datum. → konkretes „Stand: <Monat>" oder Claim abschwächen.
- [x] **M30 · briefing: „Bewegung" ungleiche Zeitfenster** *(erledigt v0.9.180: Sortierung + `net_pickup`-Summe auf `net_per_day` statt rohem `net` — fair über 1- vs 3-Nächte-Fenster. Aktuell alle days=1, war latent; jetzt korrekt bei ungleichen Fenstern.)*
- [ ] **M31 · RevPAR existiert nirgends** — keine belegungs-normalisierte Kennzahl in start/cockpit/economics. Ranking läuft über absolutes Brutto (bevorzugt teure Halb-leere). → `STREcon.revPAR` ergänzen.

## ⚪ Klein / Aufräumen

- [ ] **C32 · Encoding-Defekt** `data/cockpit-markets.json` — Umlaut-Keys kaputt (`ennetb�rgen`, `k�ssnacht`) → evtl. broken Markt-Link. UTF-8 neu schreiben.
- [ ] **C33 · `staysFor` rundet statt aufrundet** — `economics.js:73` → 1 Reinigung zu wenig bei manchen Fenstern, netto leicht zu optimistisch. `Math.ceil`.
- [ ] **C34 · start: keine Stale-Markierung** je Markt-Karte (Frische nicht durchgereicht).
- [ ] **C35 · atlas: toter Unlock-Code** — `atlas.html:856` `if(false)`-Block + verwaiste `state.unlock`-Logik. Aufräumen.
- [ ] **C36 · market-facts.json 5–6 Tage alt** (12.06.) — bei BFS-Export unkritisch, vor „Live"-Aussage neu exportieren.
- [ ] **C37 · akquise: ImmoScout-Param vermutlich falsch** — `:989` `pr` (Preis-von) statt `pt` (Preis-bis) → filtert ≥ statt ≤. Gegen echte Query prüfen.
- [ ] **C38 · netzwerk→akquise-Brücke verliert Kontext** — `netzwerk.html:282` übergibt nur Markt, nicht Operator/Zimmer/Miete → Dossier fällt auf Default 2.5 Zi.
- [ ] **C39 · `cap90`-Heuristik 3× dupliziert + Luzern hartcodiert** — `akquise.html:997,1364`. → ein Helper aus `data.js`-Tag.
- [x] **C40 · „Ø" auf Medianen** — `netzwerk.html:377/385` + Playbook-Signale: „Ø" → „Median" (cap_median/occ_median/Preis sind Mediane; rating_avg bleibt „Ø", clustert eng). *(erledigt v0.9.176)*
- [ ] **C41 · `_health.json` stale (04.06.) + nur von Legacy gelesen** — `update_health.py` fehlt. Pflegen+global einbinden oder als tot markieren.
- [ ] **C42 · landing: Produkt-Narrativ driftet** — `landing.html:306` bewirbt „Scout/Atlas"-Features, die im Live-Rückgrat so nicht mehr existieren (Zahlen stimmen).
- [ ] **C43 · Cache-Bust-Tags uneinheitlich** — `data.js?v=` divergiert je Seite (akq2/09153/09154/09107). Harmlos, aber inkonsistent.

---

## Empfohlene Abarbeitungs-Reihenfolge

1. **Schnelle 🔴-Einzeiler zuerst** (hoher Vertrauensgewinn, kein Risiko): K1 (MWSt), K2 (datenqualitaet), K9 (compEst-Tier), K8 (Homegate-Links).
2. **Wurzel W-A** (Kurzfenster-Krönung): K3 + K4 zusammen — Ranking/Kohorte/Briefing auf occ@30-stabil bzw. occ@90-Gegencheck. Räumt auch K5 mit auf.
3. **Wurzel W-B** (investor Rent-Modus): K10 + M13/M14/M15 in einem Durchgang.
4. **Wurzel W-C** (akquise eine Ertrags-Engine): K6 + K7 + M24.
5. **Wurzel W-D** (netzwerk Markt-Pool-Dedup): K11 — Build + Rebuild + vorher/nachher zeigen.
6. **Rest 🟡 → ⚪** nach Kapazität.
