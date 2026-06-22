# Fehler-Sammlung — Penetrationstest 2026-06-22

> Adrian: „schau dir alles an, sagt man dem Penetrationstest." 7 Prüf-Agenten parallel über **alle** Seiten + Engines, jeder adversarial: **Anzeige gegen Quelldaten** verifiziert. **NICHT gefixt — gesammelt.**
> Kern: **5 systemische Wurzeln** erzeugen die meisten ~40 Einzelfehler. Schwere 🔴/🟡/⚪.

---

## ✅ GEGENGEPRÜFT (2026-06-22 · 4 adversariale Verifizierer, je gegen den echten Code)

**Die Sammlung hält.** Fast alle Funde BESTÄTIGT (jede Zahl selbst am Code reproduziert), **1 widerlegt, 2 abgeschwächt, mehrere Counts korrigiert.** Korrekturen:

- **A (occ-Aufblähung) — Mechanismus bestätigt, aber NICHT uniform.** occ_by_horizon ohne Block-Sperre stimmt (95 `cal_managed=False`, 7 mit ≥183-T-Block → occ90=100). ABER „+22–37 pp in JEDEM Markt" war zu pauschal: echte Spanne **−7.5 bis +37 pp, 3 Märkte NEGATIV** (Aesch LU, Hildisrieden, Spreitenbach), Median pro-Inserat occ90−raw nur **+5 pp**. Stark horizont-/saison-abhängig — die krassen Fälle (occ100 auf geblockten Inseraten) sind ein **realer Teil**, nicht die Regel. Fix bleibt nötig (geblockte Inserate vergiften Perlen/Top-Verdiener), Tragweite nuancierter. *Beckenried-Beispiel: zwei Inserate verwechselt (112-T-Block hat reviews=263; das reviews=None ist ein anderes, 183-T).*
- **B — Überschrift „NIRGENDS" zu stark:** 3 Pfade filtern doch auf `entire` (cockpit-Kundensicht, akquise-Kohorte-Hauptpfad, datenqualitaet-Aspekt). Aber alle konkret benannten Pfade (start-Kohorte, briefing-Perlen, Cohort-Median, netzwerk) haben wirklich kein Gate → Einzelfunde alle bestätigt (Szilvia 19'803, 19/58, 135, 156/242, 5/14).
- **C bestätigt** (marketHeadline im Cockpit nicht aufgerufen, akquise ohne in_municipality); **Kriens aktuell 77 vs 77** (nicht divergent), Vitznau/Baden schon. **D bestätigt** (**40** Outlier statt 35). **E bestätigt** (Backend dedupt korrekt per uid = reines Display-Problem, 108 Namen ≥2 uids).
- ❌ **WIDERLEGT — Cockpit „host=None = toter Link":** der Link funktioniert (gültige url), nur das Label ist „—". Real bleibt nur fehlender Host-Name + Scraper-Inkonsistenz (Roger/horw vs None/kriens).
- 🟠 **ABGESCHWÄCHT — Cockpit ★=Superhost:** bewusster Design-Entscheid (★ = Rating-Band-Kopf 4.8–5.0, Kommentar dokumentiert; echter Superhost-Flag separat gerendert). Verwechslungsgefahr ja, Falschzuordnung nein. — 🟠 **Netto-Pickup „Nächte":** Defekt real (summiert Raten), aber heute (alle days=1) ist die Zahl korrekt → latent.
- **Count-Korrekturen** (Mechanismus stimmt): „besetzt"-1-Inserat 40→**25**, zwei-Sterne-Karten 44→**54**, Cockpit KPI-vs-Kurve 87/78→**77/69** (ältere Daten), akquise +234 %→**+214 %** / maxMiete **4'196** (Snapshot-Drift).
- **SAUBER-Behauptungen halten der Prüfung stand:** investor Buy-Mathe + data.js (199 Märkte, revpar≈adr×occ), kein Auto-Versand, Operator-Dedup, hotel kein STR-Leak.

**Fazit: keine Falsch-Positiv-Flut.** A + B bleiben Top-Priorität (vergiften Perlen, Top-Verdiener, Akquise-Spielraum am stärksten).

---

## SYSTEMISCHE WURZELN (hier zuerst fixen — räumen je eine ganze Fehlerklasse weg)

### 🔴 A — Auslastung tool-weit AUFGEBLÄHT (occ zählt Eigenblöcke als „belegt")
`compdata.py:47 occ_by_horizon` zählt **jeden** nicht-verfügbaren Kalendertag als belegt — **keine** Block-Sperre auf der pro-Inserat-`occ`. Die „gebucht-vs-geblockt"-Heuristik (`fetch_airbnb_free.py:144`, Block ≥45 T) läuft **nur aufs Markt-Aggregat**, nie auf das `occ`-Dict, das cockpit/start/netzwerk/akquise/briefing konsumieren.
- **95 Inserate** `cal_managed=False` (Block-Verdacht), davon **73** mit occ30≥40 weiter als belegt gezählt. **7 Inserate mit 183-Tage-Durchblock** zeigen occ90=**100 %** (Beckenried 112-T-Block, occ90=100, reviews=None = leere geblockte Whg = „100 % gebucht").
- occ30 liegt **+22 bis +37 pp über `cal_occ_raw_pct`** in JEDEM Markt. Der ehrliche Wert (`cal_occ_raw_pct`) liegt in jedem Inserat bereit, wird von **keinem** Geldrechner genutzt.
- **Kaskade (alles Folge-Fehler):** start-Spitzenverdiener (Vitznau „Carmen" 29'714/Mt auf occ93 % vs roh **39 %** = **2.4× aufgebläht**), briefing-Perlen (**17 von 17** occ-100-Perlen sind host-geblockt!), akquise-Spielraum (+234 %, s. F), netzwerk-est, Cockpit-Raster/KPI, Luzern Atlas 95 % occ.
- **Smoking Gun:** Code-Kommentar `fetch_airbnb_free.py:483` nennt Lukas/Kriens selbst „~90 % belegt" — das Tool glaubt der Falschzahl.
- **WO fixen:** `compdata.py occ_by_horizon` + `classify_calendar`; Roh-Kalender ist in Snapshots aufgehoben (`compdata.py:115`) → offline nachrechenbar.

### 🔴 B — R2R-Regel „nur GANZE Wohnungen" wird NIRGENDS durchgesetzt
Kein Code-Pfad filtert auf `entire===true`. Privatzimmer führen STR-Schlagzeilen an:
- **start:** Spitzenverdiener „Szilvia/Emmetten **19'803/Mt**" = `Private room`, price 943 (fehlgetypter Ganz-Objekt-Preis) → Schein-Run-Rate 240k/J, zählt in die ≥40k-Kohorte. 4/24 Märkte.
- **briefing:** **19 von 58** Stille Perlen sind Privatzimmer (6 in den Top-12: Judy 66 CHF, Edwin 59, Pia 119 …).
- **datenqualitaet:** Preis-/Occ-Sample mischt Zimmer (Adligenswil 5 von 14 = Zimmer) → Vertrauens-Score auf R2R-fremden Objekten.
- **netzwerk:** **135 reine Zimmer-Operatoren** gleichberechtigt in „Grosse Spieler"; Hotel/Hostel („Baden Youth Hostel") als STR-Operator.
- **cockpit/akquise/briefing-Median:** mischt Zimmer (Kriens 156 mit Zimmern vs **242** ganze Whg).

### 🔴 C — „Eine Wahrheit" nicht verdrahtet: Markt-Auslastung hat 4 verschiedene Werte
`marketHeadline` (cohort.js) ist nur zwischen **start ↔ cockpit** „eine Wahrheit" — und selbst da: **`marketHeadline` wird im Cockpit gar nicht aufgerufen** (0 Treffer), start behauptet trotzdem „exakt dieselbe Zahl wie im Cockpit". netzwerk/akquise/atlas nutzen je eigene Kohorte:

| Markt | Atlas (occ_cube) | Cockpit/start | Netzwerk (occ_median) | Akquise (isBusy) |
|---|---|---|---|---|
| **Vitznau** | 38 % | 73 % | 65 % | **83 %** |
| Kriens | 38 % | 66 %/72 % | 72 % | 77 % |
| Baden | 46 % | 37 % | 40 % | 63 % |

Vitznau **38 → 83 %**, vier Seiten, vier Zahlen. Zusatz: akquise filtert **nicht** `in_municipality` → Geo-Bleed bläht zusätzlich (Ebikon +30 pp). (Hinweis Atlas: occ_cube ist STR-Modell, NICHT Hotel — verifiziert.)

### 🔴 D — Preis-Cap versteckt den Preis, behält aber den aufgeblähten Ertrag
`build_operator_network.py:443` kappt `est_month` bei Preis>4×Median, lässt aber `price_chf` roh und rendert `price_outlier` **nie**. `netzwerk.view.js:75` zeigt Preis · occ · est zusammen → **User-Mathe ≠ gezeigter est**: „Adrian Steiner 1'634 × 90 % × 30 = 44'118" aber gezeigt **21'789** (2× Lücke, kein Flag). 35 solche Inserate. **briefing kappt NICHT** → zeigt 44'118 als **#1-Top-Verdiener**. Zwei Tools, dieselben Inserate, doppelte Zahl.

### 🟡 E — Gleichnamige Operatoren nur im DISPLAY nicht unterscheidbar
Backend dedupt **korrekt per `host_uid`** (nicht Name) → keine Doppelzählung im Graph. ABER das UI zeigt nur den Vornamen → zwei „Lukas"/„Szilvia"/„Doris" im selben Markt sind für dich nicht trennbar (dein Ausgangs-Fund). 108 Namen über ≥2 uids.

---

## PER-SEITE — spezifische Funde (nicht durch die Wurzeln erklärt)

### Cockpit
- 🔴 **„Auslastung 30T" = zwei Zahlen auf einer Seite:** KPI-Kachel (Median **87 %**) ≠ Buchungskurve (Mittelwert **78 %**) für Kriens, gleiche Auswahl. `cockpit.view.js:214` vs `251`.
- 🔴 **★ suggeriert „Superhost", ist aber reines Rating-Band** (Header „★ 4.8–5.0"); 15 Superhosts in Kriens haben Rating <4.8. `cockpit.view.js:68,132`.
- 🔴 **„min N erscheint nach dem nächsten Scrape"** — Doku-Text, aber die Daten sind live + rendern schon. `cockpit.view.js:199`.
- 🟡 Lücke/Preismacht-Flags feuern auf **n=1-Zellen** + Grenzwert-Median. 🟡 KPI-Schlagzeile auf **n=4–5** ohne Konfidenz-Hinweis am Wert. 🟡 `host=None` rendert „— ↗" als toten Link; dasselbe Inserat hat in horw.json `host=Roger`, in kriens.json `None` (Scraper-Inkonsistenz).

### Netzwerk
- 🔴 **100%-Belegungs-Inserate voll im Top-Verdiener** trotz eigener Warnung „eher Dauervermietung" (Mario #7 zu ⅓ auf occ100+outlier). 🔴 **Zwei verschiedene Sterne** auf einer Karte: `host_rating` (Meta) vs `rating_avg` (Playbook), 44 Karten >0.15 ab (Sharedlock 4.42 vs 4.75).
- 🟡 Carmen erscheint mit **81'912** (Operator) und **161'596** (Netzwerk) auf einer Seite. 🟡 „🔒 besetzt" auf Segmenten mit **1 Inserat** (40 Bänder). 🟡 „N Betreiber"/„total" im Lücken-Tab nutzt einen **anderen Pool** als der Operator-Tab (Rheinfelden 9 vs 49 distinkte Operatoren).

### Akquise
- 🔴 **„+234 % über der Marktmiete bieten"** steht wörtlich im UI — ökonomisch unmöglich, Artefakt von Wurzel A (occ30 als Jahres-Anker in `breakevenRent`, obwohl `economics.js:200` Jahresschnitt fordert → maxMiete **7× zu hoch**, Kriens 4'196 statt ~597).
- 🟡 Board-Ampel (stabile Kohorte) und Deal-Analyse-Panel können **denselben Lead unterschiedlich** bewerten. 🟡 Lead-Sortierung mischt **Spielraum (CHF) und Score (Punkte)** im selben Sort-Key. 🟡 „Markt unbekannt" durch Substring-Falle bei gleichnamigen Gemeinden. ⚪ ISC24-Deep-Link sendet aufgeblähtes `pr=maxRent`.
- ✅ sauber: **kein Auto-Versand** (nur Gmail-Prefill/Outbox), Merkliste-Dedup per URL, 3-Engine-Wurzel vereinheitlicht über STREcon.

### Briefing
- 🔴 **0-Nachfrage-Markt → „grau/unbekannt" statt rotem Signal:** Spreitenbach `med=0.0` → `round(0 if sg else None)` macht 0→None (`briefing_mails.py:146`); die ehrlichste Aussage („STR ~null, kein R2R") wird verwässert.
- 🟡 **Datums-Balken = Scan-Zeit, nicht Aufschaltung** (alle first_seen = 19.06. Batch; mein Scanner-Fix wirkt erst nach Re-Scan; Tooltip „≈ Aufschaltung" daher noch falsch; Zeitstempel malformed `+00:00Z`). 🟡 „Bewegung"-Toggle mischt **netto (mit Stornos) und brutto (lead_buckets)** → Balken kippt Vorzeichen (Hildisrieden −3 vs +11). 🟡 „Netto-Pickup (**Nächte**) +1121" summiert per-Tag-**Raten** als Nächte.
- ⚪ **Perlen-Regel „≥2 Bewertungen im letzten Monat" ist NICHT umgesetzt** — nur Lebenszeit-Count (`PERLE_MIN_REVIEWS=10`), `briefing.py:40` gibt's selbst zu.

### Start + Investor
- 🟡 **investor Rent-Sensitivitäts-Tabelle inkonsistent:** modus-blind nutzt Buy-Konstante → CoC-Mittelzelle 540 % ≠ Schlagzeile 565 %, Werte absurd >500 % ohne Modus-Hinweis. 🟡 „CoC"-Label-Drift im Rent-Modus.
- ✅ sauber: **investor Buy-Mathe vollständig konsistent** (NOI/Cap/CoC/FINMA/Hypothek/Wasserfall); **data.js (199 Märkte) intern sauber** (revpar≈adr×occ, Grade-Verteilung) — die alte data.js-RevPAR-Frage ist KEIN Bug (bewusst entkoppelt, korrekt getaggt).

### Nebentools
- 🔴 **atlas:** RevPAR liegt in **5 Märkten außerhalb des gezeigten Occ-Bands** (Gstaad RevPAR 290 = 65 % > Band-Obergrenze 44 %); **Luzern occ_cube 95 %** trotz 90-Tage-Cap (unrealisierbar); **Genève NICHT reg-capped** im Atlas, aber regulierung.html führt Genève als härtesten 90-Tage-Cap → Cross-Page-Widerspruch.
- 🔴 **datenqualitaet:** **fängt die occ-Aufblähung NICHT** (die Seite, die genau das prüfen soll — Adligenswil occ7=100/occ30=83/occ90=73 läuft durch); Zimmer im Sample (Wurzel B).
- 🔴 **hotel:** 10 Gemeinden ohne 2025-Jahreswert werden **still aus dem Ranking gedroppt**. 🟡 „Jahr 2025" hartcodiert, Daten bis 2026-03. ✅ sauber: **keine STR/ADR-Leckage** (Hotel≠STR eingehalten); der vermutete eingefrorene 2015-Timestamp **existiert nicht mehr** (dynamisch gelöst).
- 🟡 **regulierung:** MWSt „Stand 2024" (Wert 3.8 % korrekt, Etikett stale); Regulations-Watch „H1 2026" überfällig. 🟡 **datenqualitaet** Kalibrier-Panel hängt komplett an **Zürich** (zeigt Zürcher Δ auf jeder Markt-Seite). 🟡 **positionierung:** SVG-Karte ≠ Tabelle (Interim Homes doppelt + als „Zimmer-R2R" gegen die Ganze-Whg-Regel).

---

## ✅ GEPRÜFT & SAUBER (keine Regression / kein Fund)
- `lead_share>100` / `n_operators>total` / `band.share>100`: **0 Fälle** (K11-Guard hält). occ-Werte außerhalb 0–100: **0/11'296**.
- Operator-Dedup **per host_uid** korrekt (keine Namens-Verschmelzung); est_month = Σ(own.est) exakt; Netzwerk-Aggregate sauber; Pickup net=nb−fr korrekt.
- **STREcon**-Geldformeln intern korrekt (breakeven→netto=0, Kurtaxe nicht doppelt, DEFAULT_COSTS plausibel, keine zweite Geld-Formel). **isProfi** start↔cockpit identisch verdrahtet.
- **investor Buy** + **data.js** intern sauber. **kein Auto-Versand** in der Akquise. **hotel** kein STR-Leak. Atlas Hotel/STR-Trennung konsequent beschriftet.

---

## Reihenfolge zum Abarbeiten (Vorschlag)
**A** (occ-Aufblähung) und **B** (R2R-Gate) zuerst — sie erzeugen zusammen die Mehrheit der 🔴 über alle Seiten. Ein `entire`-Gate + Umstieg von `occ[30]` auf einen block-bereinigten Wert räumt start/briefing/cockpit/akquise/netzwerk/datenqualitaet gleichzeitig auf. Dann **C** (eine occ-Wahrheit als Band), **D** (Cap konsistent + Flag), dann die Per-Seite-🔴, dann 🟡/⚪.
