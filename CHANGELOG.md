# Changelog

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.
Format: [Semantic Versioning](https://semver.org/lang/de/).

## [0.9.115] — 2026-06-13 — Täglicher Cockpit-Runner (Free-Pipeline + Auto-Commit/Push) als Windows-Aufgabe

Der bestehende `run_focus_daily.ps1` nutzte die **bezahlte** BrightData-Pipeline (`fetch_airbnb.py`, API-Key). Neuer **`tools/daily_cockpit.ps1`** fährt den **Gratis-Cockpit-Weg** vollautomatisch, state of the art: pro Fokus-Gemeinde (`tools/cockpit_communes.txt`: Kriens/Emmen/Horw/Ebikon/Baden/Meggen) den öffentlichen Airbnb-Kalender frisch holen → `compdata.py` schreibt Serving-JSON + datierten Snapshot, dann **`git add data/snapshots data/cockpit-*.json` → commit → push** (Daten landen täglich off-machine in GitHub). **Robustheit:** (1) **Selbstheilung** — scheitert eine Gemeinde, laufen die anderen weiter (per-Gemeinde try/catch); ein Leer-Scrape (0 Inserate) überschreibt den letzten guten Stand NICHT (neuer Guard in `compdata.py`). (2) **Push-Ausfall ist nicht-fatal** — Commit bleibt lokal, landet beim nächsten erfolgreichen Push, Daten nie verloren. (3) Transcript-Log pro Tag in `data/raw/` (gitignored). (4) Coverage-Report nach jedem Lauf. Flags: `-Full` (zusätzlich Suche neu scrapen + PDP anreichern, wöchentlich sinnvoll), `-NoPush` (Testlauf). **`tools/register_daily_task.ps1`** registriert die Windows-Aufgabe „SwissSTR-Cockpit-Daily" (täglich 06:00, S4U = läuft ob eingeloggt oder nicht ohne gespeichertes Passwort, `StartWhenAvailable` holt verpasste Läufe nach, `WakeToRun`, laptop-/akku-tauglich, 2× Retry, kein Admin nötig). Caveat ehrlich: unter S4U kann der `git push` ggf. keine interaktiven Credentials sehen → dann greift der nicht-fatale Fallback (lokal committet); ersten geplanten Lauf prüfen, sonst auf `-LogonType Interactive` wechseln.

## [0.9.114] — 2026-06-13 — Snapshots durabel machen: committet statt gitignored + Coverage-Struktur

Adrian: „bleiben die Daten die wir scrapen bestehen? Das sollen sie — wir brauchen eine Struktur dafür." **Befund:** In v0.9.113 hatte ich `data/snapshots/` gitignored (wie die Roh-Scrapes) — falsch. Das Repo liegt in `C:\Users\adria\Claude`, **nicht** in OneDrive → die Snapshots lebten nur auf der lokalen Platte, ohne Backup. **Korrektur (Kern-Unterscheidung):** Roh-Scrapes (`data/raw/`) sind **regenerierbar** (neu scrapen geht) → bleiben gitignored; die täglichen Kalender-Snapshots sind **unwiederbringlich** (ein vergangener Tag lässt sich nie mehr holen) → gehören zum **best geschützten** Bestand. Darum: `data/snapshots/` aus `.gitignore` entfernt, **wird jetzt committet** = off-machine in GitHub, versioniert (160 KB heute, ~66 MB/Jahr für 6 Gemeinden — git trägt das jahrelang). **Struktur dokumentiert:** `data/snapshots/README.md` (warum committet, Dateiformat, Pickup-/r-Logik, Retention-Policy: nie löschen, erst bei sehr grossem Repo zu Monats-Aggregaten eindampfen). **Coverage-Tool:** `tools/snapshot_status.py` zeigt pro Gemeinde erster/letzter Tag, Anzahl Tage, **Lücken** (verpasste Tage), Inserate, belegte Kalendertage — so ist sofort sichtbar, ob die tägliche Reihe lückenlos läuft. Heutiger Stand: 6 Gemeinden, 6 Snapshot-Tage, 9'730 belegte Kalendertage, keine Lücken. **Offen (Folge):** der tägliche Runner muss den neuen Snapshot auch `git commit && push` (sonst landet die Historie erst beim nächsten manuellen Commit in GitHub).

## [0.9.113] — 2026-06-13 — Daten-Retention (Roh-Kalender werden aufgehoben) + 4 neue Gemeinden

Adrians Befund/Wunsch: das Tool soll bestehen + sich aufbauen, und heute mehr Gemeinden. **Befund vorab (ehrlich):** `compdata.py` holte bisher pro Inserat den vollen Kalender und reduzierte ihn auf die 8 Horizont-Prozente — **der Tag-für-Tag-Kalender (das Gold für Pickup-Kurve/r) wurde weggeworfen**, und `cockpit-<m>.json` wurde bei jedem Lauf überschrieben (keine Historie). Mengen-Check: ein Snapshot ≈ 30 KB/Tag/Gemeinde → ~11 MB/Jahr; 10 Gemeinden täglich ≈ 150 MB/Jahr → Speicher ist kein Engpass, das Leck war die Struktur. **Fix (additiv, Serving unverändert):** `compdata.py` schreibt jetzt zusätzlich einen datierten Snapshot `data/snapshots/<gemeinde>/<datum>.json` mit den Roh-Kalendern je Inserat (`booked`-Tage + Fenster), append-only; `cockpit-<m>.json` bleibt unverändert → Cockpit-UI unberührt. Snapshots sind gross+privat → `.gitignore` (`data/snapshots/`), wie die Roh-Scrapes; nur abgeleitete Zeitreihen kommen später ins Repo. Ab morgen ergibt der Diff zweier Snapshots die **echten Buchungen** (Tag, der von frei→weg springt) = Pickup-Kurve + r über Zeit. **4 neue Gemeinden** als Cockpits aufbereitet (Pipeline `pdp_enrich → fetch_boundary → compdata`, alle schon geo-sauber in_radius gescrapt): **Horw** (23 Inserate), **Ebikon** (25), **Baden** (10), **Meggen** (8) — plus Kriens/Emmen mit Retention nachgezogen. Gemeinde-Umschalter (`#mkt`) im Cockpit um die vier erweitert. **Datenmanagement-Befund (ehrlich, offen):** Cockpit-Gemeinden ≠ BFS-Markt-Set — **Horw + Ebikon fehlen in `market-facts.json`** (keine occ_band/bfs_monthly) → ihre Cockpits funktionieren voll (Filter/Karte/Geld-Fluss/Tabelle), aber die Jahres-Prognose zeigt den ehrlichen „kein Saison-Profil"-Hinweis statt geratener Zahlen (Daten-First). Baden (occ_band 20–46) + Meggen (59–70) haben BFS → Prognose rechnet. **Verifiziert (Browser, 0 Fehler):** Baden Cockpit + Prognose (Pool-Median 65 % ÷ Saison 1.19 → 54 % Jahresschnitt); Horw lädt voll (23 Zeilen, 25 Marker) mit grazilem Prognose-Hinweis (kein Crash, Leitplanke hält); Umschalter wechselt korrekt. Snapshots verifiziert (Kriens 1'939 / Horw 1'948 / Ebikon 2'316 / Baden 926 / Meggen 938 / Emmen 1'663 belegte Kalendertage aufgehoben), `git check-ignore` bestätigt sie bleiben lokal.

## [0.9.112] — 2026-06-13 — Prognose-Anker: gemessener Pool-Median × Hotel-Saison (cross-kalibriert, filter-reaktiv)

Adrians Methodik-Entscheid: Die Jahres-Prognose soll nicht auf einem Host (Lukas könnte Tage für sich/Freunde blocken) und nicht auf einem pauschalen Marktwert hängen, sondern auf dem **gemessenen Median des gefilterten Pools**, in die Zukunft projiziert über die **Hotel-Saisonkurve** als Rückgrat (BFS) — und auf jede Filterwahl reagieren. **Strikte Leitplanke (Adrian): rein additiv, bricht nichts vom Bestehenden; im Zweifel kippt die Prognose, nicht der Rest.** Umgesetzt nur in `renderForecast` + neuem `medOcc`-Helfer: (1) **Anker (Jahresschnitt-Auslastung)** = `medOcc(cur,30T) ÷ Saison-Index des Mess-Monats` — das gesettelte mittlere Fenster (30 T, vorlaufzeit-entzerrt) als gemessenes Niveau, entsaisonalisiert auf den Jahresschnitt, dann je Monat × Saison-Index verteilt (Reihenfolge: deine Eingabe > Pool-Median ÷ Saison > occ_band > ferner Horizont). **Median statt Mittel** → ein host-geblocktes Inserat kippt den Anker nicht (Adrians Lukas-Sorge). (2) **Ehrliche Spanne:** das Kalender-Niveau zählt gebucht + evtl. host-geblockt = **Obergrenze**; zusätzlich der **konservative Floor** aus dem review-basierten `occ_band` (Kriens 36–38 %) als zweite Netto-Zeile — Wahrheit dazwischen, der tägliche Scrape engt sie ein und ersetzt den Hotel-Proxy durch echte STR-Saison. (3) **`try/catch`-Kapsel:** ein Fehler in der Prognose zeigt nur einen Hinweis in ihrer eigenen Karte und reisst nie Tabelle/Karte/Charts/Filter mit (schützt auch retroaktiv v0.9.110). **Verifiziert (Browser, Kriens, 0 Fehler):** Anker = Pool-Median 73 % (30 T, 26 Inserate) ÷ Saison 1.27 → Jahresschnitt 58 % → Jun 73 % / Jul 81 % / Winter ~34 % (deckungsgleich mit Python-Nachrechnung, reproduziert Adrians „70 % in Hauptsaison" aus den Daten). **Filter-reaktiv bewiesen:** „nur Gemeinde" → 14 Inserate, Pool-Median 69 % → Jahresschnitt 54 %, Werte ziehen mit. **Leitplanke geprüft:** nach allen Filter-/Toggle-Klicks Tabelle weiter 26 Zeilen, Karte 28 Marker, 4 Charts, 4 KPIs unberührt. Jahr-Toggle (Rest 2026, Juni anteilig) weiter korrekt. Hinweis: bei selektiertem Host folgt der Preis dem Inserat, die Auslastung bleibt bewusst der Pool-Median (kein Single-Host-Risiko).

## [0.9.111] — 2026-06-13 — Methodik-Sektion deckt jetzt auch die Jahres-Prognose ab

Lücke geschlossen nach Adrians Nachvollziehbarkeits-Regel (jedes Resultat muss seine Herleitung zeigen): Die in v0.9.110 gebaute Jahres-Prognose produzierte Monatszahlen, war aber noch nicht in der „📐 Wie wird gerechnet?"-Sektion erklärt. Neuer Absatz `<h4>Jahres-Prognose — Monat für Monat 🟡</h4>` legt die ganze Kette offen: (1) Niveau = Jahres-Auslastung (`occ_band`, Reihenfolge Eingabe→Mitte→Kalender-Median); (2) Verteilung = `seasonalIndex` aus `bfs_monthly` (27 Mte BFS-Logiernächte 🟢, auf Jahresschnitt 1.0 normiert, Juli ≈1.42 / Jan ≈0.58); Formel `Monats-Auslastung = Jahres × Saison-Index`, Deckel 92 %; Verdienst = dasselbe Geld-Modell pro Kalendermonat mit echten Tagen; Toggle 12-Monate-rollend ↔ Rest-Kalenderjahr erklärt. Grenzen-Absatz ergänzt: Saison-Form ist Hotellerie-Proxy für STR, occ_band-Punkt verschweigt die Spanne, fehlendes `bfs_monthly` → Hinweis statt geratener Zahlen. **Verifiziert (Browser):** Methodik-Sektion 6 Überschriften (vorher 5), Prognose-Absatz + Grenzen-Caveat gerendert, 0 Fehler.

## [0.9.110] — 2026-06-13 — Cockpit: Jahres-Prognose Monat für Monat + Gesamttotal-Box

Adrians Wunsch: unter dem Cockpit eine Vorhersage pro Monat (wahrscheinliche Auslastung + wahrscheinlicher Verdienst), rechts ein Jahres-Gesamttotal aus Einnahmen/Ausgaben, mit Umschalter Kalenderjahr ↔ 12 Monate. **Methode (deckt sich mit der „Wie"-Diskussion der Vor-Session — BFS-Saison × Snapshot-Level):** Die Monats-Auslastung ist **kein erfundener Wert**, sondern `Jahres-Auslastung × regionales Saison-Profil`: Anker = `occ_band` aus `market-facts.json` (Kriens 36–38 % Jahresschnitt, 🟡 ehrliche Spanne), Saison-Form = `bfs_monthly` (27 Monate BFS-Hotellerie) normiert auf Jahresschnitt 1.0 (`seasonalIndex()`), Deckel 92 % (occ_band ist Jahres-, nicht Monatswert). Der **Geld-Teil wiederverwendet 1:1 das bestehende Geld-Fluss-Modell** (`hostBleibt`, Miete/Internet/Wasser-Strom fix, Reinigung+Verbrauch variabel, alle Werte aus `PD`/localStorage) — pro Kalendermonat mit echten Tagen + Saison-Auslastung gerechnet, reagiert live auf Preis/Belegung/Kosten oben. Anker-Auslastung: Override (Geld-Fluss-Belegung) > occ_band-Mitte > Kalender-Median. **Toggle:** „Nächste 12 Monate" (rollend ab fetched-Datum, 12 Zeilen) ↔ „Dieses Jahr" (Rest des Kalenderjahres, laufender Monat anteilig nach Resttagen, weniger Zeilen) — zwei genuin verschiedene Totale (volles Jahr vs. Rest-Jahr-Cashflow). Layout: Monatsliste links (Saison-Balken + Netto + Nächte/Einnahmen je Monat), sticky Gesamttotal-Box rechts (Einnahmen − Fix − Variabel = Netto, Ø-Auslastung, Methoden-Fussnote), stapelt mobil. Tier-Badge 🟡 modelliert, Saison-Form ehrlich als „Hotel-Proxy für STR" benannt. Fehlt einem Markt `bfs_monthly`, erscheint ein ehrlicher Hinweis statt geratener Zahlen. Zeit-Anker = `fetched`-Datum (kein `Date.now`-Drift). **Verifiziert (Browser, Kriens):** 0 Konsolenfehler; Monatskurve exakt deckungsgleich mit unabhängiger Python-Nachrechnung (Jun 47 · Jul 52 · Aug 51 · … · Mai 44, Ø 37 % = occ_band-Mitte); beide Toggle-Modi korrekt (12 Zeilen ↔ 7 Zeilen mit Juni anteilig „· Rest"); Desktop zweispaltig (Monate + sticky Box), reagiert live auf Geld-Fluss-Eingaben. Hinweis: bei Adrians gespeicherter Test-Miete 3'000 ist das Jahres-Netto negativ — ehrlich konsistent mit „Kriens kein B"; in der Geld-Fluss-Box anpassbar.

## [0.9.109] — 2026-06-12 — Landingpage neu: Ehrlichkeit als Verkaufsargument (Taktik vom Architekten geprüft)

Adrians Befund: alles ausser dem Hero unprofessionell, Taktik fehlt. Die alte Page war v0.9.x-früh-Stand (81 Märkte, 72 BFS, 6 Scout-Strategien, erfundene Mock-Zahlen, unbelegter AirDNA-Vergleichs-Claim). **Neue Taktik (Kernsatz: Die Page verkauft radikale Daten-Ehrlichkeit — jede Zahl muss aus `market-facts.json` belegbar sein):** Der swissstr-architekt hat die Taktik vor dem Bau geprüft und 3 Prämissen-Fehler gefunden, alle 5 Korrekturen umgesetzt: (1) Hero-Mock zeigt nie Trust-8-Werte badge-los — Top-RevPAR-Liste mit Trust-Chips, Grindelwald/Zermatt ausgegraut («dünne Beleglage»), **Luzern (das einzige B) hervorgehoben** — Pointe «Hohe Zahl ≠ belastbare Zahl»; (2) Grade-Story als **Beleglage-Urteil, nicht Markturteil** geframt (Dreischritt: Regel → Befund 1×B/31×C/156×D → Unlock-Liste Chur/Zermatt/Interlaken/Lauterbrunnen/Meggen als Beweis, dass der Deckel fällt); (3) «BFS-fundiert» präzisiert zu «27 Monate amtliche Hotel-Daten als Fundament», STR-Werte sichtbar als 🟡 Modell geschichtet; (4) AirDNA-Claim gestrichen, positiv ersetzt (gemeinde-genau, Trust pro Aussageart, offene Quellen); (5) Features 6→3 Entscheider-Fragen (WO lohnt's · WAS springt raus · WIE legal). Neu ausserdem: Datenstand sichtbar (Trust-Strip + Footer: HESTA bis März 2026, Abgleich Mai 2026), durchgerechneter **Luzern-Steckbrief** (RevPAR 185 🟡, ADR 195, Occ «ab 49%», Trust 50/50/50, NOI ~47'900) als «So antwortet SwissSTR», Unabhängigkeits-Satz (keine Provisionen/Objektvermittlung), Frühzugang-CTA mit ehrlicher Erwartung (Beta, unregelmässige Mails). Raus für immer: erfundene Testimonials/Logos/Nutzerzahlen, Preise, badge-lose Mock-Zahlen. `transition:all`→spezifische Props (Screenshot-Timeout-Plage). **Verifiziert (Browser):** 0 Konsolenfehler, alle Sektionen + Grade-Balken + Steckbrief gerendert; alle Page-Zahlen gegen `market-facts.json` (Stand nach v0.9.108) re-verifiziert — unverändert gültig.

## [0.9.108] — 2026-06-12 — DURCHBRUCH: Free-Scraper kann doch Kalender (Auslastungs-Obergrenze gratis)

Adrian forderte „finde den Weg, den Kalender zu sehen" — und es gibt ihn. Der Free-Scraper holte bisher nur die Such-Seite (kein Kalender, v0.9.101 hielt Belegung für free-strukturell unbeobachtbar). **Falsch:** Airbnb hat einen ZWEITEN öffentlichen Endpoint je Inserat (`PdpAvailabilityCalendar`, GraphQL, öffentlicher Web-Client-Key `d306…` — gleicher Weg wie Inside Airbnb). Ein Aufruf pro Wohnung, gratis, liefert pro Tag available true/false über ~183 Tage. Live verifiziert (4/4 Test-Inserate, dann 5 Märkte voll).

**Eingebaut in `fetch_airbnb_free.py`:** `fetch_calendar(id)` (öffentlicher Endpoint, ~0.7s/Inserat Höflichkeitspause, Deckel 80/Markt) + `classify_calendar()` = **Adrians „gebucht vs. host-geblockt"-Heuristik**: ein dominanter Langblock (≥45 Tage UND ≥70% aller Sperrtage) = host-geblockt/privat → fliegt aus der Auslastung; verstreute Buchungen ODER viel-frei = echtes Marktsignal → zählt. **1.-Wurf-Fehler korrigiert:** erste Regel („gaps≥3") warf fast-LEERE Inserate fälschlich in den Block-Topf (7%-belegt-Inserat hat nur 1 Frei-Block) — schwache Nachfrage ist ehrliches Signal, muss zählen. Engine-Felder `occ_calendar_pct`/`occ_method=calendar` NUR für aktiv bewirtschaftete Inserate gesetzt (host-geblockte würden die Obergrenze künstlich heben = Horw-180/183-Problem), Roh-Werte transparent in `cal_occ_raw_pct`/`cal_managed`/`cal_longest_block_days`.

**Ergebnis — die Spanne SCHLIESST sich, und zwei unabhängige Methoden stimmen überein:** Erstmals hat die Luzern-Agglo beide Enden. Horw 40–40% (Breite 0!), Kriens 36–38% (2), Ebikon 35–41% (6), Emmen 38–45% (7), Engelberg 24–39% (15, Off-Season-Forward-Vorbehalt: Ski-Resort im Juni → Winter noch nicht gebucht). **Schmale Bänder = Review-Proxy und Kalender bestätigen sich** → `calculateCalendarIntegrity` springt auf 78 (Ehrlichkeits-Deckel, „mittel") → Horw D→C. **Ehrliche Lesart: der Kalender BESTÄTIGT das nüchterne Bild (~36–45% Auslastung), statt Adrians Augenschein-Optimismus zu belegen** — kein B, aber jetzt belastbar statt geraten. occOf-Punktwert unverändert (kein Revenue-Shift). Fix: `loadAirbnbComp` fetch `{cache:'no-cache'}` (Heuristik-Cache verbarg die neuen Kalenderdaten). Texte der 3 Export-Märkte neu (Sonnet). **Tragweite: gilt projektweit** — jeder künftige Free-Scrape liefert die Obergrenze gratis, nicht nur diese 5. Offen: Off-Season-Forward-Bias dokumentieren/dämpfen; Snapshot-Velocity (v0.9.101) bleibt die Gold-Lösung über Zeit; persisted-query-Hash kann brechen (dann nachziehen).

## [0.9.107] — 2026-06-12 — Adrians Fokus-Liste gescrapt + KI-Texte LIVE: das Modell wurde ehrlich korrigiert

**KI-Texte sind live.** Erster echter Batch-Lauf (Sonnet, 188 Märkte, 0 Fehler, ~$0.45). Fix dabei: `safe_id` erzeugte Nicht-ASCII-IDs („zürich" — Pythons `isalnum()` ist Unicode-aware) → API-400; jetzt ASCII-Filter. Poller starb still → neues `tools/fetch_batch_results.py` (holt fertige Batches nach, kostenlos). Neues `tools/refresh_market_texts.py`: frischt EINZELNE Märkte per Direkt-API auf (nach Scrapes; 3 Märkte ≈ 2 Rp. statt Voll-Batch).

**Fokus-Liste gescrapt (Adrian: Emmen/Emmenbrücke, Kriens, Horw, Ebikon, Engelberg).** Emmenbrücke = Ortsteil von Emmen; **Ebikon als Markt neu angelegt** (data.js, Horw-Muster konservativ, war schon in `_LUZERN_AGGLO`); Ebikon+Engelberg in `market-centers.json`. Free-Scrape alle 5 geo-sauber (90–100% in-radius, 34–58 Preise je Markt, Engelberg via Quadtree-Sweep 29 Boxen/0 Fehler). **Scraper-Fix `append_history`:** Tages-Guard ERSETZT jetzt den Tages-Snapshot statt zu überspringen — ein magerer Früh-Lauf (adr_n=1–3) hatte den besseren Lauf blockiert. `--aggregate` neu gebaut (79 Märkte, Ebikon/Engelberg erstmals mit Serie).

**Ehrliches Ergebnis — der Grenchen-Effekt, wieder:** Die echten Preise liegen KLAR unter den Modell-Annahmen. Kriens NOI 26'710→**11'375** (ADR real 157, Occ ab 37%), Emmen NOI→4'933 (ADR real 119), Engelberg NOI 11'100. **Kriens fliegt aus der „B möglich"-Liste** (Potenzial C statt B) — kein einziges B für die Fokus-Liste, dafür belastbare Wahrheit VOR einer Anmietung. Trust deutlich rauf: Engelberg econ 8→50 (demand 84), Emmen/Kriens 30→50, Ebikon (neu) 40. Preis-Trust deckelt bei 40–55 wegen Platform-Drift (Früh-Lauf vs. Haupt-Lauf am selben Tag) — legt sich mit konsistenten Folge-Scrapes. Horw/Ebikon bleiben ohne BFS-Match → nicht im Atlas-Export (Voll-Tool hat die Daten). Cache-Bust data.js v0988→v09107. market-facts.json re-exportiert, Texte der 3 Export-Märkte mit frischen Zahlen regeneriert.

## [0.9.106] — 2026-06-11 — KI-Texte: Kosten-Optimierung (Modellwahl + schlanker Prompt)

`tools/generate_market_texts.py` auf Adrians Kosten-Entscheid optimiert, ohne die Daten-First-Grenze zu berühren: (1) **`--model {opus,sonnet,haiku}`** mit Preistabelle im Dry-Run — Default neu `sonnet` (claude-sonnet-4-6): für kurze Fakten-Umformulierungen qualitativ ausreichend, 40% des Opus-Preises; `haiku` für Minimal-Kosten per Flag. (2) **Prompt geschlankt:** `bfs_monthly` (27 rohe Monatswerte je Markt — Peak steht bereits als Feld drin) + Null-Felder fliegen aus dem Payload (`slim_fact`) — Input 115k→95k Tokens, keine einzige vom Texter genutzte Zahl ändert sich. Dry-Run real gemessen: **Opus ~$0.75 · Sonnet ~$0.45 · Haiku ~$0.15** für alle 188 Märkte (Batches-Rabatt eingerechnet). Prompt-Caching geprüft und bewusst NICHT eingebaut: System-Prompt ~300 Tokens liegt unter dem Cache-Minimum von Sonnet 4.6 (2048) — würde nichts bringen. `_meta.model` im Output trägt jetzt das tatsächlich verwendete Modell.

## [0.9.105] — 2026-06-11 — Atlas: Claude-API-Key-Verwaltung oben rechts (unauffällig, mit Gratis-Test)

Neuer dezenter ⚿-Button in der Atlas-Topbar (zwischen Daten-Stand und Voll-Tool-Link): Popover zum **Eintragen und Testen des Anthropic-API-Keys nach Bedarf**. Der Test ruft `GET /v1/models?limit=1` direkt aus dem Browser auf (Header `x-api-key` + `anthropic-version` + `anthropic-dangerous-direct-browser-access`) — **kostenlos, verbraucht keine Tokens**. Status-Punkt am Button: grün=gültig, rot=ungültig (401), leer=kein Key. Key liegt NUR im localStorage dieses Browsers (nie committet, nie an Dritte); Popover erklärt das und bietet «Zeile kopieren» für die `.env` (der Python-Batch-Lauf liest weiterhin `swissstr/.env`, seit v0.9.104b automatisch). Passwort-Feld, Enter=testen, Entfernen-Button, Outside-Click schliesst.

**Verifiziert (Browser):** 0 Konsolenfehler; CORS-Pfad end-to-end bewiesen (absichtlich ungültiger Key → echte 401-Antwort der API → „✗ Ungültig" + roter Punkt, localStorage-Persistenz); Layout Desktop 1280 + Mobile 375 (eine Zeile, Popover im Viewport).

## [0.9.104] — 2026-06-11 — Atlas: Erreichbarkeit + individuelle Scrape-Liste (Adrian wählt, nicht die Engine)

Adrians Einwand: nicht die 6 Deckel-Märkte der Engine scrapen, sondern **Märkte, die er erreichen kann — individuell gewählt.** Neu im Atlas, Sektion «📍 Erreichbarkeit & deine Auswahl»: (1) **Standort setzen** (Datalist aus 137 Orten mit Koordinaten: `MARKET_COORDS` + neu `communes.json` als Fallback, localStorage-persistent) → jede Karte zeigt die **Distanz in km (ehrlich gelabelt: Luftlinie)**, Sortierung «Nähe ↑», Filter-Chips «≤25/50/100 km» (warnen, wenn kein Standort gesetzt). (2) **Scrape-Liste:** «+ Liste»-Button auf jeder Karte und im Steckbrief, Filter-Chip «📋 Meine Liste», persistent; Listen-Panel mit Distanzen, **indikativer Kostenschätzung** (BD ~$2.50/1k Records × 100–300 Inserate/Markt, als Schätzung gelabelt) und «Liste kopieren» (Clipboard → an Claude schicken: „scrape diese Liste"). Distanz ist reine Anzeige-Geometrie (Haversine), keine Markt-Berechnung — Daten-First unverletzt.

**Verifiziert (Browser):** Standort Luzern → Grindelwald 52 km/Gstaad 101 km plausibel; ≤25-km-Filter liefert exakt die Agglo (Emmen, Kriens, Zug, Weggis, Vitznau, Brunnen, Sursee, Beckenried, Luzern); Liste Chur/Thun/Engelberg → $0.75–2.25 geschätzt, «Meine Liste»-Filter zeigt genau diese 3; 0 Konsolenfehler.

## [0.9.103] — 2026-06-11 — Atlas Wurf 2: Grade-Engine, Zwei-Welten-Trennung, Occ-Spanne, Trust — und der ehrliche Befund zu „mehr A/B"

Adrians Frage „kannst du mehr Grade A/B erzeugen?" hat einen strukturellen Fund ausgelöst: **`grade` war nie engine-gerechnet, sondern ein kuratiertes Hardcode-Label in `js/data.js`.** Mehr A/B per Label wäre die Sorte Lüge, die Daten-First verbietet. Stattdessen:

**Grade-Engine (`computeGradeEngine`, index.html):** Grade neu aus Engine-/BFS-Werten hergeleitet — Ertrag (Modell-NOI) + reale Nachfrage (BFS YoY) + Realitäts-Check (Optimismus-Lücke) + Hotel-Basis (BFS-Occ) + Reg-Cap, Schwellen dokumentiert. **Daten-Deckel:** Economics-Trust ≤30 → max C, ≤50 → max B. **Ehrlicher Befund:** 0×A, 0×B, 32×C, 156×D — denn 143/188 Märkte haben Economics-Trust ≤30 (meist n_preise=0). Sechs Märkte (Chur, Interlaken, Meggen, Zermatt, Lauterbrunnen, Kriens) wären nach Markt-Signalen **B**, hängen aber am Daten-Deckel → Export-Feld `grade_potential` macht den Weg sichtbar: **mehr A/B entsteht durch gezielte Preis-Scrapes, nicht durch Label.** Kuratiertes Alt-Grade bleibt als `grade_curated` erhalten; `m.grade` im Voll-Tool unangetastet (kein Regressions-Risiko).

**Export erweitert** (`buildMarketFacts()` von Download getrennt, beides `window.*`): `grade_potential/score/parts/cap/curated`, `trust` {demand/price/econ} aus `calculateFinalDataTrustScore`, `occ_band` aus `occupancyBand` (v0.9.101-Spanne), `bfs_monthly` (27 Monate reale Logiernächte für Saisonalität). Re-Export via Mini-HTTP-Listener (PowerShell, Port 8799) direkt aus dem Browser auf Platte — kein Download-Dialog.

**Atlas-Qualitätssprung (atlas.html):** (1) Hero-Stat + 🔓-Sektion **„Der Weg zu mehr A/B führt über Daten"** = klickbare Scrape-Prioritätenliste der 6 Deckel-Märkte. (2) Steckbrief **zweispaltig „STR-Modell 🟡 ↔ Hotel-Realität 🟢"** mit Konvergenz-Zeile (Optimismus-Lücke in Worten) — die Hotel/Airbnb-Trennung ist jetzt Layout, nicht Fussnote. (3) **Occ als ehrliche Spanne** überall: „53–65%", „ab 63%" (nur Untergrenze, mit Open-End-Balken), nie mehr nackter Punktwert. (4) **„Warum Grade X?"**-Zerlegung als ±Chips + Daten-Deckel-Box. (5) **Trust-Balken** je Aussageart (Stufen-Mapping gespiegelt von `_trustStufe`). (6) **BFS-Saisonalitäts-Sparklines** auf jeder Karte + gross im Steckbrief mit Peak-Label (echte Messdaten). (7) Trust-Pill auf jeder Karte, NOI-Relativbalken, Top-3-Medaillen, Skeleton-Loader, Scroll-Reveals, Sortierung neu nach Grade-Score/Trust, Filter-Chip „🔓 Daten-Deckel". Fix: `fetch(..., {cache:'no-cache'})` gegen Browser-Heuristik-Cache nach Re-Export; `transition:all`→spezifisch (hängende border-width-Transitions).

**Verifiziert (Browser):** 0 Konsolenfehler auf Atlas UND Voll-Tool; Export 188 Märkte/alle neuen Felder auf Platte geprüft; Chur-Steckbrief: Score +4, Deckel „Trust 8 → max C", Trust 58/8/8, Spanne „ab 63%", Peak Aug 2025 = 25'854 Logiernächte; Unlock-Liste = exakt die 6 Deckel-Märkte; Mobile 375px komplett geprüft.

## [0.9.102] — 2026-06-11 — Atlas: zweite Seite als reine Entscheider-Ansicht (mobile-first, Daten-First)

Neue eigenständige Seite **`atlas.html`** neben dem Voll-Tool — gebaut als Antwort auf „Was verdient man, und wo?" in einer Ansicht, die aufs iPhone passt. **Architektur-Entscheid (Daten-First, keine zweite Engine):** Atlas berechnet keinen einzigen Markt-Wert neu, sondern liest ausschliesslich den Engine-Export `data/market-facts.json` (`exportMarketFacts()`, einzige Rechen-Engine bleibt `marketEconomics`/`detectAnomalies`/`occOf`). Damit kann die zweite Seite nie von der ersten abweichen.

**Was Atlas zeigt:** (1) Hero-Stats (188 Märkte, 28 Edge-Kandidaten, Top-NOI, 79 Reg-Caps), Daten-Stand automatisch aus Last-Modified des Exports. (2) Echte TopoJSON-Schweiz-Karte (gleiche Projektion + swiss-maps-Quelle wie Voll-Tool, `MARKET_COORDS` aus `js/coords.js`), Punktgrösse = NOI, Farbe umschaltbar NOI/RevPAR/YoY, ehrlicher Hinweis „82 Märkte mit Koordinaten sichtbar". (3) Ranking-Cards mit NOI-Headline zuerst (Entscheider-UI-Regel), Grade-Badge, REG-CAP-Flag, Verdikt-Ampel. (4) Such-/Filter-Leiste sticky: Kategorie, Grade, „ohne Reg-Cap", Verdikt-Chips mit Zählern. (5) Markt-Steckbrief als Bottom-Sheet inkl. Edge-Zerlegung (Nachfrage/Optimismus/Hebel als Balken) und Deep-Link `#m=Name`. (6) Direktvergleich bis 3 Märkte (Bestwert gold). (7) Quadrant „Realität vs. Modell": x = Logiernächte-YoY (real BFS), y = NOI (Modell) — oben rechts zuerst suchen.

**Ehrlichkeit als UI-Element:** Jeder Wert trägt einen Quellen-Punkt (🟢 real BFS: YoY/Hotel-Occ/Leerstand · 🟡 Modell: ADR/Occ/RevPAR/Brutto/NOI), Occ ist explizit als „Cube-Punktwert, Spanne im Voll-Tool" gelabelt (v0.9.101-Linie), Methodik-Block erklärt Grade/Verdikt/Reg-Cap. Kein Tailwind, kein Build-Step — eine Datei, nur topojson-client als CDN-Dependency. Voll-Tool-Nav verlinkt neu auf „Atlas" (eigene Klasse `nav-ext`, damit der `showView`-Handler nicht greift).

**Verifiziert (Browser, Preview-Server):** 0 Konsolenfehler; 188 Märkte geladen; Gstaad-Steckbrief CHF 78'918 netto/Jahr = exakt Export-Wert; Edge-Filter 28/188; Suche „grenchen" → 1 Treffer; Vergleich 3 Spalten/11 Zeilen; Quadrant 186 Punkte; Mobile 375px sauber (sticky Filter, Cards, Sheet mit safe-area-inset).

## [0.9.101] — 2026-06-10 — Auslastung als ehrliche Spanne: „Kalender (scharf)" war eine Überzeichnung

Deep-Research (5 Winkel, 17 Quellen, 21 Claims adversarial verifiziert) zum Kalender-Problem ergab einen harten Befund: **echte Belegung ist aus öffentlichen Airbnb-Daten strukturell NICHT beobachtbar.** Seit Airbnbs Umbau 2014 verschmelzen „gebucht" und „host-blockiert" in eine einzige „nicht verfügbar"-Kategorie (Housing Studies 2023, Inside Airbnb, PLOS ONE 2024, alle 3-0). Es gibt keine Ground Truth. Anders als Geo-Bleed (Defekt, an der Quelle reparierbar) ist Belegung *prinzipiell unbeobachtbar* — die ehrliche Lösung ist Einklammern, nicht „Wahrheit finden".

**Strukturelle Lösung — Auslastung als Spanne zwischen zwei gegenläufig verzerrten Schätzern** (`docs/auslastung-methodik.md`): Kalender-Verfügbarkeit überschätzt (Host-Blocks zählen als gebucht) = **Obergrenze**; Review-Proxy unterschätzt (nicht jeder bewertet) = **Untergrenze**; echte Belegung liegt dazwischen, die **Spannenbreite IST die Unsicherheit**. Neu: `occupancyBand(m)` → {lower, upper, mid, widthPp}. `calculateCalendarIntegrity` zieht das Vertrauen jetzt aus der **Band-Übereinstimmung** (schmal = beide Methoden einig) statt aus roher Kalender-Quote, mit **Ehrlichkeits-Deckel max 78** (Einzel-Snapshot nie „stark" — analog „nie decision_grade"). Das Lügen-Label **„Kalender (scharf)" → „Kalender-Verfügbarkeit (Obergrenze)"** korrigiert (gleiche Klasse wie host-blinder Profi-0%, v0.9.99). Band sichtbar im Cube-Detail je Markt.

**Verifiziert (Browser):** Zug 28–47% (Δ19pp), Aarau 31–48%, Gstaad 24–44%; Zürich Free-Scrape nur Untergrenze 32% „gebucht-vs-blockiert offen". 0 Konsolenfehler, occOf-Punktwert unverändert (kein Revenue-Shift, keine Regression). **Strukturelle Quell-Lösung offen (v-next):** Snapshot-Velocity (per-Listing-Kalender-Historie über Zeit → available→unavailable-Übergänge); braucht wiederholte Scrapes (Frequenz entscheidend: täglich vs. >50% verfehlt bei vierzehntägig).

## [0.9.100] — 2026-06-10 — KI-Begründungs-Texte: Pipeline gebaut (Perlen/Such-Strategien, P2.2+P2.3)

Erste Claude-API-Integration im Projekt — und zwar **innerhalb** der Daten-First-Grenze: der LLM **rechnet nichts**, er formuliert nur die bereits von `marketEconomics`/`whyEdge` berechneten Werte zu einem scharfen Satz um. Damit bleibt die EINE Engine die einzige Rechen-Quelle (P1).

**3-Stufen-Pipeline** (`docs/ki-texte.md`): (1) SPA-Exporter `exportMarketFacts()` → `data/market-facts.json` (188 BFS-Märkte, Werte aus der echten Engine, nicht in Python nachgerechnet). (2) `tools/generate_market_texts.py` → Anthropic **Batches API** (50% günstiger), `claude-opus-4-8`, strukturierte Ausgabe je Markt (`pearl_reason`, `strategy_hint`), strikter Grounding-Prompt (keine erfundene Zahl, keine Prognose) → `data/market-texts.json`. (3) `index.html` lädt die Texte graceful (fehlen sie → Fallback auf deterministisches `whyEdge()`); KI-Texte erscheinen im Edge-Ranking mit ehrlichem **`✨ KI · 🟡 MOD`**-Label.

**Verifiziert:** Exporter liefert 188 Märkte mit Engine-Werten (Zürich: ADR 146 kalibriert, Occ 49%, NOI 15'145), 0 Konsolenfehler. Dry-Run: ~78k In-/41k Out-Tokens, **~$0.71** für alle Märkte. **Offen (Adrians Spend-Entscheid):** echter Batch-Lauf — `python tools/generate_market_texts.py` mit `ANTHROPIC_API_KEY` gesetzt. Bis dahin zeigt das Tool unverändert die deterministische Begründung.

## [0.9.99] — 2026-06-10 — Zahlen-Audit: Profi-Anteil lügt nicht mehr (host-blinde 0% → „n/v")

Erster Fund des In-Tool-Zahlen-Audits, direkt aus dem InsideAirbnb-Quervergleich (v0.9.98). Der **Profi-Host-Anteil** wurde für Free-Scrape-Märkte als gemessene **0%** angezeigt (Konkurrenz-Röntgen Markt-Detail: „0% (0/42)"; Scout-Röntgen: „0 Vollzeit-Profis" mit grünem ● Live-Badge) — obwohl der Free-Scraper **strukturell host-blind** ist (`host_listings_count` durchgehend null, `is_pro_host` hartcodiert false). Der Quervergleich belegte: Zürich real **~61% Profi-Hosts**, das Tool zeigte 0%.

**Fix:** Pro Markt `hostKnown = listings.some(host_listings_count != null || is_pro_host === true)`. Ist die Host-Info nicht erfasst → Anzeige **„n/v 🔴"** (mit Tooltip + InsideAirbnb-Referenz) statt einer Fake-0. **17 BD-gescrapte Märkte** (Zug 41, Gstaad 5, Aarau 6 …) behalten ihren echten Profi-Anteil; **60 Free-Scrape-Märkte** (Zürich, Luzern, Bern …) zeigen jetzt ehrlich „nicht messbar". Browser-verifiziert: Zürich → „n/v / Profis 🔴 nicht erfasst", Zug → „32 Vollzeit-Profis" (entire-gefiltert), 0 Konsolenfehler.

**Roter Faden:** „Tier an jedem Wert" — eine 0, die „nicht gemessen" bedeutet, ist eine Lüge im Entscheider-UI. Offen im Audit: Markt-Anzahl-Inkonsistenz (Hero-Pill hardcodet 81 vs `markets.length`/197), ADR-Mehrfachrechnung-Check.

## [0.9.98] — 2026-06-10 — Cross-Check Free-Scrape ↔ InsideAirbnb (zwei Quellen, keine Bodenwahrheit)

`tools/calibrate_insideairbnb.py`: vergleicht den Free-Scrape eines Markts gegen den InsideAirbnb-Snapshot mit **derselben Methode** (`occupancy_proxy`, Radius, Entire-Filter), damit die Differenz die Daten misst, nicht die Rechnung. **Prämisse (Adrian):** InsideAirbnb ist NICHT die Wahrheit — pro Metrik wird gefragt, welche Quelle glaubwürdiger ist (Frische vs. Coverage). Frische-Check (jüngstes `last_review`), Zombie-Filter (0 Reviews + kein Preis raus), Pro-Host als einzige Metrik wo InsideAirbnb klar besser ist. Report → `data/insideairbnb-calibration.json` (dict-of-markets). **Zürich-Befund:** ADR Free 217 vs IA~166 USD (+31%, IA-Snapshot 2025-09 alt → uns glauben); Occupancy 31.6% vs 22.5%; **Pro-Host Free 0% vs IA 61%** (1484/2438) = bewiesene Blindstelle; Coverage 33 vs 2438. InsideAirbnb-CSV bleibt gitignored (Rohdownload).

## [0.9.97] — 2026-06-10 — Tier-A Map-Bounds: Geo-Bleed an der Quelle strukturell eliminiert

Der bisher in CLAUDE.md als offen markierte Free-Scraper-Geo-Bleed (Genève→Kentucky, Wädenswil→Kanada bei Namenskollision) ist **strukturell gelöst** — nicht mehr nur per nachgelagertem Distanzfilter, sondern an der **Quelle**: die Airbnb-Suche wird auf eine **Map-Bounding-Box** (`ne_lat/ne_lng/sw_lat/sw_lng`) aus dem **eigenen Marktzentrum** (`market-centers.json`) + Radius eingeschränkt, daher liefert Airbnb nur noch Inserate IM Rechteck.

**`bounding_box(center, radius_km)` + `bbox_zoom(radius_km)`** (`fetch_airbnb.py`): Bounds aus Zentrum/Radius, `dlng` um `cos(lat)` korrigiert (Längengrade schrumpfen polwärts). **Quadtree-BBox-Sweep** im Free-Scraper kommt über Airbnbs ~300-Listing-/15–17-Seiten-Deckel hinweg (rekursive Box-Teilung).

**Preflight Tier-A-bewusst** (`run_free_scraper_preflight(market, query, bbox)`): mit Bounds → `preflight_status="ok"`, `place_selection_status="synthetic_bounds"`, `geo_filter_mode="map_bounds"`, `source_tier_max="usable"`. Ohne Bounds (Markt nicht in `market-centers.json`) Rückfall auf alt: `missing` / `exploratory`. **Ehrlichkeits-Grenze bleibt:** Bounds sind SYNTHETISCH (eigener Geocode, NICHT Airbnbs bestätigte Place-ID), Kalender fehlt weiter → **nie `decision_grade`**, max `usable`. `source_tier_from_geo` jetzt `has_bounds`-bewusst (ohne Bounds max `exploratory`).

**Live-Beweis (echter Re-Scrape, gratis, vs. alter posthoc/radius-Modus):**
- **Genève:** inMkt **0% → 100%**, median-Distanz **8'118 km → 1.58 km** (Kentucky-Bleed weg), ADR-Median 198.
- **Wädenswil:** inMkt **0% → 89%**, **7'650 km → 5.71 km** (Kanada-Bleed weg).
- **Grenchen:** inMkt 73% → **100%**, 4.2 km → **0.78 km**.
- **Luzern:** neu erfasst, n bis **172**, inMkt 76–93%, ADR-Median ~283–341.

**Run-Log:** `data/airbnb-scrape-runs.json` (Contract-Artefakt — pro Lauf run/signature inkl. `listing_ids_hash`, `median_distance_km`, `in_market_share`, `geo_filter_mode`) belegt posthoc-vs-map_bounds nachvollziehbar. py_compile beider Scraper sauber; Display-Layer mit neuen `airbnb-competitors.json`/`-insights.json` browser-verifiziert (Markt rendert, 0 Konsolenfehler, Datenform unverändert).

**Offen (nächster Schritt):** InsideAirbnb-Zürich-CSV (lokal als Ground-Truth gezogen, noch nicht verdrahtet → gitignored) als Kalibrier-Cross-Check für die map_bounds-ADR/Occ einhängen; `market-centers.json`-Abdeckung über die kuratierten Zentren hinaus erweitern (sonst Rückfall auf `exploratory`).

## [0.9.96] — 2026-06-09 — Free-Scraper: hartes Preflight-Gate (keine Place-Selection → nie decision-grade)

Keine Autocomplete-Integration, keine neue Architektur. Verhindert nur, dass eine Textquery als bestätigte Airbnb-Place-Selection durchgeht.

**`run_free_scraper_preflight(market, query)`** (in `fetch_airbnb_free.py`): da der Free-Scraper KEINE Place-Selection macht (kein Autocomplete/Place-ID/Bounds), liefert es immer `place_selection_status="missing"`, `preflight_status="warning"`, `source_tier_max="exploratory"`, `geo_filter_mode="posthoc_radius_only"`, `no_airbnb_place_selection=true`, blocking_reasons + required_next_step (BD/Browser/Map-Bounds/Place-ID).

**`source_tier_from_geo(in_market_share)`** (Post-Scrape): **0% → `unusable`** (keine Markt-/ADR-/RevPAR-/Ökonomik-Aussage, Brief „Free-Scraper ungeeignet…") · **1–69% → `exploratory`** (nur Hinweis/Beobachtung) · **≥70% → `usable`** (max — **nie `decision_grade`**, weil Place-Selection fehlt → Brief „vor Entscheid mit BD/Place-ID bestätigen"). Run-Metadaten + Markt-Eintrag tragen `place_selection_status`/`source_tier`/`source_tier_max`/`no_airbnb_place_selection`/`strategy_brief`.

**Test (live, Gate aktiv):** Wädenswil 0% → **unusable**; Genève 0% → **unusable**; Grenchen 74% → **usable** (nicht decision-grade); Biel/Bienne 100% → **usable** (nicht decision-grade). Alle 4 preflight `warning · missing · max-tier exploratory`. py_compile sauber, keine Python-Fehler.

## [0.9.95] — 2026-06-09 — Live-Validierungs-Scrape: Scraper Contract bewiesen

### Echter Re-Scrape (gratis) für 4 Märkte — geo-saubere Inputs nachgewiesen

Kein Cube-/UI-Code. Kontrollierter Live-Scrape mit dem neuen Contract (nur `fetch_airbnb_free.py`, kein BD/Geld). Backup vorher unter `data/raw/backup_pre_contract_scrape/`.

**Resultat — der Contract wirkt genau dort, wo er soll:**
- **Grenchen:** präzise Query „Grenchen, Solothurn, Switzerland" geokodiert sauber → **Geo-Bleed Critical→Medium, in-radius 0→73%**, cubeADR **185→133** (das Berner-Oberland-**Artefakt 364 ist weg**, echte Grenchen-Preise), Status Beobachtbar→**Testbar**, Business jetzt ehrlich **Negativ** (occ 11%).
- **Biel/Bienne:** „Biel, Bern, Switzerland" → **100% in-radius, n_preise 0→37**, Price-Trust 8→55, Status→**Testbar**, Demand bleibt getrennt (84). Preisbasis sauber aufgebaut.
- **Wädenswil / Genève:** Airbnbs Free-Endpoint liefert für diese Queries weiterhin **globalen Fallback** (Florida/Kanada/Brasilien/Schottland) statt der Schweiz — der **Geo-Filter blockiert das korrekt** (0 in-radius, ∅ Daten, bleibt Critical). Keine falsche ADR. Braucht BD `--discover`/Map-Bounds.

**Bug-Fixes (an der Quelle gefunden):** `precise_query` sanitiert „/" (Biel/Bienne → 404 behoben) und vermeidet Kanton==Markt-Dopplung (Genève); URL-Quoting `safe=''`; `append_history`-Pfad sanitiert „/" (`biel-bienne.jsonl` statt Unterordner); Kanton-Schreibweise „Zürich" statt „Zuerich" in `market-centers.json`.

**Contract-Audit bestanden:** run_id/query/market_center/radius/geo_filter_mode · listing distance/in_radius/price_mode/price_raw/normalized_nightly_price/captured_at · snapshotSignature (result_count/listing_ids_hash/adr_median/in_market_share/price_mode_share) — nichts erfunden (Genève listing 9366 km/out-of-radius ehrlich). 0 Console-Fehler.

**Offen:** Wädenswil/Genève brauchen BD-Discover oder Map-Bounds (Free-Query reicht nicht); Luzern-Agglo (Horw/Kriens/Emmen/Meggen) bewusst NICHT free-gescrapt (würde BD-Kalender→Review-Proxy regressieren).

## [0.9.94] — 2026-06-09 — Scraper Contract in den Python-Scrapern umgesetzt

### Reproduzierbare, vergleichbare, geo-saubere, kalendertaugliche Scrapes — additiv, rückwärtskompatibel

Umsetzung von `docs/scraper-contract.md` in `fetch_airbnb.py` (BD) + `fetch_airbnb_free.py` (gratis). Keine Cube-/UI-Änderung; alle bestehenden JSON-Keys bleiben, Contract-Felder kommen dazu.

**Geo-Schutz an der Quelle (E):** neue `data/market-centers.json` (Marktzentren + Kanton + Radius). Helfer `haversine_km`, `enrich_geo` (markiert je Listing `distance_to_market_center_km` + `in_market_radius`, **löscht nichts**), `precise_query` (gegen Namenskollision: „Grenchen, Solothurn, Switzerland" / „Genève, Switzerland"). Der Free-Scraper sucht jetzt mit präziser Query und berechnet Aggregate **bevorzugt aus in-radius**-Listings (Rohdaten bleiben vollständig in `listings`). Validiert (Mock): Grenchen 0% in-radius / Median 68.75 km, Emmen 100% / 1.15 km, Genève 0% / 7090 km.

**Snapshot-Signatur (D):** `build_snapshot_signature` pro Lauf — market/timestamp/query/check_in/out/stay_length/currency/room_type/geo_filter_mode/radius/result_count/listing_ids(+hash)/median_distance/in_market_share/adr_median/adr_iqr/entire_home_share/calendar_share/review_share/price_mode_share. Run-Metadaten via `build_run_metadata`, Append-only-Log `data/airbnb-scrape-runs.json` (`append_scrape_run`, additiv).

**Preis-Normalisierung (F):** `price_contract` → `price_raw` · `price_currency` · `price_mode` (nightly/stay_total/unknown) · `normalized_nightly_price`. Free-Scrape: stay_total ÷ stay_length; BD: nightly direkt, sonst stay_total ÷ Fenster. Unklar → „unknown" (Evidence-Cube deckelt dann Price).

**Kalender-Felder (G):** je Listing `available_nights` · `unavailable_nights` · `calendar_window_days` · `calendar_snapshot_date` · `captured_at` (BD aus `available_dates`; Free = null, kein Kalender).

**Output (H):** rückwärtskompatibel — bestehende Dateien/Keys unverändert, Contract-Felder additiv im Listing + Markt-Eintrag (`scrape_run`, `snapshot_signature`, `geo`); neue Datei nur `airbnb-scrape-runs.json` (additiv, vom JS nicht gelesen). Geprüft: `py_compile` sauber, Mock-Dry-Run für Grenchen/Emmen/Genève ohne Python-Fehler.

**Offen:** echter Re-Scrape der Geo-Critical-Märkte (Grenchen/Wädenswil/Genève) mit präziser Query; Kalender-Snapshots über 14–30T; `airbnb-trends.json`-Aggregate künftig aus in-radius.

## [0.9.93] — 2026-06-09 — Scraper Contract / Data Acquisition Standard

### „Kein Snapshot ohne Signatur, kein Vergleich ohne gleiche Parameter, kein Trust ohne reproduzierbaren Scrape."

Keine neue Cube-Logik, keine neue UI: der nächste Schritt liegt an der Datenquelle. Verbindlicher Scrape-Standard + Vergleichbarkeits-Funktionen, damit **Parameter-Drift nicht mit Platform-Drift verwechselt** wird.

**`docs/scraper-contract.md` (Haupt-Deliverable):** verbindlicher Standard pro Scrape-Lauf — Query-/Geo-/Result-/Preis-/Kalender-/Listing-Kontext + `snapshotSignature`. Plus: vorhanden-vs-fehlt-Bilanz, Calendar-Tracking-Datenmodell, Pipeline-Nächste-Schritte.

**`compareScrapeSignatures(prev, cur)`:** prüft, ob zwei Snapshots vergleichbar sind. **Unterschiedliche Parameter (StayLength/Currency/Query/Geo/PriceMode/RoomType) sind BLOCKIEREND** → `{comparable, comparabilityScore, driftReasons, blockingDifferences}`. Belegt: 7N vs 30N → comparable=false (kein Platform-Drift, sondern Parameter-Drift).

**`calculateListingOverlap(prev, cur)`:** `{overlapCount, overlapShare, newListings, missingListings, stableListings}` aus listingIds; tiefer Overlap bei gleichen Parametern → Drift-/Geo-Verdacht. (Braucht listingIds-je-Snapshot — Contract.)

**Platform-Drift gegated (C):** `calculatePlatformDrift` prüft jetzt ZUERST `compareScrapeSignatures` der letzten zwei Läufe; nicht vergleichbar → Platform-Drift = `unbekannt` + Warnung „Parameter vereinheitlichen". Heute: Params nicht gespeichert → nicht-blockierend, gleiche Pipeline angenommen → Zug bleibt Critical (keine Regression).

**Geo-saubere Brief-Präzision (E):** Geo-Critical-Scraper-Brief enthält jetzt die präzise Query gegen Namenskollision — „Grenchen, Solothurn, Switzerland", „Genève, Switzerland" (nicht USA), „Wädenswil, Zürich, Switzerland" — + Distanz-Filter aufs Marktzentrum.

**Sofort geo-sauber neu scrapen:** Grenchen, Wädenswil, Genève (+ Geo-High: Solothurn, Städte). **14–30T Calendar-Tracking:** Horw/Emmen/Zug/Meggen/Baden (hohe Reviews-vs-Kalender-Divergenz) + Review-Proxy-Märkte. 0 Console-Fehler.

## [0.9.92] — 2026-06-09 — Evidence Cube: Zeitdimension (Platform Drift + Kalenderbewegung)

### „Misst der Scrape heute noch gleich wie beim letzten Lauf?"

Der Evidence Cube (v0.9.91) bekommt die Zeitdimension — kein neuer Assistent, keine zweite Ökonomik. Aus vorhandenen Daten abgeleitet, wo messbar; sonst sauber als spec/prepared markiert.

**Platform-/Scraper-Behavior-Drift (REAL, `calculatePlatformDrift`):** aus `AIRBNB_TRENDS.series` — wechselt die Scrape-Komposition (Supply/ADR/n_preise) run-to-run? `_scrapeSignature(m)` erfasst die Lauf-Signatur. Level Low/Medium/High/Critical. **Befund:** Zug Supply 70→24→47, ADR **163 vs 280** je Lauf → Critical; Emmen 10→5, Horw/Kriens/Baden High. Critical Platform-Drift = SOFTER Deckel (Price/Demand auf 50, Source −15, Bias +12) und Strategy-Status max Testbar — **selbst der „Sehr attraktiv"-Markt Zug wird auf Testbar gestuft, Scraper-Brief „Query/Radius fixieren, Signaturen vergleichen"**. (<2 Snapshots → unbekannt.)

**Calendar-vs-Review-Drift (REAL, `calculateCalendarVsReviewDrift`):** je Listing `occ_calendar_pct` vs `occ_reviews_pct` — widersprechen sich die zwei Auslastungs-Methoden? Ø-Divergenz → Level. Befund: Horw Critical, Emmen/Zug/Meggen/Baden High → Reviews nur als Plausibilisierung, Demand vorsichtiger (−7/−12) + Bias.

**Calendar-Movement/Booking-Velocity (`calculateCalendarMovementIntegrity`):** SPEC/vorbereitet — braucht per-Listing-Kalender-Historie (client-seitig nicht geladen); schwacher Proxy aus Markt-occ-Bewegung; flaggt 14–30T-Calendar-Tracking.

**Vorgeschaltet (E/F):** Price-Trust ← priceEvidence (hart) + Platform-Drift (soft); Demand-Trust ← geo (hart) + Platform-Drift (soft) + Calendar-vs-Review; Source Reliability ← Platform-Drift; Bias/Noise ↑ Platform-Drift/CalVsReview/Host/Quality. Aggregat `calculateOverallEvidenceIntegrity` erweitert um calendarMovementTrust/calendarVsReviewDrift/platformDriftTrust/scraperSignature.

**Strategy-Engpass-Priorität:** Geo > Platform-Drift > Preis > Demand. Critical Platform → Scraper-Brief „stabilisieren"; Geo-Critical → „Radius eingrenzen"; sonst Preis/Kalender. UI: Datenintegritäts-Block um Kalenderbewegung · Reviews-vs-Kalender · Platform-Drift erweitert.

**Scraper-Daten-Standard (K)** als Code-Kommentar fixiert (pro Lauf: Signatur Supply/ADR/Geo/RoomType/Currency; pro Listing: Koordinaten/Distanz/Kalender-Historie/Preis-Modus). Fehlt heute v.a.: per-Listing-Kalender-Historie + gespeicherte Scrape-Signatur je Lauf.

**Wirksamkeit (13 Märkte):** Grenchen/Wädenswil/Genève geo-Critical → blockiert; Zug/Emmen platform-Critical → demotiert + „stabilisieren"; saubere Märkte sichtbar. 0 Console-Fehler.

## [0.9.91] — 2026-06-09 — Evidence Cube (Datenintegrität vor Trust/Economics)

### „Keine Ökonomik ohne Datenintegrität" — Evidence-Subcube vorgeschaltet

Kein neuer Assistent, keine zweite Ökonomik: der Master Cube bekommt eine **vorgeschaltete Datenintegritäts-Schicht**. Reihenfolge jetzt: Daten → **Evidence Cube** → Trust → Economics → Strategy. Der Evidence Cube rechnet nichts, er bewertet nur die Qualität der Eingangsdaten und deckelt Trust.

**9 Integritäts-Aspekte** (je Trust 0–100 + Ampel), aus echten Listing-Feldern abgeleitet: `calculateGeoIntegrity` (Geo-Bleed) · `calculateListingTypeIntegrity` (entire-Share) · `calculateCalendarIntegrity` (occ_method) · `calculateSeasonIntegrity` (_adrCal unanchored) · `calculateDuplicateHostIntegrity` (Host-Konzentration, nur BD-Scrapes) · `calculateQualityIntegrity` (Schlafzimmer-Spanne/Profi-Share) · `calculateStayLengthIntegrity` + `calculatePriceNormalizationIntegrity` (spec/light — Scrape liefert nur ein 7N-Fenster) · `calculateMarketBoundaryIntegrity` (≈ Geo). Aggregat `calculateOverallEvidenceIntegrity` → `{geo/listingType/stayLength/season/priceNormalization/calendar/duplicateHost/quality/boundary-Trust, priceEvidence, demandEvidence, overallEvidenceIntegrity, evidenceGates, evidenceWarnings}`.

**Vorgeschaltet (C):** Price-Trust wird durch `priceEvidence = min(Geo, Objektart, Saison, Preis-Norm)` gedeckelt (≤25 → Deckel 30; ≤50 → Deckel 55) — ersetzt den bisherigen inline-Geo-Cap (konsolidiert, kein Doppelzählen). Demand-Trust durch Geo-kritisch (Deckel 40). Bias/Noise steigt bei Geo-Bleed (+15), Host-Konzentration (+8), Qualitäts-Heterogenität (+6), Review-Proxy statt Kalender (+5). Economics erbt via min(Demand, Price).

**UI (F):** kompakter Detail-Block „🔬 Datenintegrität (Evidence Cube)" mit Ampel je Aspekt + „Gesamt: nicht belastbar / eingeschränkt / belastbar für Ökonomik" + Preis-/Demand-Evidenz. Keine grosse Tabelle.

**Wirksamkeit (13 Testmärkte):** Grenchen/Wädenswil/Genève → Geo kritisch, Preis-Evidenz 20 → Economics 30 → „∅ Daten" (Ökonomik blockiert, gap=geo). Solothurn Geo schwach → Preis-Evidenz 45 → „Knapp +". Emmen/Kriens/Zug/Horw → Geo+Kalender stark, Demand-Evidenz 90 sichtbar; Zug „Sehr attraktiv". Kloten → Demand-Engpass = Kalender (Review-Proxy). 0 Console-Fehler.

## [0.9.90] — 2026-06-09 — Cube-Assistent v1 abgeschlossen

### Abschlussrunde: Geo-Bleed + Kalender als Evidence-Bausteine, Wirksamkeit belegt

Stabilisierung + die zwei offenen Themen minimal-real aus vorhandenen Daten abgeleitet (keine neue Feature-Schicht, Scores nur aus bestehender Logik).

**Geo-Bleed (`geoBleed`, neuer Evidence-Baustein):** Airbnb erweitert bei dünnen/namenskollidierenden Orten den Suchradius → der Scrape misst „Markt + Umgebung". Pro Listing liegen Koordinaten vor; `marketCenterLatLng` (COMMUNES 93 + kuratierte Zentren) erlaubt `haversineKm`-Distanz → `inMarketShare`, `geoBleedScore` (Low <10% / Medium <30% / High <60% / Critical außerhalb 8km-Radius). **High/Critical deckelt Price-Trust** (Critical→30) und erzeugt einen **Geo-Scraper-Brief** (Radius/Polygon/Gemeindegrenze eingrenzen) statt eines Preis-Briefs. **Befund — Root-Cause vieler Artefakte:** Grenchen-Listings 68 km weg (Berner Oberland), **Genève → Kentucky/USA**, **Wädenswil → Italien + Kanada** (Median 8'126 km) — diese hatten scheinbar hohe n_preise, maßen aber Fremdorte. Saubere BD-Scrapes (Emmen/Kriens/Zug) Low, 100% im Radius.

**Kalender (`calendarSignal`, STR-Demand-Baustein):** `occ_method` je Listing — `calendar` (scharfe Belegung) vs `reviews` (Proxy, weich). Pro Markt Kalender-Anteil; im Detail sichtbar (Auslastungs-Quelle), im Demand-Scraper-Brief priorisiert (Kalender vor Preis, wenn Demand schwach + kein Kalender). Emmen/Kriens/Meggen/Horw/Zug/Baden/Aarau = Kalender, Grenchen/Kloten/Biel/Wädenswil = Review-Proxy.

**UI:** Market-Tabelle zeigt Median-Cashflow zusätzlich pro Monat. Detail-Block „Nachfrage-Quellen getrennt" zeigt Geo-Bleed-Level + Auslastungs-Quelle + Geo-Warnung bei High/Critical. Architektur-Block (in-Code) + CLAUDE.md um Geo/Kalender + v1-Regeln/Definition-of-Done ergänzt.

**Wirksamkeit belegt (12 Testmärkte):** Grenchen Geo-Critical→Price 30→„∅ Daten" (Artefakt an der Wurzel gekillt); Kloten business_airport-Blend; Emmen/Kriens/Meggen/Horw residential_spillover intakt; Zug „Sehr attraktiv"; Critical-Drift-Gate, aspekt-getrennter Trust, raw/cube/drift alle wirksam. Strategy Queue: Biel/Meggen/Kriens/Emmen/Horw oben (price), Genève/Lausanne/Fribourg (geo) — Grenchen/Kloten korrekt nicht Top. 0 Console-Fehler.

## [0.9.89] — 2026-06-09

### Entscheider-UI: „Was verdient man?" zuerst — Trust und Realität sichtbar getrennt

Reine UI-Übersetzung der bestehenden Cube/Trust/Strategy-Logik (keine neue Datenlogik, keine neuen Scores) im Cube-Assistenten.

**Earnings-Headline (Markt-Detail, ganz oben):** dunkle Karte „💰 Was verdient man?" mit Bottom-30 / Median / Top-10 R2R-Cashflow je Jahr **und** Monat, cubeADR, Cube-Auslastung, cubeRevPAR, Ökonomik-Vertrauen + ein Klartext-Fazit. Alle Werte aus `getCubeOutputs` (median/top10/bottom30 cashflow) — nichts neu gerechnet.

**Business-Klassifikation** `classifyBusiness(m)` — rein abgeleitet aus Cube-Cashflow + Ökonomik-Trust-Gate (keine neue Logik): **Nicht belastbar wegen Datenlage** (Ökonomik-Vertrauen ≤30) · **Negativ** · **Nur Top-10-operatorfähig** (Median ≤0, Top-10 >0) · **Knapp positiv** · **Attraktiv** · **Sehr attraktiv**. Je mit Fazit-Satz.

**Trust und Realität getrennt (Begriffe):** „Demand/Price/Ökonomik" → **Nachfrage-Vertrauen / Preis-Vertrauen / Ökonomik-Vertrauen** (mit „/100" + Tooltip „Vertrauen ≠ Höhe — misst die Verlässlichkeit der Aussage, nicht den Wert"). Operative Werte (cubeADR, Cube-Auslastung, cubeRevPAR, NOI, Cashflow) klar separat. Tooltips für Cube-Auslastung und Ökonomik-Vertrauen.

**Detail neu strukturiert (Reihenfolge):** 1 Earnings-Headline → 2 Aussage-Vertrauen (3 Aspekte + Gates + Unsicherheit) → 3 Operative Cube-Werte → 4 Methodik/Datenlage → 5 Raw→Cube→Drift + Nachfrage-Quellen → 6 Kausalität/Bias/Strategie → 7 Scraper-Brief.

**Market Trust Table:** neue Spalten **Business-Fazit · Median CF/J · Top-10 CF/J**; Trust-Header „Nachfrage-V. / Preis-V. / Ökonomik-V."; Cashflow kursiv+grau wenn Datenlage nicht belastbar.

**Validiert (11 Testmärkte):** Wädenswil Median −183/Top-10 +2'392 → „Nur Top-10-operatorfähig"; Zug +16'477 → „Sehr attraktiv"; Solothurn +366 → „Knapp positiv"; Horw/Kriens/Emmen/Meggen/Biel (n_preise≤1) → „Nicht belastbar wegen Datenlage" (Cashflow gemutet). Earnings vor Trust, Nachfrage-Vertrauen klar nicht als Auslastung lesbar. 0 Console-Fehler.

## [0.9.88] — 2026-06-09

### Horw-Integrationslücke geschlossen — gescrapter Markt läuft jetzt durch den Cube

Horw hatte Airbnb-Daten (`AIRBNB_COMP`/`AIRBNB_TRENDS`), fehlte aber im `markets`-Array → lief durch keine Cube/Trust/Drift/Strategy-Logik. Jetzt als eigener Markt in `js/data.js` ergänzt (kein neues Feature, keine neue Logik).

**Baseline (kein Fantasiewert):** identisch zu den Luzern-Agglo-Peers Emmen/Kriens/Meggen — `{ canton:"LU", listings:50, adr:160, occ:55, revpar:88, grade:"D", profile:"summer", peak:"August", tags:["See","Luzern-Agglo"], cat:"Stadt" }`. adr/occ/revpar = konservative Modell-Baseline (rawADR/rawOcc/rawRevPAR); kein BFS/HESTA-Match (daher kein Leerstand/Zweitwohnung); Kantonsmiete LU via `computeRentBenchmark`. Vorhandene Airbnb-Daten (occ ~70 %, adr_n=1) layern via `occOf`/Kalibrierung drüber. `marketProfile` = `residential_spillover` (bereits im `_LUZERN_AGGLO`-Set).

**Resultat (durch die bestehende Logik, nicht schöngerechnet):** rawOcc 55 → cubeOcc 70 (STR-Signal sichtbar, Drift High), rawRevPAR 88 → cubeRevPAR 113. Demand 75 (sichtbar), Price 29 / Economics 29 (n_preise=1 → Gate „n_preise<3 Deckel 30" + „ADR nicht verankert Deckel 40"). Status **„Beobachtbar"** — NICHT belastbar priorisierbar. Scraper-Brief: Ziel ≥15 ganze Einheiten mit Preis, Prio hoch, vgl. Luzern/Vitznau/Weggis. Erscheint in der Strategy Queue (Platz 5, Uplift 46). Keine neuen Critical-Artefakte; Emmen/Kriens/Meggen unverändert.

Zusätzlich: Cache-Bust-Tag `js/data.js?v=0988` (verhindert stale data.js nach Refresh, Dev + Prod).

## [0.9.87] — 2026-06-09

### Methodische Härtung: Critical-Drift-Gate · ADR-Artefaktschutz · profilabhängige Occ-Quelle

Vier Fixes aus der Stabilisierungsrunde — keine neuen Features, nur Härtung gegen Artefakte. Leitsatz: hohe Stichprobe heiligt keinen unplausiblen Wert; Critical Drift blockiert starke Aussagen; Quellenpriorität passt zum Marktprofil.

**Fix 1 — Critical-Drift-Gate:** `calculateEconomicsTrust` deckelt Economics Trust auf max. 50, sobald ADR- **oder** RevPAR-Drift `Critical` ist (+ Gate-Warnung „Preisniveau/Ökonomik nicht belastbar – Kalibrierung/Quelle prüfen"). Da die Empfehlung auf Economics gated, kann der Strategy-Status dann nicht mehr „Belastbar priorisierbar" sein (max. Testbar/Beobachtbar). econ.gates werden in `trust.gates` sichtbar gemacht.

**Fix 2 — ADR-Kalibrierung gegen Artefakte:** In `calibrateAdrFromAirbnb` wird `calAnnual = Fenster-ADR ÷ Saisonfaktor`; bei Saisonfaktor <1 bläht das den ADR auf. Neuer Schutz: weicht `calAnnual` >40 % vom Profil-Modell-ADR ab, wird das Kalibrier-Gewicht gedämpft (`wEff`, Floor 0.2); ab 60 % gilt die Kalibrierung als `unanchored`. `calculatePriceTrust` deckelt unanchored-ADR trotz hoher n_preise auf 55 (Source-Größe ≠ Source-Validität). → **Grenchen cubeADR 364→185, cubeRevPAR 218→111, Economics 73→50, Status „Belastbar priorisierbar"→„Testbar".**

**Fix 3 — profilabhängige Occ-Quelle + Hotel/STR-Trennung:** Neue Klassifikation `marketProfile(m)` (resort_tourism · residential_spillover · business_airport · city_hotel_market · mixed_midland · unknown) + saubere Begriffe `hotelDemandBaseline(m)` (BFS) und `strDemandSignal(m)` (Airbnb) — sie messen verschiedene Märkte. `marketRealStats` blendet **nur** für `business_airport` bei BFS≫STR-Konflikt zu einer BFS-gewichteten `cubeOcc` (0.6·BFS+0.4·STR); alle anderen Profile unverändert (minimale Streubreite: 4 Märkte). `calculateDemandTrust` senkt Demand bei Quellenkonflikt (business/city/midland, ≥15pp) statt blind eine Quelle zu wählen; Wohn-Spillover/Resort ausgenommen. → **Kloten: Hotel-Baseline 50 % / STR-Signal 29 % / cubeOcc 42 %, Demand 84→44, Economics 83→44, Status „Belastbar priorisierbar"→„Testbar", Konflikt sichtbar.** Detailpanel zeigt neuen Block „Nachfrage-Quellen getrennt" (Hotel-Baseline · STR-Signal · Cube-Auslastung · Quellenkonflikt + Profil-Interpretation).

**Fix 4 — Horw:** Integrationslücke nur dokumentiert (kein Code): Horw hat Airbnb-Daten (Comp/Trends), fehlt aber im `markets`-Array → läuft durch keine Cube/Trust-Logik. Vorschlag als separater kleiner Fix.

**Validierung:** Solothurn (Critical RevPAR-Drift) → econ 50/„Testbar"; Emmen/Kriens/Meggen (Wohn-Agglo) unverändert „Beobachtbar"; Baden/Aarau n_preise<5-Gate wirkt weiter (price 50). Strategy Queue plausibler (Biel/Meggen/Kriens/Emmen oben statt Artefakt-Märkte). 0 Console-Fehler.

## [0.9.86] — 2026-06-08

### Cube durchdringt das Projekt — raw/cube/drift für ADR, Occ, RevPAR + sichtbare Kennzeichnung

Alle operativen STR-Werte laufen jetzt durch den Cube; Rohdaten bleiben als Evidenz mit Drift sichtbar.

**Kanonische Accessoren (raw/cube/drift) für alle drei Kennzahlen:**
- `cubeADR(m)`=m.adr (kalibriert) · `rawADR(m)`=m._adrModeled · `adrDrift(m)`
- `cubeOcc(m)`=occOf(m) (operativ) · `rawOcc(m)`=m.occ (Modell, nie überschrieben) · `occDrift(m)`
- `cubeRevPAR/rawRevPAR/revparDrift` (aus v0.9.85)
- `classifyDrift(absPct)` → **Low (<8%) / Medium (<20%) / High (<40%) / Critical (≥40%)**; `marketDriftLevel(m)` = schlimmster Drift über die drei.

**Audit-Mapping (operative Raw-Reads umgestellt):**
| Ort | Fläche | vorher | jetzt |
|---|---|---|---|
| `drawMap` Badge | Karte (Occ-Metrik) | m.occ | cubeOcc |
| Karten-Tooltip | Map-Popover | m.occ | cubeOcc + „Cube" |
| Cashflow-König `filter` | Strategie-Liste | m.occ≥60 | cubeOcc≥60 |
| Hidden-Gem `whyTemplate` | Strategie-Card | m.occ | cubeOcc |
| Trend-Surfer `sortBy` | Ranking | m.occ | cubeOcc |
| Markt-Detail KPIs | mdRevpar/mdAdr | „MOD" | „● Cube" + Drift-Chip |

`drawMap`-Wertfunktion (Occ-Färbung) und Markt-Detail-mdOcc nutzten bereits `occOf` (Cube). Der Anomalie-Detektor vergleicht **bewusst** Modell-occ vs BFS (eigene Drift-Logik, bleibt Roh). `m.adr` ist projektweit der kalibrierte cubeADR (operativ) — nur Roh/Drift ergänzt.

**Drift sichtbar & nutzbar (E + F):**
- Markt-Detail-KPI-Badges: „● Cube / operative Berechnung" (RevPAR), „● Cube"/„● Modell" (ADR), Drift-Chip „⚠ Drift High/Critical" mit Roh→Cube-Tooltip.
- Cube-Assistent-Detail: Tabelle **Roh (Quelle/Modell) → Cube (operativ) → Drift** für ADR/Auslastung/RevPAR, je mit Level-Badge.
- Cube Health: Panel „Modell-vs-Cube-Drift (Qualitätssignal)".
- **Cube Reliability** zieht High/Critical-Drift jetzt als Eingabe-Unsicherheit ab (−7/−12) — Drift wird zum Score-wirksamen Signal, nicht nur Anzeige.

**Schatten-Berechnungen (markiert, nicht still):** `compSetForMarket` (Mock-Vergleichs-Listings, low) und `redrawEarn`-Custom-Pfad (dupliziert strUnitEconomics, med) bleiben in `detectShadowCalculations` ausgewiesen → im Cube-Health-Block sichtbar.

Effekt: Städte zeigen jetzt cube-ehrliche Auslastung (Zürich Roh 72% → Cube 32%, Critical Drift), Strategie-Filter selektieren entsprechend (Cashflow-König 5, Hidden Gem 9, cubeOcc≥60 = 10 Märkte). Keine zweite Wahrheit, kein Rohdatenverlust. 0 Console-Fehler.

## [0.9.85] — 2026-06-08

### Hebel #1 — RevPAR raw/cube/drift: eine operative Wahrheit, Rohwert bleibt Evidenz

`m.revpar` wird projektweit aus dem Cube abgeleitet (operative Rechenwahrheit), **ohne Rohdaten zu überschreiben**. Drei kanonische Helfer + Architektur-Doku im Code:
- **`rawRevPAR(m)`** = Quellenwert (data.js-Modell, basiert auf modellierter `m.occ`) — bleibt in `m._revparModeled` als Evidenz, nie überschrieben.
- **`cubeRevPAR(m)`** = `ADR × occOf/100` (tatsächlich genutzte Auslastung: Airbnb/BFS/Modell) = was der Cube rechnet; alle ~30 wirtschaftlichen Leser (Karte, Top-Tabelle, KPI, Scout, Empfehlungs-Filter, Default-Miete) sehen jetzt diesen einen Wert.
- **`revparDrift(m)`** = `cubeRevPAR − rawRevPAR` → **Qualitätsindikator** statt Bug: wie weit lag die Modell-Annahme neben dem Cube?

`calibrateAdrFromAirbnb` setzt `m.revpar = cubeRevPAR(m)` jetzt in **beiden** Zweigen (kalibriert + nicht-kalibriert) — vorher trugen nicht-kalibrierte BFS-Märkte den rohen Modell-RevPAR (basiert auf `m.occ` statt der echten `occOf`-Auslastung), was die „zweite Wahrheit" war. **Externe Snapshots** (`AIRBNB_TRENDS.latest.revpar_chf`) sind eine SEPARATE Roh-Messquelle und bleiben unverändert als 🟡 MOD gekennzeichnet.

**Effekt:** Cube-Health-Konsistenz **25/197 → 197/197**, Health-Score **50 → 89**. Der Modell-vs-Cube-Drift wird in Cube Health (Top-Liste) und im Markt-Detail (Roh/Cube/Drift-Zeile + „Roh bleibt als Evidenz") sichtbar. 183 Märkte mit nennenswertem Drift — z.B. Zürich Roh 155 → Cube 46, Bern 102 → 32: echte Airbnb-Daten (n=23–47) zeigen, dass das ursprüngliche Modell bei ADR und Auslastung zu optimistisch war. Kein Datenverlust, keine zweite Wahrheit. 0 Console-Fehler.

### Doku — Architektur der Assistenten-Schichten im Code festgeschrieben

Master-Kommentar über dem Assistenten: Cube = Rechenwahrheit · Trust Layer = Aussagekraft nach Aussageart (Demand/Price/Economics, Gates je Aspekt) · Pearl = Kausalität · Kahneman = Bias/Noise · Strategy/OODA = arbeitsfähige Diagnose + Informationsgewinnungs-Queue (kein To-do, Scraper-Briefs aus Trust/Pearl/Bias begründet).

## [0.9.84] — 2026-06-08

### Neu — 🎯 Strategy / Actionability Layer (Rumelt-Kern + OODA) + aussage-spezifischer Trust

Zwei zusammengehörige Erweiterungen des Cube-Assistenten (`index.html`, additiv, Vanilla).

**(1) Trust nach Aussageart getrennt** (gegen das pauschale „Markt ungenügend"). Statt eines Final Data Trust gibt es jetzt **Demand Trust** (Nachfrage/Auslastung — n_occ/BFS/Buchungen), **Price Trust** (ADR — n_preise/Kalibrierung) und **Economics Trust** = `min(Demand, Price, Cube-Struktur)`, weil RevPAR=ADR×Occ nur so stark ist wie die schwächste Säule. **Gates wirken je Aspekt:** n_occ→Demand, n_preise→Price. Effekt: eine schwache Preis-Stichprobe deckelt die Ökonomik-Aussage, entwertet aber die Nachfrage-Aussage NICHT mehr. **129 Märkte** haben jetzt eine belastbare/brauchbare Nachfrage-Aussage (Demand ≥ 51), während ihre Ökonomik mangels Preis-Sample „ungenügend" bleibt — vorher pauschal alle „ungenügend". Funktionen: `calculateDemandTrust`/`calculatePriceTrust`/`calculateEconomicsTrust`. Tabelle + Detail zeigen die drei Aspekte getrennt; Empfehlung gated auf Economics.

**(2) Strategy Layer** übersetzt die geprüften Cube-/Pearl-/Kahneman-Ergebnisse in Strategie & gezielte Datensuche — **kein Aktionismus, keine To-do-Liste.** Rumelt-Kern: `generateStrategicDiagnosis` (was sehen wir wirklich?), `generateGuidingPolicy` (Leitlinie), `generateCoherentActions` (zusammenhängende, info-getriebene Schritte). OODA: Observe (welche Daten) → Orient (Cube/Pearl/Kahneman) → Decide (verantwortbare Aussage) → Act (was suchen/scrapen). Kern-Logik `identifyInformationGap` leitet aus dem **bindenden** Trust-Engpass ab, welche fehlende Information die stärkste Aussage freischaltet; `rankInformationGaps`/`generateStrategyQueue` priorisieren über alle Märkte nach Trust-Uplift × Machbarkeit; `generateScraperBrief` erzeugt strukturierte Aufträge (Markt/Ziel/fehlende Kennzahl/Ziel-Stichprobe/Filter/Vergleichsmärkte/Priorität/erwarteter Trust-Nutzen/Befehl); `generateSearchQuestions` (offene Kernfragen aus Confoundern); `generateWorkableDecisionSummary` (Nicht entscheidbar/Beobachtbar/Testbar/Strategisch relevant/Belastbar priorisierbar). UI: Block 3 ist jetzt die **Strategy Queue** (priorisierte Informationssuche statt Aufgabenliste); Detailpanel zeigt Diagnose→Leitlinie→Aktionen, OODA-Raster, Entscheidungs-Status und vollen Scraper-Brief.

Bsp. Emmen (Nachfrage belastbar, n_preise=1): Status „Beobachtbar", Leitlinie „nicht auf Modell-RevPAR wetten — zuerst Preisbasis messen", Scraper-Brief Ziel ≥15 ganze Einheiten → Economics-Trust 30→~75 falls konsistent. Strategy-Queue-Top: Biel/Bienne (Uplift +58), Kriens (+56), Meggen (+55) — starke Nachfrage, nur Preis fehlt. 0 Console-Fehler.

## [0.9.83] — 2026-06-08

### Neu — Breiten-Scan (gratis) + Auslastungs-Quelle pro Perle markiert

**53 neue Märkte gratis erfasst** (`fetch_airbnb_free.py`, Review-Proxy, kein BD-Budget): Städte (Bern/Basel/Lausanne/Genève/Winterthur/St. Gallen/Lugano/Biel/Fribourg/Neuchâtel/Schaffhausen/Solothurn/Bellinzona…), Agglo (Kloten/Opfikon/Dübendorf/Uster/Wädenswil/Rapperswil/Meyrin/Vernier/Lancy) und Regionalzentren (Frauenfeld/Kreuzlingen/Arbon/Wil/Buchs/Lenzburg/Rheinfelden/Pratteln/Langenthal/Burgdorf/Köniz/Sursee/Yverdon/Morges/Nyon/Vevey/Martigny/Sierre…). Abdeckung **24 → 77 Märkte**, Perlen-Radar **13 → 66**. Neue Top-Kandidaten: Grenchen 91, Wil (SG)/Delémont 84, Pratteln 80, Rapperswil/Genève/Lausanne.

**Ehrlichkeit — Auslastungs-Quelle pro Perle:** Gratis-Scan liefert nur **Review-Proxy** (weicher), BD liefert echte **Kalender-Belegung** (scharf). Jede Perlen-Zeile trägt jetzt ein Tag: **📅 Kalender** (grün) vs **≈ Proxy** (grau) — damit ein Proxy-Score (z.B. Grenchen 91) nicht dieselbe Sicherheit vortäuscht wie ein Kalender-Score (Emmen 84). Proxy-Perlen = Kandidaten, gezielt mit BD-Discovery zu verifizieren. Strategie: Breite gratis, Tiefe gezielt BD.

## [0.9.82] — 2026-06-08

### Fix — Double-Counting in den Trust-Scores beseitigt (Ownership-Matrix)

Eine Schwäche wie kleine Stichprobe senkte bisher Source Reliability UND Cube Reliability UND Causal Plausibility UND Bias/Noise — plus Gate. Im geom. Mittel × Bias-Dämpfer × Gate wurde dieselbe Schwäche bis zu 5× durchmultipliziert → künstlicher Score-Kollaps. Neue **Ownership-Matrix** (als auditierbarer Code-Kommentar): jede Schwäche hat genau ein Zuhause, Echos sind bewusst und gedeckelt.

- **Stichprobengröße** (n_preise/n_occ) → HOME **Source Reliability** (volle Gradation). Echo nur in Bias/Noise (reduziert: +14/+9/+6 statt +30/+18/+10, als „Interpretations-Risiko") und im Gate (harte Decke). **Aus Cube Reliability entfernt** (n_preise<5-Malus weg) und **aus Causal reduziert** (Saison-Confounder −10→−6, Kalender-Snapshot −15→−8).
- **Cube Reliability** misst jetzt nur noch strukturelle Integrität: gemessen-vs-modellierte Inputs (gebündelt −9/−18 statt separater Occ/ADR-Strafen), m.revpar-Drift, Cashflow-Sensitivität, Wohnungsgrößen-Annahme.

Effekt: die 5 Scores messen wieder 5 verschiedene Dimensionen. Bsp. Emmen (n_preise=1): Source 94 (Auslastung *ist* gut gemessen) statt künstlich getankt — die Preis-Schwäche wirkt nur noch über das Gate (Deckel 30). Gstaad: Cube 85→95, Bias 36→27, Final unverändert 50 (jetzt gate-, nicht kollaps-getrieben). 188/197 „ungenügend" bleiben, aber gate-getrieben (ehrlich) statt durch Mehrfach-Bestrafung. 0 Gate-Verletzungen, 0 Console-Fehler.

## [0.9.81] — 2026-06-08

### Neu — 🔎 Information & Trust Layer (Reframe: Verlässlichkeit vor Empfehlung)

Der Cube-Assistent führt nicht mehr mit „was tun?", sondern mit **„wie verlässlich ist die Aussage?"**. Neuer Information-Retrieval- + Vertrauens-Layer, der reale Projekt-Daten pro Markt abgreift (`classifyDataSource` über Airbnb-Stichprobe, BFS/HESTA, Mietpreise, Leerstand, Zweitwohnung, Supply, Frische), klassifiziert und zu einer kanonischen Datenlage zusammenführt (`buildMarketEvidenceProfile`, `collectMarketEvidence`, `collectSourceMap`, `collectMissingData`).

**6 berechnete Vertrauenswerte pro Markt:** Evidence Completeness · Source Reliability · Cube Reliability (inkl. Input-Stärke + Sensitivitäts-/Konsistenz-Check, hier zeigt sich der m.revpar-Drift als Malus) · **Causal Plausibility (Pearl als Rechnung** — Korroboration durch unabhängige Quellen, Trend-Kohärenz, Confounder-Abzüge, Widerspruchs-Strafen) · **Bias/Noise Risk (Kahneman als Rechnung** — Small-Sample, Overconfidence, Survivorship, Base-Rate-Neglect, Noise, Anchoring, Availability, Preisanker) · **Final Data Trust Score** = geom. Mittel(Evidence·Source·Cube·Causal) × Bias-Dämpfer, gedeckelt durch harte Gates. (Geom. Mittel statt reinem Produkt, damit die Stufen-Skala nutzbar bleibt — schwächste Säule zieht trotzdem hart runter.)

**Aussage-Stufen** (≤30 ungenügend · 31–50 Hinweis · 51–70 vorsichtig · 71–85 belastbar · 86+ stark) begrenzen, was der Assistent verantwortungsvoll sagen darf. Die Empfehlung ist jetzt dem Final Data Trust **untergeordnet** (Master-Gate), nicht mehr eigenständig.

**Harte Gates (E):** n_preise<3 → Deckel 30 (keine starke Aussage); n_preise<5 → Deckel 50 (nur Hinweis); n_preise 5–9 → Deckel 85 (nie „stark"); Hauptquelle Modell → Deckel 55; hohe ADR + schwache Occ → Bias↑ (Preisanker-Check); RevPAR hoch + schwache Basis → „Signal, nicht Tatsache"; stark Top-10-abhängig → als operator-abhängig markiert.

**UI führt mit Trust:** Market Trust Table sortiert nach Final Data Trust (nicht Attraktivität) mit Stufe/Hauptquelle/n_preise/Cube-RevPAR/wichtigster Unsicherheit; Detailpanel zeigt Evidenz-Chips (vorhanden/fehlt), 6-Score-Zerlegung, aktive Gates, Cube-Ergebnis, dann erst die abgeleitete Empfehlung. Project Advancement Queue zu „Daten-Hebel (sekundär)" degradiert.

**Verifiziert:** 188/197 Märkte „ungenügend" (ehrlich — fast kein Markt hat ein Preis-Sample); nur Zug (n=7→85), Schwyz/Olten/Zofingen (n=20–38→75–76) erreichen „belastbar". 0 Gate-Verletzungen, 0 Console-Fehler. Rein additiv, Vanilla JS, defensive Null-Behandlung.

## [0.9.80] — 2026-06-08

### Neu — 🧠 Cube Governance Assistant (Steuerungs- & Prüf-Assistent)

Neuer Nav-Punkt **„🧠 Cube-Assistent"** + `view-cube`. Der Cube (`marketEconomics`/`strUnitEconomics`) wird zur **Chef-Instanz**: der Assistent rechnet nichts neu, sondern liest Cube-Outputs + Datenqualität und steuert daraus das ganze Projekt. Vier Blöcke: **(1) Cube Health** — Konsistenz-Check aller 197 Märkte gegen die Cube-Identität `RevPAR = ADR×Occ`, bekannte Schatten-Formeln, fehlende Badges. **(2) Project Advancement Queue** — priorisierte Aufgaben (High-Impact/Low-Effort, Data-Quality, Scraper-Refresh, Cube-Refactoring). **(3) Market Decision Table** — pro Markt Empfehlung (Priorisieren/Testen/Beobachten/Zurückstellen/Datenlage ungenügend) + Qualität/Datenvertrauen/Risiko. **(4) Detailansicht** je Markt — Cube-Werte, 5 Scores, Bias-Warnungen (Kahneman), Kausalitäts-Check (Pearl), nächster Schritt.

**Anti-Scheingenauigkeit als harte Regel:** `n_preise < 5` kann nie „Priorisieren" ergeben (auto-Downgrade auf „Testen"); schwache Datenlage dämpft den Chancen-Score multiplikativ. ADR wird nie isoliert positiv gewertet — RevPAR (Cube) ist der Haupttreiber, hohe ADR bei schwacher Auslastung erzeugt eine Bias-Warnung.

**Erster echter Befund:** Cube-Health 50/100 — bei 172 von 197 Märkten weicht das angezeigte `m.revpar` vom Cube-Wert ab (BFS-Märkte ohne ADR-Kalibrierung nutzen Modell-Occ statt der Cube-Occ aus `occOf`). Beispiel Genève: Dashboard zeigt RevPAR 100, der Cube rechnet 75 (−33%). → Top-Refactoring-Kandidat: `m.revpar` projektweit aus dem Cube ableiten.

Rein additiv, Vanilla JS, keine neue Dependency, keine externe/AI-API, defensive Null-Behandlung, keine Console-Fehler. Neue Funktionen: `getCubeInputs`, `getCubeOutputs`, `auditCubeConsumers`, `detectShadowCalculations`, `calculateCubeHealthScore`, `calculateMarketQualityScore`, `calculateDataConfidenceScore`, `calculateOpportunityScore`, `calculateRiskScore`, `calculateCubeConsistencyScore`, `detectBiasWarnings`, `inferCausalHypotheses`, `generateMarketRecommendation`, `generateProjectAdvancementQueue`, `renderCubeGovernanceAssistant`.

## [0.9.71] — 2026-06-08

### Neu — Nur ganze Einheiten (R2R) + actionable Perlen-Satz (WO + WAS)

**Feedback #1 — Rooms/Shared raus.** R2R mietet die GANZE Wohnung. Das Entire-vs-Room-Signal sitzt NICHT im abgeleiteten `room_type` (`"Rental unit in Zug"` steht für Entire UND Room — mehrdeutig), sondern im Rohtitel: BD `listing_name` Prefix `"Entire …"` vs `"Room/Private room/Shared room/Hotel room …"`, Free `it["title"]` analog. Neuer Helper `is_entire()` (dreiwertig: True/False/None) in beiden Fetchern, Flag `is_entire` ins Listing-Schema. **Nicht hart gefiltert** — Flag persistiert, Aggregate gespalten: `count` (alle = Markt-/Konkurrenz-Dichte) vs. `entire_count` + `avg_occupancy_entire_pct` (Earnings/Pearl). Anzeige filtert (`is_entire !== false`): Radar-Tabelle, Perlen-Radar, Konkurrenz-Röntgen, Verfügbarkeit UND die zentrale Engine (`marketRealStats` → `occOf` → marketEconomics) laufen jetzt auf Entire-Auslastung. Märkte ohne ganze Einheit (`entire_count=0`, z.B. Edlibach/Steinhausen) zeigen ehrlich `—`, kein Zimmer-Fallback. Bestandsdaten kostenlos gesäubert: BD-Märkte aus `data/raw/*` re-normalisiert, 7 Free-Märkte neu gescrapt (in Zug-Discover: 38 von 103 = 37% keine ganze Einheit).

**Feedback #3 — Actionability + #2 — Progressive Disclosure.** Perlen-Radar zeigt pro Markt EINEN Klartext-Satz statt 4-Komponenten-Block: „Kriens — hol dir eine 3–4-Pers-Wohnung (2–3-Zi) als ganze Einheit: im Sample nur 3, Ø 78% gebucht — knappes Angebot trifft hohe Belegung. Spread grob CHF 600–700/Mt → R2R geht auf." Die Lücke IST die Antwort (WO + WAS + WIE). Volle Score-Rechnung erst auf Klick (`<details>`). Ehrlich: „im Sample", explizite n, Spread als Range (±10% Modell-Unschärfe), „nur 1 Inserat — sehr dünne Basis" bei n=1.

## [0.9.70] — 2026-06-05

### Neu — `swissstr.cmd`: lokaler Ein-Klick-Start (Repo darf privat bleiben)

- GitHub Pages serviert private Repos im Gratis-Plan nicht (→ 404). Da die Akquise ohnehin den lokalen Agenten braucht, ist lokal-laufen der saubere Weg. `swissstr.cmd`: Doppelklick → serviert SwissSTR lokal (127.0.0.1:8766), startet den Akquise-Agenten im Hintergrund (ohne Extra-Tab) und öffnet den Browser. Kein Cloud, Repo bleibt privat.

## [0.9.69] — 2026-06-05

### Neu — Akquise-Ansicht (Rent-to-Rent, lokal an Heimstatt angegliedert)

- Neuer Nav-Punkt **„Akquise"** + `view-akquise`: passende Miet-Inserate finden → mit echten SwissSTR-Marktdaten scoren (Score · Spread · STR-Brutto · Payout) → **Anschreiben vorbereiten**. Pro Inserat ein Link „→ Marktanalyse" in die jeweilige SwissSTR-Markt-Ansicht (`openMarket`).
- **Lokale Anbindung:** SwissSTR ist statisch, die Akquise-Logik lebt im lokalen Heimstatt-Agenten (`127.0.0.1:8782`, via CORS). Ist der Agent nicht gestartet, zeigt die Ansicht einen Hinweis mit dem Startbefehl (`agent\cockpit.cmd`) + „erneut verbinden". Nichts verlässt den Laptop.
- **Kein Versand:** Entwürfe (Mock gratis / echter Claude per Schalter) landen nur in der Outbox zur Ansicht — bewusst kein Send.

## [0.9.67] — 2026-06-05

### Neu — Nacht-Preis → ADR & RevPAR (TODO #1 erledigt)

- **Nacht-Preis korrekt erfasst:** `normalize()` mappte bisher das 7-Nächte-Stay-Total als „price_usd". Jetzt echter Nacht-Preis (BD-Feld `price`, Fallback Total/7). Heutige Zeitreihe migriert (Total → Nacht).
- **ADR & RevPAR in CHF** in der Aggregation: ADR = Median der Nacht-Preise im Buchungsfenster (heute +42…+49 T, 7 Nächte) × USD/CHF **0.79** (🟡 dokumentiert, Stand 06/26, via env `SWISSSTR_USD_CHF` überschreibbar). RevPAR = ADR × Kalender-Auslastung. Trend-Deltas Δ ADR/Δ RevPAR ab 2. Punkt.
- **STR-Radar: neue „💰 ADR & RevPAR"-Card** (🟡 MOD) — Snapshot ab dem 1. Datenpunkt, sortiert nach RevPAR, mit „n Preise" (Inserate mit sichtbarem Preis) und voller Methodik-Fussnote. Δ-RevPAR-Spalte im Trend-Block.
- Erste echte Zahlen: Gstaad RevPAR CHF 177, Horw 152, Emmen 130, Baden 78. Meggen/Schönried ohne Preis (BD lieferte keinen) → ehrlich „—".

Verifiziert via Preview (Port 8766), keine Konsolenfehler. Kein neuer Scrape (REST-API/Token unberührt, keine BD-Kosten).

## [0.9.66] — 2026-06-05

### Neu — Verfügbarkeits-View + Buchungs-Dynamik (ready für morgen)

- **Verfügbarkeit pro Markt** im Röntgen: frei in 7/30 Tagen (X/N), kurzfristig ausgebucht, **frei nach Grösse** (z.B. Kriens 4Zi 0/1 = ausgebucht = Lücke/Chance). Serving-Felder next_free/free_7d/free_30d pro Inserat.
- **Buchungs-Dynamik** in der Aggregation: Tag-zu-Tag-Diff der Kalender (frei→belegt) → gebuchte Nächte, Lead-Time, „bestes Geschäft" pro Markt. Rechnet automatisch ab dem 2. Datenpunkt (morgen 06:00).
- **STR-Radar Trend-Block** zeigt ab morgen Δ Auslastung · gebuchte Nächte · Ø Vorlauf · Δ Supply.

Alles aufgesetzt: die tägliche 06:00-Automatik (scrape→aggregate→reviews) füllt es selbst. Verifiziert via Preview, keine Konsolenfehler.

## [0.9.65] — 2026-06-05

### Geändert — Geo-Zuordnung per Inserat-Standort (Airbnb-Karten-Zoom-Bleed neutralisiert)

Adrian: Airbnb-Suche zoomt die Karte automatisch raus → „Luzern"-Suche zeigt Emmen-Inserate
(teils Anti-Scraping). Fix: jedes Inserat wird seiner **echten Gemeinde** zugeordnet — aus der
**listing-eigenen `location`** (nicht such-/zoom-abhängig) + `lat/long` gespeichert. `write_market`
macht **Geo-Bucketing**: Inserate fallen in ihre wahre Gemeinde, Suchbegriff ist nur Fallback.
- Bewährt: Gstaad-Sample hatte 1 Inserat in **Schönried**, Aarau 1 in **Buchs** → jetzt korrekt dort.
  STR-Radar zeigt 9 statt 7 Gemeinden. `SUBLOCALITY`-Map snappt Quartiere (Emmenbrücke→Emmen …).
- Skaliert „möglichst viele Orte": breit scannen → automatische korrekte Bucketung.

Verifiziert via Preview, keine Konsolenfehler. (n<5 Gemeinden fliessen nicht in die Engine.)

### Neu (v0.9.64) — Kalender in die Zeitreihe (Buchungs-Erkennung-Fundament)
`normalize()` behält freie Zukunfts-Tage; `append_history` speichert `avail_dates` + `avail_count`
+ `is_superhost` pro Inserat/Tag. Ab 2 Datenpunkten: Tag-zu-Tag-Diff → gebuchte Tage, Lead-Time,
Preis-Änderung, „bestes Geschäft".

## [0.9.63] — 2026-06-05

### Neu — Review-ABSA: „was Gäste loben / bemängeln" pro Markt (Phase B)

Aspect-Based Sentiment (SOTA) über die echten Review-Texte, transparent ohne LLM:
- **`tools/fetch_airbnb.py --reviews`** → `data/airbnb-insights.json`. DE+EN-Aspekt-Lexikon
  (Lage · Sauberkeit · Preis/Wert · Host/Kommunikation · Ausstattung · Lärm · Check-in) +
  Sentiment-Cues. Pro Markt: loben/bemängeln (saubere Schwellen, kein Aspekt in beiden) + Beispiel-Zitate.
- 100–160 Reviews/Markt analysiert. Durchgängig **geschätzt: Lage · Host · Ausstattung · Sauberkeit**
  (deckt sich mit der Forschung); Kritik selten (Airbnb-Reviews positiv-lastig) — z.B. Aarau „Lärm".
- **Röntgen-Block „💬 Was Gäste sagen"** im Markt-Detail: Geschätzt/Kritik-Chips + **„🎯 Dein Edge:
  bei X mithalten, bei Y besser sein"** + echtes Zitat. Genau die „was loben/fehlt"-Intelligenz.

Ehrlich: Keyword-Heuristik (Richtung, nicht Präzision; 🟡), LLM-ABSA wäre der Accuracy-Upgrade.
Verifiziert via Preview (7 Märkte), keine Konsolenfehler.

## [0.9.62] — 2026-06-05

### Geändert — SOTA-Auslastung: Kalender-Belegung statt Review-Proxy (AirDNA „Booking Pace")

`available_dates` von Bright Data ausgewertet → **echte Kalender-Belegung** (Anteil der nächsten
90 Tage, die nicht verfügbar sind = gebucht ODER blockiert). Das ist der SOTA-Forward-Occupancy-
Proxy, deutlich belastbarer als Review-Velocity:
- **Baden 14% → 47%** (Review-Proxy war durch Hostel-Sample verzerrt), Kriens 76%, Emmen 73%,
  Horw 70%, Meggen 68%, Gstaad 58%, Aarau 47% — Agglo Luzern durchweg stark.
- `normalize()` nutzt Kalender-Belegung primär, Review-Proxy als Fallback (`occ_method` mitgespeichert,
  beide Werte transparent). Speist via `marketRealStats` die ganze Engine (Kriens-KPI jetzt 76%).
- Ehrlich gelabelt: „Kalender-Belegung, nächste 90 Tage, gebucht/blockiert → Obergrenze" (🟡).
- Captions in Röntgen + STR-Radar entsprechend umgestellt.

Caveat: blockiert ≠ gebucht (Obergrenze); Preis/ADR weiterhin TODO (kein Nacht-Preis ohne
verfügbare Anfrage-Tage). Verifiziert via Preview, keine Konsolenfehler.

## [0.9.61] — 2026-06-05

### Neu — `aggregate`-Stufe + Zeitreihen-Trends (SOTA-fundiert)

SOTA gecheckt (AirDNA/AirROI: ADR·Occ·RevPAR·Supply·Saison·Booking-Pace; Review-Mining: ABSA),
dann gebaut:
- **`tools/fetch_airbnb.py --aggregate`**: Zeitreihe (history JSONL) → `data/airbnb-trends.json`
  pro Markt: Serie {date, occ, supply, pro_share} + MoM-Δ (occ_delta_pp, supply_delta) ab 2 Punkten.
- **ADR/RevPAR bewusst NULL** (data-first): BD liefert ein Aufenthalts-Total, keinen Nacht-Preis,
  oft leer → kein falscher RevPAR. Als „● TODO" sichtbar; sauberer CHF-Nacht-Preis = Folge-Schritt.
- **STR-Radar Trend-Block** lädt die Trends: erfasste Punkte + Δ-Tabelle ab 2. Lauf.
- `run_focus_daily.ps1` ruft am Ende `--aggregate` → Trends täglich aktuell.

Verifiziert via Preview (7 Märkte, je 1 Punkt, Δ ab morgen), keine Konsolenfehler.
Nächste SOTA-Schritte: `availability` extrahieren (echte Zukunfts-Occ = Booking-Pace) · Review-ABSA.

## [0.9.59–0.9.60] — 2026-06-05

### Neu — Tages-Automatik scharf
`tools/run_focus_daily.ps1` (ASCII-safe) + versionierte Fokus-URL-Listen (`data/airbnb-urls/`).
Windows-Aufgabe „SwissSTR-Airbnb-Fokus" täglich 06:00 (StartWhenAvailable), echter Scheduler-Lauf
validiert, Tages-Guard gegen Dupes, Transcript-Log.

## [0.9.58] — 2026-06-05

### Neu — Phase B: „STR-Radar" als eigene Header-Seite (Cross-Markt-Konkurrenz)

Eigener Nav-Eintrag **STR-Radar** (neben Markt-Detail) — Cross-Markt-Übersicht aller Märkte mit
echten Airbnb-Röntgen-Daten: sortierbare Tabelle (echte Ø-Auslastung 🟡 mit n · Profi-Anteil ·
Sample-Grösse · Grössen-Mix · Stand), Klick öffnet das volle Röntgen im Markt-Detail. Zeigt
„X von 197 Märkten erfasst" + Trend-Platzhalter (erscheint mit wachsender Zeitreihe).
7 Märkte live, sortiert: Kriens 72% > Horw 57% > Emmen 45% > Meggen 44% > Aarau 33% > Gstaad 31% >
Baden 14%. Verifiziert via Preview, keine Konsolenfehler.

## [0.9.57] — 2026-06-05

### Geändert — Phase A: echte Airbnb-Auslastung speist die Engine (🔴 MOCK → 🟡 echt)

Die echten Röntgen-Daten gehen jetzt nicht nur ins Anzeige-Kästchen, sondern in die zentrale
Engine — damit werden ALLE Profit-Zahlen eines Marktes echt statt geschätzt:
- Neuer Resolver **`marketRealStats(m)`**: Priorität **echte Airbnb-Stichprobe (Ø, n≥5) 🟡 >
  BFS-Hotel-Proxy > Modell 🔴**. `occOf(m)` zieht daraus → Earn-Card, Konkurrenz-Tiers, KPI-Modal,
  Investor-Kalk, Edge-„verdient" laufen für die 7 Märkte auf echter Auslastung.
- Beispiel Kriens: KPI-Auslastung jetzt **72%** (echte Stichprobe) statt Modell. Zermatt unverändert
  (kein Airbnb-Sample → BFS-Fallback).
- **Ø statt Median** bewusst: der Review-Proxy pinnt bei vielbesuchten Inseraten am 95%-Cap, Median
  überschätzt → Ø (= die im Röntgen angezeigte Zahl) dämpft das und bleibt konsistent.
- Röntgen zeigt sichtbar „✅ diese Auslastung speist jetzt die Profit-Rechnung (🟡 n=X, indikativ)".

Ehrlich: 🟡 nicht 🟢 (Review-Proxy + kleine Stichprobe). Verifiziert via Preview, keine Konsolenfehler.

## [0.9.56] — 2026-06-05

### Neu — 7 Märkte live (Fokus-5 + Gstaad + Aarau) im Konkurrenz-Röntgen
Baden, Meggen, Kriens, Horw, Emmen, Gstaad via Bright-Data-Pipeline gezogen + in OneDrive-Zeitreihe.
Befunde: Kriens 71.5% Ø-Auslastung (heiss), Horw 57%, Emmen/Meggen ~45%, Gstaad 31% (Resort), Baden 14%.

## [0.9.55] — 2026-06-05

### Neu — Skalierbare Daten-Schichten + Zeitreihen-Fundament (3-Jahres-Strategie)

Fundament für proprietäre CH-STR-Intelligenz über Zeit (Adrian: „klare, hoch skalierbare Struktur").
- **Schichten getrennt:** ① Roh-Archiv + ② Zeitreihe liegen in **OneDrive** (`Claude Cowork/
  03_Projekte_Aktuell/SwissSTR_Daten/`, via `.env:SWISSSTR_DATA_DIR` überschreibbar) — gross/wachsend,
  ausserhalb Git. ③/④ Serving-Aggregate bleiben klein im Repo (`data/`). README im Archiv dokumentiert.
- **Zeitreihe** `history/airbnb/{markt}.jsonl` — append-only, **eine Zeile pro Inserat pro Tag**
  (price/reviews/reviews_per_month/occ_proxy/rating/bedrooms/pro_host), Identität via `property_id`,
  Tages-Guard gegen Duplikate. Aarau ist der erste Datenpunkt (9 Zeilen, 2026-06-05).
- **Fokus-Märkte** `tools/markets_focus.txt`: Baden · Meggen · Kriens · Horw · Emmen (Agglo Luzern +
  Baden) für die *tägliche* Preis-Sammlung; breiter Monats-Sweep über alle 187 separat.

**Kadenz-Plan:** täglich Fokus-5 (~Rappen/Tag → Preisdynamik), monatlich 187 (~$14/Mt → Trends/Supply).
Roadmap: `aggregate` (→ airbnb-trends.json) · Review-Text-Mining (→ insights) · Pricing-Co-Pilot.

## [0.9.54] — 2026-06-05

### Neu — Konkurrenz-Röntgen LIVE mit echten Aarau-Airbnb-Daten

Bright-Data-Pipeline scharf geschaltet und erste echten Daten gezogen. Aarau (9 Inserate):
- **Bestätigt Adrians These mit echten Zahlen:** ein Bed&Breakfast mit **162 Reviews = 13.95
  Reviews/Monat ≈ 95% Auslastungs-Proxy, Vollzeit-Profi** — daneben 2 starke Profis (65%/62%) und
  ein langer Schwanz mittelmäßiger Inserate. Die „Top-10% vs. Rest"-Realität, jetzt belegt.
- Ø-Auslastung 33.4% · 6 von 9 Vollzeit-Profis · Grössen-Mix 7× Rental unit, 1× B&B, 1× Treehouse.

**`tools/fetch_airbnb.py` produktiv gemacht** (echtes BD-Schema, Stand 2026-06):
- Async-Snapshot-Flow (trigger → `progress` pollen → `snapshot` laden) + `--snapshot <id>`-Modus
  zum Nach-Laden ohne neuen Scrape.
- Room-URLs werden mit Such-Parametern + `currency=USD` augmentiert (sonst `dead_page` bzw.
  „Unsupported currency: Fr"-Parse-Fehler).
- Korrektes Mapping: `property_number_of_reviews`, **Reviews/Monat aus `reviews_details`-Datumsangaben**
  (echtes Velocity-Signal), Host aus `host_details`, **Profi = Superhost ODER Host mit >1 Inserat im
  Markt**, Typ/Zimmer aus dem `name`-String geparst. Rohantwort wird vor dem Parsen gesichert.

`data/airbnb-competitors.json` enthält jetzt echte Aarau-Daten; Röntgen rendert sie live (verifiziert
via Preview, keine Konsolenfehler). **Token bleibt in `.env` (nie committet).**

## [0.9.53] — 2026-06-05

### Neu — Konkurrenz-Röntgen (Gerüst) + Bright-Data-Pipeline (secret-safe)

Vorbereitung für echte Airbnb-Konkurrenz-Daten (Adrian: „Aarau hat 2× 4-Zi, immer ausgebucht,
~13 Reviews/Mt = Profi"). Bright Data ist im Trial — Token wird NIE im Code/Repo gespeichert.

- **`tools/fetch_airbnb.py`** — zwei Modi: `--ingest <export>` trimmt einen heruntergeladenen
  BD-Export (kein Token nötig) → `data/airbnb-competitors.json`; `--fetch` ruft die BD-API
  (Token aus `.env` via `os.environ`, nie committet). Rechnet **Reviews/Monat → Auslastungs-Proxy**
  (÷55% Review-Quote × 3 Nächte) und erkennt **Vollzeit-Profis** (host_listings_count > 1).
- **`.gitignore`**: `.env`, `.env.*`, `data/raw/` ausgeschlossen. **`.env.example`** als Vorlage.
- **Konkurrenz-Röntgen im Markt-Detail** (in der Konkurrenz-Analyse): zeigt bei vorhandenen Daten
  aktive Inserate · Ø-Auslastung (Reviews/Mt) · Vollzeit-Profis · Grössen-Mix · Top-Inserate nach
  Auslastung (mit Profi-Badge, Preis, Reviews/Mt). Ohne Daten: ehrlicher „● geplant"-Hinweis statt Fake.

Verifiziert via Preview: Hinweis-Modus ohne Daten + Render mit Test-Daten (Zermatt: 3 Inserate,
71% Ø, 2 Profis, sortiert nach Auslastung), keine Konsolenfehler. Python-Skript kompiliert.
**Nächster Schritt (Adrian):** Token in Bright Data resetten, „Entdecken nach Standort Aarau"
laufen lassen (async), JSON → `data/raw/`, dann `--ingest`.

## [0.9.52] — 2026-06-04

### Geändert — Edge-Kandidaten: „was gesucht ist" + „was man verdient" pro Markt

Adrian: „hier möchte ich sehen was gesucht ist — Homeoffice/Studio/Familie — und was man verdient,
was bringen mir die Punkte." Jede Edge-Zeile zeigt jetzt:
- **🔎 Gesucht:** die passenden Zielgruppen/Personas (Business-Reisender, Familie, Paar-Wellness,
  Flugcrew) aus `computeOpportunities` — oder ehrlich „🌐 breite Nachfrage" wenn kein Spezial-Treiber.
- **💰 verdient:** konkrete CHF aus der **zentralen Engine** — Median-Operator ~CHF Xk · Top-10%
  ~CHF Yk Brutto/Jahr. Macht den abstrakten Score greifbar.
- Klarstellung am Score: **„Punkte = Signalstärke, nicht Verdienst"** — trennt Momentum-Signal von
  der Verdienst-Zahl.

Verifiziert via Preview (Olten: Familie · Median 19k/Top 25k; Rheinfelden: breite Nachfrage),
keine Konsolenfehler.

## [0.9.51] — 2026-06-04

### Geändert — Engine-Konsolidierung Runde 2: ALLE Brutto-/NOI-Zahlen aus einer Quelle

Adrian: „alles soll über die Engine laufen, etwas anderes macht keinen Sinn — es gibt noch andere
Abweichungen, korrigiere das." Erledigt — alle verbliebenen Rechen-Stellen außerhalb von
`marketEconomics` aufgespürt und umgehängt:
- **Investor-ROI-Rechner (Brutto):** lief auf eigener Formel (`adr × bedMult × 365 × occ × pctMult`)
  → jetzt Engine. Perzentil-Slider (P25–P90) wird auf die Engine-Tiers interpoliert (Bottom/Median/Top),
  Schlafzimmer → Wohnungstyp. Zermatt P50/3Z: Brutto **91'638 → 83'200** (= identisch zu Markt-Detail).
  Break-Even-Occupancy zieht ebenfalls aus der Engine.
- **Anomalie-Panel Ø Tag/Monat/Jahr:** war `RevPAR × Tage` → jetzt Engine-Median (Tag 228 / Monat
  6'933 / Jahr 83'200 für Zermatt, deckungsgleich mit KPI-Modal & Investor-Kalk).
- **Arbitrage-Spread-Detektor** (`RevPAR × 30`) → Engine-Brutto/Monat.
- **Recommender „grob NOI"**: hatte `RevPAR × 365 × Occ × 0.71` = **Auslastung doppelt gezählt** →
  jetzt Engine-NOI (Median).
- **Drill-Modal „Jahres-Potenzial 3.5Z"** → Engine-Brutto.

Folge: dieselbe Kennzahl zeigt jetzt überall im Tool exakt dieselbe Zahl. Verifiziert via Preview
(Zermatt 83'200 in Investor-Kalk = Anomalie = KPI-Modal), keine Konsolenfehler.

## [0.9.50] — 2026-06-04

### Behoben — Kauf-Rechner: Finanzierung nach CH-Standard (Amortisation + echtes Cash-on-Cash)

Adrian: „da stimmt doch nicht, auch der Zins wird anders gerechnet — nimm die beste Vorlage."
Der Kauf-Modus zog nur den **Hypothekarzins** ab, aber **nicht die Pflicht-Amortisation** und
rechnete CoC nur auf das Eigenkapital → Cash-on-Cash war zu schön (Zermatt-Beispiel 9.72%).

Jetzt CH-Standard-Finanzierung:
- **1. Hypothek ≤65% / 2. Hypothek 65–80%**, letztere zwingend **in 15 Jahren amortisiert**.
- **Freier Cashflow = NOI − Zins − Amortisation** (Amortisation als echter Liquiditätsabfluss,
  Hinweis „baut EK auf"). Eigene Wasserfall-Stufe „−Amort." + eigene Breakdown-Zeilen (1./2. Hyp).
- **Cash-on-Cash auf tatsächlich eingesetztes Kapital** (EK + Kaufnebenkosten + Möblierung),
  nicht nur EK.
- Sensitivitäts-Matrix, Break-Even-Occupancy und Verdict ziehen alle die Amortisation mit.

Resultat Zermatt (1.25M, 25% EK, 2.10%): CoC **9.72% → 5.70%**, freier Cashflow CHF 22'042
(statt geschönter ~30k), Amortisation CHF 8'333 sichtbar, Verdict ehrlich „Hold / Cautious Buy"
statt „Strong Buy". Rent-Modus unverändert. Verifiziert via Preview, keine Konsolenfehler.

## [0.9.49] — 2026-06-04

### Neu — „Kann ich mir das leisten?" (CH-Tragbarkeit + hartes Eigenkapital) im Kauf-Modus

Adrian: der Kauf-Rechner zeigte nur die Rendite (CoC/Cap), aber nicht die zwei Schweizer
Finanzierungs-Gates, die entscheiden, ob man überhaupt kaufen kann. Neu im Kaufen-Modus:
- **Brutto-Einkommen**-Input + Hinweis, dass die Bank **STR-/Airbnb-Einkommen nicht anrechnet** —
  der Lohn muss tragen.
- **PK-Anteil am Eigenkapital**-Slider.
- **Gate 1 Tragbarkeit** (FINMA-Standard): kalk. Kosten = 5% Kalk-Zins + 1% Unterhalt +
  Amortisation auf 65% LTV in 15 J., muss ≤ ⅓ des Brutto-Einkommens sein. Zeigt Quote vs. 33%.
- **Gate 2 Hartes Eigenkapital**: ≥10% des Kaufpreises müssen „hart" sein (Cash/Säule 3a),
  kein PK-Geld. Zeigt hartes EK vs. nötig.
- **Gesamt-Verdict** 🟢 Leistbar / 🟡 1 Gate offen / 🔴 nicht leistbar.

Verifiziert via Preview: 🟢 bei 250k Einkommen/0% PK (Quote 21.7%), 🔴 bei 90k + 80% PK
(Quote 66.7%, hartes EK 40k < 100k). Karte nur im Kauf-Modus, keine Konsolenfehler.

### Roadmap — Bright Data priorisiert (AirDNA raus)
AirDNA endgültig verworfen (Adrian: Kosten/Unabhängigkeit). Bright Data (Scraping, Gratis-Test
verfügbar) als priorisierter TODO notiert für „Konkurrenz-Röntgen" (echte Airbnb-Inserate →
Reviews/Monat als Auslastungs-Proxy + Vollzeit-Anbieter-Erkennung) und Auto-Inserat-Parsing im
Arbitrage-Modus (Weg A). Einsatz, sobald Nutzen klar hoch; braucht API-Key von Adrian.

## [0.9.48] — 2026-06-04

### Neu — Doing-Flow „Inserat-Check & Anschreiben" im Investor-Kalk (Arbitrage-Modus)

Erster Schritt Richtung R2R-„Doing"-Tool, eingebaut wo es hingehört: in den **Mieten/Arbitrage-
Modus** des Investor-Rechners (nicht auf die Scout-Beispielkarten). Weg B = manuelles Einfügen,
ohne Scraping/Account/Backend:
- **Inserat einfügen:** Inserat-Link + optionale Foto-URL. Zeigt das **echte Inserat-Foto** (kein
  Stockbild — bleibt ehrlich), „Inserat öffnen ↗"-Button.
- **Lohnt-Ampel** (🟢/🟡/⚪/🔴) aus der bestehenden Arbitrage-Rechnung (STR-Multiple, Break-Even,
  Cashflow) — sofort sichtbar pro konkretem Inserat.
- **R2R-Anschreiben-Generator:** erzeugt einen fertigen, auf Markt/Miete/Zimmer zugeschnittenen
  Vermieter-Text (Mietgarantie-Argument, professioneller Unterhalt, ausdrückliche Zustimmung nach
  Art. 262 OR, Referenzen/Betreibungsauszug) mit Platzhaltern [Telefon]/[Name] + Kopieren-Button.
  **Senden bleibt manuell.**

Grundsatz-Entscheid dokumentiert: Analyse (SwissSTR) und Doing (R2R) gehören perspektivisch
zusammen + teilen die `marketEconomics`-Engine; AirDNA bleibt raus (Adrian-Entscheid). Auto-Inserat-
Abruf via Bright Data ist Weg A (braucht API-Key/Account von Adrian) — später andockbar.

Verifiziert via Preview (Zermatt-Arbitrage): Ampel/Foto/Fakten/Anschreiben rendern, Panel nur im
Arbitrage-Modus sichtbar, keine Konsolenfehler.

## [0.9.47] — 2026-06-04

### Geändert — P2: KPI-/Saison-/Verteilungs-Block direkt unter den Scout gezogen

Adrian wollte den Charts-Block (KPI-Bar + Saisonalität + Revenue-Verteilung) direkt unter
„Wer übernachtet hier / Markt-Chancen-Scout" — vorher lag er erst nach den Warn-Panels
(Liveness/Anomalie/Konkurrenz/Standort-Signale). Neue Modal-Reihenfolge: Scout → KPI/Saison/
Verteilung → Warn-Panels → Konkurrenz-Analyse → Earn-Card. Grid sauber gesplittet (Charts in
eigenem Grid, Earn-Card behält ihres), keine Duplikat-IDs. Verifiziert via Preview: vertikale
Reihenfolge korrekt, alle Blöcke rendern, keine Konsolenfehler.

## [0.9.46] — 2026-06-04

### Geändert — P2: Edge-Perlen & Such-Strategien konkret begründet

**Edge-Ranking „Perlen" (Adrian: „schwach begründet für den Platz"):** Top-5 bekommen jetzt
ein „Perle"-Badge + eine konkrete, daten-fundierte Warum-Zeile aus den echten Treibern statt
nur Zahlen-Tags — z.B. „Logiernächte +31% YoY (stärkstes Momentum) · Leerstand 1.67% →
Mietverhandlung in deiner Hand (Hotel-Occ 50.9% · RevPAR 77 · Grade D)". Downsides werden
ehrlich genannt (z.B. „angespannter Wohnungsmarkt — Objekt zu kriegen ist die eigentliche Hürde").

**Such-Strategien-Argumente (Adrian: „deine Argumente schwach"):** Floskel-Tags durch konkrete,
benannte Anker ersetzt — Business nennt den größten Arbeitgeber mit MA-Zahl („Anker UBS
(22'000 MA) → planbare Mo–Do-Belegung"), Familien-Gap zeigt Nachfrage- vs. Angebots-Index,
Couple/Sport nennen RevPAR + Hochsaison, Mid-Term den Anker, „solider Markt" → „kein 90-Tage-Cap".

Verifiziert via Preview: Edge-Perlen mit Begründung, Recommendations mit benannten Arbeitgebern,
keine Konsolenfehler.

## [0.9.45] — 2026-06-04

### Geändert — P4: Google-Quick-Search klar gekennzeichnet

Konkurrenz-Recherche-Buttons tragen jetzt einen sichtbaren „Google ↗"-Tag pro Button
plus Tooltip („Öffnet die Google-Suche in einem neuen Tab — keine Daten aus diesem Tool,
du recherchierst selbst"). Vorher nur eine leicht überlesbare Intro-Zeile. Macht transparent,
dass diese Buttons nicht tool-interne Daten zeigen, sondern eine externe Google-Suche öffnen.

## [0.9.44] — 2026-06-04

### Behoben — P3: Saison-Modal-Filter „teilweise nicht klickbar"

**Problem (Adrian):** Im Modal „RevPAR — Saisonalität, Verteilung & Bewertung" ließen sich
Monate teilweise nicht anklicken. Ursache: Der Balken-Klick nutzte Chart.js mit `intersect:true`
— nur die tatsächliche Balkenfläche war Klick-Target. Bei Nebensaison-Monaten (kurze Balken)
trifft man oberhalb des Balkens ins Leere → kein Filter.

**Fix:** `interaction: { mode: 'index', intersect: false }` + `getElementsAtEventForMode('index')`
im `onClick`/`onHover`. Jetzt ist die GANZE Monats-Spalte klickbar, unabhängig von der Balkenhöhe.
Verifiziert via Preview: Klick oberhalb eines kurzen Balkens (Juli/Zermatt) traf vorher `[]`
(nicht klickbar), jetzt `[6]` (Juli). Keine Konsolenfehler.

## [0.9.43] — 2026-06-04

### Geändert — ⭐ P1: Zentrale Rechen-Engine (löst widersprüchliche Zahlen an der Wurzel)

**Problem (Adrian):** Dieselbe Kennzahl wurde an 5+ Stellen verschieden gerechnet → Widersprüche.
Konkret Zermatt: Konkurrenz-Analyse Top-10% = 196'799 vs. Revenue-Verteilung (KPI-Modal) = 169k;
Median 47'794 vs. 67k. Ursache: zwei verschiedene Formeln auf `revpar×365` (×0.65→×3.5/×0.85/×0.4
vs. ×0.78→×2.5/×1.0/×0.45) — beide reine Heuristik, beide inkonsistent.

**Lösung — eine Quelle, ein Annahmen-Satz:**
- Neue `marketEconomics(m, größe)` + `strUnitEconomics(...)` als zentrale Engine. Operator-Tiers
  (`OPERATOR_TIERS`: Bottom-30% / Median / Top-10%) modellieren ehrlich die Spreizung *gleiche
  Wohnung, anderer Betreiber* (ADR-Pricing-Power × Auslastung), nicht eine erfundene Pareto-Decke.
- Kostenmodell = das der Earn-Card (Plattform 14% · Mgmt 5% · Reinigung nach Ø-Aufenthalt ·
  Kurtaxe als Pass-Through). Brutto/NOI/Tag/Monat/Jahr aus einer Hand.
- Alle Views ziehen jetzt aus der Engine: Earn-Card-Szenarien, Konkurrenz-Analyse
  (`computeMarketCompetition`), Revenue-Verteilung (KPI-Modal), Scout-Karten (`genProperty`),
  `annualGrossYield`, „Markt im Fokus", „Bester Cashflow-Markt" (Gesamt-KPIs).
- Folge: Konkurrenz-Analyse = Revenue-Verteilung = Earn-Card, identische Zahlen. Beispiel Zermatt:
  Top-10% 108k · Median 83k · Bottom-30% 60k — überall gleich. Proof zeigt ADR × Nächte (Occ%)
  pro Tier statt Blackbox-Multiplikator; Auslastung 🟢 BFS-verankert wo vorhanden.

**Mitbehoben:**
- Eigenkapital-vs-Preis-Bug in Scout-Karten: Text sagte „CHF 868k Eigenkapital", meinte aber den
  Kaufpreis. Jetzt „CHF 217k Eigenkapital (25% von 868k Kaufpreis)".
- Doppelte Occ-Diskontierung entfernt (`revpar×365×0.78` bzw. `revpar×365×(occ/100)` — RevPAR
  enthält Auslastung bereits). „Markt im Fokus" jetzt ehrlich als „Netto-Cashflow vor Finanzierung".

Verifiziert via Preview (Zermatt/Winterthur/Zug): Konkurrenz-Analyse und KPI-Modal zeigen
identische Tier-Werte, Earn-Card-Brutto deckungsgleich, Scout-Grid + Featured ohne Konsolenfehler.

## [0.9.38] — 2026-06-04

### Geändert — Markt-Detail aufgeräumt + Ranking erweitert (mehrere User-Befunde)

**Liveness-Warner kontext-sensitiv** (Adrian: „Vorsicht empirisch soll angezeigt werden wenn
dies der Fall ist. Zermatt gehört nicht dazu. Gesetz nicht an den Anfang. Vorgehen ist gut,
etwas verständlicher ohne auszuschweifen."):
- „Empirische STR-Daten fehlen / zu optimistisch"-Block + Sanity-Check erscheinen NUR noch bei
  echter Proxy-Schwäche (Business-/Pendler-Märkte) — bei Touristen-Resorts wie Zermatt nicht
  (HESTA ist dort ein guter Proxy). Signale nach Kategorie getaggt (proxy/reg/supply).
- Recht (ZWG/Stop) wird ans ENDE der Signal-Liste sortiert, nicht an den Anfang.
- Sanity-Check von 5 auf 3 Schritte gekürzt, klarere Sprache.

**Anomalie-Detektor: Ø-Umsatz pro Tag/Monat/Jahr** (Adrian: „übersichtlich … durchschnittliches
Einkommen pro Tag/Monat/Jahr"): 3-Kacheln-Zeile mit Brutto-Umsatz (RevPAR × Tage), ehrlich als
„vor Kosten, nicht Gewinn" + 🔴 MOCK markiert, Verweis auf Netto in der Earn-Card.

**Markt-Chancen-Scout nach oben** (Adrian: „absolut top, gehört rauf, etwas vom ersten das man
sehen soll"): Scout jetzt direkt nach dem Gäste-Mix, vor den Warn-Panels.

**Ranking-Tabelle: Leerstand-Spalte** (Adrian: „hier möchte ich auch noch die Leerstände") —
neue Spalte „Leerstand / leere Whg. % · BFS", hoher Leerstand grün hervorgehoben. Plus
„(24)" → „(24 Märkte)" — die Zahl ist die Anzahl Märkte im aktuellen Filter, jetzt beschriftet.

Verifiziert via Preview: Zermatt ohne Proxy-Block (Titel „Zu beachten"), Winterthur mit Proxy-Block;
Anomalie zeigt Tag/Monat/Jahr; Ranking mit Leerstand-Spalte; Scout vor Warnungen; keine Konsolenfehler.

## [0.9.37] — 2026-06-04

### Geändert — Wohnort frei eingebbar + Performance-Filter erklärt

Adrian: "hier sollte ich doch mein Einzugsgebiet eingeben können, also dass ich vom Dorf X
komme ... und für was steht hier Mittel Hoch und Tief."

- **Wohnort als Tippfeld mit Autocomplete** statt fixem 25-Städte-Dropdown: tippe deinen
  echten Wohnort (z.B. Baar). Liste = alle Märkte + CH-Gemeinden aus `communes.json`.
  Koordinaten werden zur Laufzeit aufgelöst + in MARKET_COORDS injiziert → Fahrzeit rechnet
  von DEINEM Ort. ✓/✗-Hinweis ob erkannt. Re-rendert Karte, Ranking, „Markt im Fokus".
- **Hoch/Mittel/Tief erklärt:** statt „Tertile des gewählten Metrics" jetzt Klartext —
  Hoch = bestes Drittel, Mittel = mittleres, Tief = unterstes Drittel der gewählten Kennzahl.

### Behoben
- TDZ-Bug: `let COMMUNES` war nach dem Wohnort-IIFE deklariert → `typeof COMMUNES` warf
  ReferenceError und brach den Rest des Scripts ab (Featured-Card hing auf „Lade Daten").
  COMMUNES früh deklariert.

### Hinweis
- Autocomplete deckt aktuell Märkte + 93 Schlüssel-Gemeinden (Bootstrap, inkl. Baar &
  Greenlist). Volle ~2'100-Gemeinden-Abdeckung sobald `fetch_communes.py` durchläuft
  (Wikidata war beim Bau rate-limitet; Monats-Action holt es nach).

## [0.9.36] — 2026-06-04

### Hinzugefügt — „Markt im Fokus" zurück, aber echt + für den User optimiert

Adrian: "es muss nicht raus, aber die Frage ist ob es besser geht, optimiert einfach für den User."

Statt der gelöschten fake-statischen Andermatt-Karte jetzt eine **dynamische, umsetzbare**
Empfehlung:
- Pickt den besten Markt nach geschätztem Cashflow (RevPAR × Auslastung), aber **nur
  regulatorisch saubere** (kein REGULATORY_STOP, kein ZWG-Cap) — kein Supply-Lock-Resort mehr.
- **Personalisiert:** wenn Einzugsgebiet gesetzt → nur erreichbare Märkte, Label „erreichbar ab X".
- Transparente Begründung („Warum: regulatorisch sauber · erreichbar in Xh · Verhandlungs-Hebel").
- Klartext-Labels (RevPAR = Umsatz/verfügb. Nacht, Auslastung = belegte Nächte %), Cashflow als
  🟡 MOD getiert, Auslastung 🟢 BFS. Re-rendert bei Einzugsgebiet-Änderung.
- Unterscheidet sich bewusst vom Hero „Bester Cashflow-Markt" (national, inkl. Resorts):
  diese Karte zeigt den, den man **wirklich umsetzen** kann.

Verifiziert via Preview: pickt Interlaken (A, CHF 54k, sauber) statt Andermatt; Scope wechselt
auf „erreichbar ab Baar" bei gesetztem Einzugsgebiet; keine Konsolenfehler.

## [0.9.35] — 2026-06-04

### Entfernt/Korrigiert — Fake-dynamische Dashboard-Karten + A/B/C/D-Klarheit

Adrian: "wann soll er sich zurücksetzen, es benötigt eine Logik ... Wo Sommer schlägt
Winter zu statisch und Diese Woche im Fokus das selbe und es ist nicht einmal ein guter
Tipp, wenn nicht besser möglich streichen ... was A,B,C,D ist auch nicht klar."

- **„TOP-CASHFLOW HEUTE" → „Bester Cashflow-Markt":** „HEUTE" war irreführend (ändert sich
  nicht täglich). Jetzt mit klarer Logik: höchster geschätzter Jahres-Cashflow aller Märkte,
  aktualisiert mit dem BFS-Daten-Refresh (monatlich). Wert war schon berechnet (Gstaad CHF 61k).
- **„Diese Woche im Fokus" (Andermatt) GESTRICHEN:** komplett hartcodiert, behauptete
  „Wöchentlich", empfahl ausgerechnet einen Supply-Lock-Resort (steht nebendran als Cap-Risiko).
  Redundant zum echten Edge-Ranking → entfernt, Karten-Grid auf 2 Spalten.
- **Saisonalitäts-Chart ehrlich gekennzeichnet:** war scheingenaue CHF-Kurven → jetzt klar als
  „Muster, kein Live-Wert" (typischer Saison-Verlauf der Profil-Typen); echte BFS-Werte im Markt-Detail.
- **A/B/C/D-Grade erklärt:** Legende direkt in der Filter-Leiste — was die Note heisst
  (A Top-Performance … D schwach, aus RevPAR + Nachfrage) UND warum man differenziert
  (A = teuer & reguliert, C/D = günstiger Einstieg, mehr Risiko).

Verifiziert via Preview: alle vier umgesetzt, Top-Cashflow dynamisch befüllt, keine Konsolenfehler.

## [0.9.34] — 2026-06-04

### Geändert — Edge-Score transparent (kein Blackbox-Wert mehr, §12)

Adrian: "was soll das 24 bedeuten ganz rechts? Das muss klar sein, ergibt sich aus Punkt a, b, c."

Die nackte Zahl war eine Blackbox. Jetzt zeigt jede Zeile die **Zusammensetzung**:
- Pro Markt unter dem Score: `Nachfrage +20 · Hebel +4 · Optimismus −X` → die Summe = der Score.
- Mini-Kopfzeile beschriftet die rechte Spalte: „Edge-Score = Nachfrage + Hebel − Optimismus".
- Fussnote ausgeschrieben: Nachfrage (BFS-Logiernächte-Wachstum YoY, ±20), Hebel
  (Leerstand ≥1.5% = +4 / ≤0.5% = −3), Optimismus (Abzug bei zu hoher modellierter Auslastung).
  Beispiel „24 = Nachfrage +20 + Hebel +4" direkt dabei.

Verifiziert: Rheinfelden zeigt 24 mit „Nachfrage +20 Hebel +4", keine Konsolenfehler.

## [0.9.33] — 2026-06-04

### Behoben — Investor-Calc P&L-Wasserfall verschwand

Adrian: "Der Wasserfall verschwindet komplett." Ursache: Chart.js mit
`maintainAspectRatio:false` ohne fixe Parent-Höhe → Canvas wuchs auf ~1680 px und
zerschoss das Layout (timing-abhängig). Fix: Canvas in Container mit fixer Höhe (260 px).
Verifiziert: Canvas stabil 260 px nach Navigation + Slider-Update, keine Konsolenfehler.

### Geändert — Ranking-Tabelle: alle Märkte, mehr Sortierungen, Klartext-Labels

Adrian: "jede Schweizer Stadt soll dabei sein ... filtern nach RevPAR, ADR und OCC ...
Abkürzungen dürfen da sein aber man soll direkt sehen von was man redet."

- **Alle 197 Märkte** statt Top-10 (scrollbarer Container 560 px, sticky Header).
- **Sortier-Toggle erweitert:** RevPAR · ADR · Auslastung · Notfall-Score (vorher nur RevPAR + Notfall).
- **Klartext unter jeder Spalte:** RevPAR → „Umsatz/verfügb. Nacht", ADR → „Ø Preis/Nacht",
  Auslastung → „belegte Nächte %", Note → „A–F gesamt". Titel zeigt Metrik ausgeschrieben + Anzahl.

## [0.9.32] — 2026-06-04

### Korrigiert — Reinigungskosten: Aufenthaltsdauer treibt Anzahl Wechsel

Adrian: "bei der Reinigung der Berechnung die stimmt definitiv nicht ... wenn man jeden
3 Tg jemand neues hat macht das x ... sie ist zu tief."

Der Fehler: fixer „4-Nächte-Schnitt" → zu wenige Reinigungen. Bei Ø 3 Nächten sind es
~85/Jahr (statt ~64), bei Ø 2 → ~128. Plus: das Modell tat so, als decke die Gast-Putzgebühr
die Kosten immer 1:1 (Netto null) — versteckt den realen Drag bei vielen Wechseln.

- **Neuer Slider „Ø Aufenthaltsdauer (Nächte)"** in der Custom-Earn-Card → treibt
  `Reinigungen = belegte Nächte ÷ Ø-Aufenthalt`. Default 3 (STR-realistisch statt 4).
- **Reinigungen/Jahr sichtbar** + **Putz-Netto** (kassierte Gebühr − echte Putzkosten);
  zeigt rot „du zahlst drauf", sobald die echte Putzkraft mehr kostet als der Gast zahlt.
- Putzkraft-Slider max 200 → **250** (CH-Reinigung inkl. Wäsche realistisch höher).
- Die 3 fixen Szenarien ebenfalls von 4 → 3 Nächte (waren zu optimistisch).
- Fließt automatisch in Cashflow, CoC und Break-even.

### Verifiziert
Preview: Slider treibt Count (Ø2→128, Ø3→85, Ø7→37); bei Putzkraft 180 > Gast-Gebühr 110
fällt Cashflow Zermatt von 34'163 auf 24'541 (Putz-Netto −8'960). Keine Konsolenfehler.

## [0.9.31] — 2026-06-04

### Hinzugefügt — Edge-Ranking + Backtest-Kalibrierung + Leerstand-Pipeline

Drei zusammenhängende Bausteine: Cross-Markt-Sicht des Anomalie-Detektors, ein echter
Phase-5-Backtest und die dritte Daten-Pipeline (Leerstand, doch via SDMX gelöst).

- **`tools/fetch_leerstand.py`** (SDMX gelöst): BFS-Leerwohnungsziffer pro Gemeinde via
  `disseminate.stats.swiss/rest` (Dataflow CH1.LWZ:DF_LWZ_1), gefilterte Slice statt 767-MB-
  Volldump (~530 KB, ~2 s). `data/leerstand.json` (2025): 2'292 Gemeinden. Stdlib-CSV, keine Deps.
- **Frontend:** `loadHesta` hängt `m.leerstand` (%) via BFS-Nummer an. Neuer Anomalie-Befund
  **Mietverhandlungs-Hebel** (Proxy §9): Leerstand ≥1.5 % = Spielraum (Chance), ≤0.5 % =
  angespannt (Risiko) — beide mit Gegen-Check.
- **Cross-Markt Edge-Ranking** (Scout-View): scannt alle BFS-Märkte, sortiert nach transparentem
  Edge-Score (reales Momentum + Hebel − Optimismus-Gap), regulatorisch gekappte ausgeschlossen,
  klickbar → Markt-Detail. Das „Aha" über alle Märkte auf einen Blick.
- **Backtest / Signal-Kalibrierung (Phase 5):** testet das Momentum-Signal retrospektiv
  (Vorjahres-YoY → realisiert Q1-2026 vs Q1-2025, rein reale BFS-Daten). **Ergebnis ehrlich:
  51 % Trefferquote (n=140) → das Signal ist kaum besser als Zufall, und die UI sagt das auch.**
  Macht die unmessbare Signal-Güte erstmals messbar (Kern von Phase 5).
- **`refresh-data.yml`**: `fetch_leerstand.py` im monatlichen Refresh (fallback-sicher).

### Hinweis

- Verifiziert via Pipeline-Run + Preview: Leerstand 2'292 Gemeinden (Zermatt 0.59 %,
  Solothurn 1.24 %, Zürich 0.10 %), Ranking 12 Märkte klickbar, Kalibrierung 51 % gerendert,
  keine Konsolenfehler.
- Die ehrliche 51 %-Kalibrierung bestätigt: Momentum ist ein schwaches Signal — der Edge-Score
  bleibt qualitativ zu lesen, kein Franken-Versprechen. Kein Confidence-Inflation.

## [0.9.30] — 2026-06-04

### Hinzugefügt — Phase 2: Anomalie-Detektor (Modell vs. Realität, MVP)

Der erste „Insight-Engine"-Baustein, der reale BFS-Signale gegen das modellierte STR-Modell
stellt. **Diagnostisch (Ist-Zustand), keine Prognose** — Edge-Kandidaten, keine Wahrheiten.

- **`detectAnomalies(m)`** prüft pro Markt vier Divergenzen, jede mit Tier + Konfidenz +
  adversarialem Gegen-Check:
  1. **Optimismus-Gap** — modellierte STR-Occ vs. reale BFS-Hotel-Occ (≥15 pp = Warnung).
  2. **Nachfrage-Momentum** — reale HESTA-Logiernächte YoY 2024→2025 (🟢 BFS, ±5 %).
  3. **Arbitrage-Spanne** — modelliertes STR-Brutto vs. Kanton-Kaltmiete (🔴 MOCK, LOW Konf.).
  4. **Regulierungs-Gate** — ZWG-Cap / REGULATORY_STOPS kappt jede Chance.
- **Verdikt §16-konform:** Grün NUR bei realem Nachfrage-Rückenwind ohne Regulierungs-Cap;
  hohe Chance + tiefe Konfidenz wird nie grün. Panel im Markt-Detail unter dem Liveness-Warner.
- Methoden-Fussnote macht den Daten-Mix (MOCK vs. BFS) transparent.

### Verifiziert
- Über alle Markttypen: Zermatt/Davos ⚖️ (Arbitrage + reg-limitiert), Winterthur 🟡
  (Optimismus-Gap), Basel/Neuchâtel/Fribourg/Chur 🟢 (Nachfrage-Rückenwind). 28 grüne
  Verdikte, 85 Momentum-Befunde, keine Konsolenfehler.

### Verschoben — BFS-Leerstand-Pipeline (bewusst NICHT gebaut)

Die BFS-Leerwohnungsdaten (Gemeinde-Ebene) sind auf die neue SDMX-Plattform stats.swiss
(`DF_LWZ_1`) migriert; der Daten-Endpoint liess sich nicht zuverlässig auflösen. Eine geratene/
fragile Pipeline würde gegen die Pipeline-Regel (reproduzierbar, keine ungeprüften Deps)
verstossen — daher transparent verschoben statt halbfertig geliefert.

## [0.9.29] — 2026-06-04

### Hinzugefügt — BFS-Mietpreis-Pipeline: Kaltmiete-Reality-Anchor am Miet-Input

Zweite A/B-Pipeline. Macht die Miet-Seite der Arbitrage-Rechnung datenfest und füllt die
Reality-Check-Lücke (§14): ADR & Auslastung hatten Markt-Benchmarks, der Mietzins bisher nicht.

- **`tools/fetch_mietpreise.py`**: holt „Durchschnittlicher Mietpreis nach Zimmerzahl und
  Kanton" (BFS-Asset je-d-09.03.03.01) via dam-api.bfs.admin.ch, parst die XLSX (neuestes
  Jahr-Sheet), schreibt `data/mietpreise.json`. Stdlib + openpyxl, fallback-sicher, Sanity-Checks.
- **`data/mietpreise.json`** (Jahr 2024): 26 Kantone × Zimmerzahl 1–5, Netto-Kaltmiete CHF/Mt.
- **Frontend:** `loadHesta` lädt die Mietpreise; `computeRentBenchmark` interpoliert pro
  Wohnungsgröße (z.B. 3.5Z = Ø rooms 3+4); unter dem Miet-Input erscheint der **BFS-Kaltmiete-
  Anchor** (🟡 MOD) mit Abweichungs-Ampel (>30 % gelb, >50 % rot, §14).
- **Ehrlich gekennzeichnet:** Es ist ein KANTONS-Durchschnitt — Resort-/City-Mikrolagen
  weichen stark ab (z.B. Zermatt 2'200 = +62 % ggü. VS-Schnitt 1'360). Der Inline-Hinweis
  „Kantons-Ø — Resort/City weicht ab" steht direkt dabei; ersetzt NICHT die Default-Miete.
- **`refresh-data.yml`**: `fetch_mietpreise.py` im monatlichen Refresh (fallback-sicher).

### Hinweis

- `computeDefaultRent` (revpar-basiert) bewusst unverändert — der Benchmark ist additiv,
  damit der Resort-Premium im Default erhalten bleibt.
- Verifiziert via Pipeline-Run + Preview: 26 Kantone, Benchmark rendert, Ampel korrekt
  (Zermatt +62 % rot, Winterthur +1 % grün, Bern ohne Miete = nur Info), keine Konsolenfehler.

## [0.9.28] — 2026-06-04

### Hinzugefügt — Roadmap B: ARE-Zweitwohnungen-Pipeline (ZWG-Cap-Layer)

Erste neue Daten-Pipeline seit den Bootstrap-Quellen — bringt regulatorische Realität
(Zweitwohnungsgesetz) als echtes Signal pro Markt ins Tool.

- **`tools/fetch_zweitwohnungen.py`**: holt das ARE-Wohnungsinventar (Layer
  `ch.are.wohnungsinventar-zweitwohnungsanteil`) via geo.admin.ch STAC-API, parst die
  offizielle XLSX-Tabelle, schreibt `data/zweitwohnungen.json`. Stdlib + openpyxl,
  fallback-sicher, Sanity-Checks, `_health.json`-Update.
- **`data/zweitwohnungen.json`** (Release 2026-03): 2'110 Gemeinden, **331 mit
  Zweitwohnungsanteil ≥20%**, **326 offiziell restricted** (ARE-Status). Beide Zahlen
  bewusst dokumentiert — die Abweichung (Sonderverfahren) wird NICHT geglättet.
- **Frontend:** `loadHesta` hängt `m.zwg` (pct, restricted) via BFS-Gemeindenummer an;
  `assessSTRLiveness` zeigt bei restricted-Gemeinden ein **ZWG-Cap-Signal** (🟡 medium):
  präzise als Proxy für regulatorische Sensibilität — kein direktes Verbot für
  Rent-to-Rent von Bestandswohnungen, aber Sensibilitäts- + Zusatzregel-Indikator.
- **`refresh-data.yml`**: `pip install openpyxl` + `fetch_zweitwohnungen.py` in den
  monatlichen Refresh aufgenommen (fallback-sicher mit `|| echo`).

### Hinweis

- Verifiziert via Pipeline-Run + Preview: 2'110 Gemeinden gefetcht, BFS-Mapping korrekt
  (Zermatt 51.86%, Davos 58.94%, St. Moritz 53.36%, Verbier→Val de Bagnes 54.12% restricted;
  Zürich 9.04% nicht), Signal rendert in Liveness-Warner, keine Konsolenfehler.
- Quelle 3-0 verifiziert (Deep-Research v0.9.25): „ARE Wohnungsinventar auf opendata.swiss,
  jährlich" + „331 Gemeinden >20% per 31.03.2026".

## [0.9.27] — 2026-06-04

### Hinzugefügt — Rechts-Layer: Untermiete-Caveat + Tessin-Präzisierung

Recht ist der Filter VOR der Ökonomie — der fundamentale Go/No-Go für Rent-to-Rent, der bisher
komplett fehlte. Verifiziert via Deep-Research (80 Claims bestätigt / 15 widerlegt).

- **Untermiete-Rechts-Caveat** in der Earn-Card (nur bei Miete > 0, 🟡 MOD): 3 Punkte —
  (1) Zustimmungspflicht Art. 262 OR, (2) Aufschlag begrenzt (BGE 119 II 353, kein Fixdeckel,
  Möblierungs-/Service-Zuschlag legitim), (3) Untermiet-Reform 24.11.2024 abgelehnt → altes Recht gilt.
  Quellen: SVIT Kommentar 2024, Jud/Steiger Jusletter 2017. Klar als „keine Rechtsberatung" markiert.
- **`REGULATORY_STOPS` Tessin präzisiert:** gewerblicher Vermieter ab < 4 Betten (verifizierte
  Korrektur — NICHT 6), max. 90 Tage/Jahr, Registrierungspflicht seit 1.2.2022.
- Neuer Glossar-Term `untermiete` (Art. 262 OR) mit Formel + BGE-Beispiel + Caveat.

### Hinweis

- Verifiziert via Preview: Caveat rendert (Zermatt), Glossar-Link aktiv, kein NaN, keine
  Konsolenfehler, Gold-Box-Styling korrekt (rgba statt Tailwind-Opacity inline).
- Kein Eingriff in Berechnungslogik — reiner Rechts-/Anzeige-Layer.

## [0.9.26] — 2026-06-04

### Hinzugefügt — Insight-Engine Phase 0: Cash-on-Cash + Break-even-Auslastung

- **Custom-Earn-Card** zeigt zwei neue Kennzahlen (🟡 MOD):
  - **Cash-on-Cash**: Jahres-Cashflow ÷ eingesetztes Kapital. Bei Rent-to-Rent = Mietkaution
    (3 Monatsmieten, Art. 257e OR) + Setup-Möblierung (größenskaliert, geschätzt). Inkl. Payback-Jahre.
  - **Break-even-Auslastung**: Occ, ab der Cashflow = 0 — linear aus dem bestehenden Modell
    abgeleitet (Deckungsbeitrag/Nacht). Ampel grün/gelb/rot ggü. erwarteter Auslastung, „nie" wenn >100 %.
- Kapital-Herleitung transparent unter den Kennzahlen, Tier-markiert.
- Neuer Glossar-Term `breakeven`; `coc`-Caveat um R2R-Kontext ergänzt.

### Dokumentation

- `docs/insight-engine.md` — 5-Phasen-Architektur (Anwender → Mustererkennung → Anomalie →
  Hypothese → Härtung → Lernschleife), Trennung diagnostisch/Kalibrierung/Prognose, Daten-Reihenfolge,
  Tool-als-Gedächtnis-Konzept, verifizierte Rechts-Befunde.
- `docs/fachliteratur.md` — verifizierte Quellenliste (Deep-Research, 80 Claims bestätigt / 15 widerlegt)
  inkl. der 4 Rechts-Korrekturen (Untermiet-Reform gescheitert, kein 30–40 % Gewinndeckel,
  Tessin < 4 Betten, FPRE monatlich).

### Hinweis

- Verifiziert: index.html lädt, keine Konsolenfehler, neue Kennzahlen Tier-markiert.
- Kein Eingriff in bestehende Berechnungslogik — CoC/Break-even leiten sich aus vorhandenen
  Werten ab; einzige neue Annahme ist das eingesetzte Kapital (dokumentiert + getiert).

## [0.9.25] — 2026-05-25

### Hinzugefügt — Deep-Research-Befunde integriert (verifizierte Quellen)
Recherche-Output: 110 Sub-Agents, 27 Quellen, 25 Behauptungen geprüft, 18 bestätigt, 7 widerlegt.

**Neue EMPLOYERS (Forschungs-/Bildungs-Cluster):**
- **Villigen**: PSI Paul Scherrer Institut · 2'200 MA + ~2'500 externe Gastforscher/Jahr · nur 53+11+4 Betten on-site (psi.ch/en/guesthouse) → strukturelle Übernachtungs-Lücke
- **Dübendorf**: Empa (1'000 MA), Eawag (500 MA), Innovationspark Zürich (1'500 MA) · 40 Apartments/116 Räume an Seidenstrasse 14/18/24 unter ETH-Priorität (empa.ch/web/s608/guesthouses)

**Neue SUBURBS_OF Solothurn** (Siedlungsstrategie Kanton SO, Primärquelle):
- Balsthal (Regionalzentrum Thal)
- Oensingen (Regionalzentrum Gäu)
- Dornach (Regionalzentrum Dorneck)
- Breitenbach (Regionalzentrum Thierstein)

**Regulatorische Stop-Datenbank `REGULATORY_STOPS`** in Liveness-Warner — höchste Priorität:
- Tessin gesamtkantonal seit 2022-02 (Registrierungspflicht + 90-Tage-Regel) → Lugano, Bellinzona, Locarno, Mendrisio, Paradiso
- Stadt Luzern seit 2025-01 (STR-Reglement)
- Davos + Klosters seit 2021-03
- Arosa (Tourismusabgabe-Registrierung)
- Sigriswil seit 2024-11 (Planungszone 24 Mt nach +75% Listings-Wachstum)

Pro Eintrag: `since` + `note` + `source` (alle Primärquellen aus sab.ch / stadtluzern.ch / dkinfo.ch). Render im Liveness-Warner: ⛔ Banner mit Quelle.

**SUBURBS_OF Zug-Korrektur**: Hypothese „Cham/Risch/Steinhausen/Hünenberg = sekundäre Zentren mit messbarer Zentrumsbildung" wurde adversarial mit 0-3 widerlegt (3 Verifikations-Voten). Notes korrigiert auf neutral „Pendler-Wohngemeinde" + Caveat-Hinweis im Note-Text. Suburb-Einträge bleiben (Pendler-Funktion belegt), aber „Zentren"-Anspruch entfernt.

**Coords.js erweitert** um Villigen + 4 Solothurner Regionalzentren.

**Roadmap nicht-integriert (offene Recherche):**
- BFS PASTA (Parahotellerie-Statistik) — Frage in Recherche nicht vollständig verifiziert
- BFS Wohnungsleerstand — Frage nicht vollständig verifiziert  
- BFS Mietpreisindex — Frage nicht vollständig verifiziert
- ARE Wohnungsinventar (opendata.swiss) — Pipeline könnte 331 Cap-Gemeinden integrieren (verifiziert verfügbar)
- Spital-Patienten-Familien-Bedarf außer Uni-Spitäler — nicht beantwortet

### Verifiziert
- Lugano/Bellinzona/Mendrisio/Locarno/Paradiso → Reg-Stop-Banner sichtbar
- Stadt Luzern → Reg-Stop-Banner
- Davos + Klosters → Reg-Stop-Banner
- Sigriswil → Reg-Stop-Banner
- Solothurn → Suburb-Liste mit Balsthal/Oensingen/Dornach/Breitenbach
- Dübendorf → Empa + Eawag in Großarbeitgeber-Liste (3'000 MA total)
- Zug-Suburbs → Caveat-Note „adversarial 0-3 widerlegt" sichtbar
- Baden → keine Reg-Stop-Warnung (Liveness-Warner behält Business-City-Logik)

## [0.9.24] — 2026-05-25

### Hinzugefügt — Phase C: Brave Search API für vollautomatische Konkurrenz-Recherche
Adrian: „he dann machen wir C" — entschieden für den vollautomatischen Pfad statt OSM-Erweiterung.

Komplette Pipeline gebaut analog zu `fetch_communes.py`:

**Backend `tools/fetch_competitors.py`:**
- Pro Markt 3 Brave-Search-Queries: „Business Apartments [Markt]" · „möblierte Wohnung [Markt]" · „Coworking [Markt]"
- Country=ch, lang=de, max 10 Results/Query
- Filter: Aggregatoren raus (Wikipedia, TripAdvisor, Homegate, etc.)
- Dedup nach Domain (gleiche Domain in mehreren Queries = 1 Eintrag)
- Max 8 Konkurrenten pro Markt
- Rate-Limit: 1 query/sec (Brave Free-Tier-Compliance)
- Robustes Error-Handling: bei API-Abriss bleibt letzte Snapshot intakt
- Updated `_health.json.competitors_brave` mit last_success + queries_used

**Bootstrap `data/competitors.json`** mit 5 Märkten (Baden/Zürich/Luzern/Bern/Basel) im neuen Schema — wird beim ersten Refresh-Run ersetzt.

**Frontend Integration:**
- `loadCompetitors()` lädt parallel zu loadHealth/loadCommunes/loadHesta
- `getCompetitorsFor(name)` merged hardcoded COMPETITOR_LISTS (kuratierte Notes haben Priorität) mit Auto-Detection (ergänzt um neue Anbieter via Domain-Dedup)
- UI zeigt zwei Sektionen wenn beide vorhanden: „Kuratierte Anbieter (mit Notes)" + „🤖 Auto-detektiert via Brave Search"
- Badge zeigt Source-Count: `● kuratiert 5 + auto 3`

**Pricing & Skalierung:**
- Brave Free-Tier: 2'000 Queries/Monat → 60 Märkte × 3 Queries = 180/Monat → kostenlos
- Base-Tier $3/1000 Queries falls Skalierung auf alle 197 Märkte = 591 Queries/Mt

**Workflow erweitert:**
- `.github/workflows/refresh-data.yml` ruft `fetch_competitors.py` monatlich auf
- Env-Variable `BRAVE_SEARCH_TOKEN` als GitHub-Secret

**Setup-Aufgabe für Adrian (manuell, 5 Min):**
1. Brave-Account erstellen: https://brave.com/search/api/
2. API-Token kopieren
3. GitHub Repo Settings → Secrets and variables → Actions → New repository secret
4. Name: `BRAVE_SEARCH_TOKEN`, Value: [Token einfügen]
5. Workflow manuell triggern: Actions → Refresh BFS Data → Run workflow
6. Beim nächsten 5. des Monats läuft es automatisch

**Daten-Tier:**
- Bootstrap data/competitors.json = 🟡 MOD (kuratiert)
- Nach erstem Brave-Run = 🟢 verified (echte API-Results)
- Hardcoded COMPETITOR_LISTS bleibt als Sicherheits-Fallback (Notes haben höhere Qualität als Snippets)

## [0.9.23] — 2026-05-25

### Hinzugefügt — Konkurrenz-Recherche pro Markt (Quick-Search + kuratierte Liste)
Adrian: „Diese arbeit muss für jeden ort gemacht werden als die analyse individuell mit abfragen" (mit Screenshot von Google-Suchresultat „Business Apartments Baden" mit konkurrierenden Anbietern: 1905 Baden, Konnex, Trafo Hotel, GLANDON Apartments).

Im Konkurrenz-Analyse-Block neuer Sub-Block „🔍 Konkurrenz-Recherche":

**1) Kuratierte Top-Konkurrenten** für 5 Bootstrap-Märkte (Baden aus Adrians Screenshot, plus Zürich/Luzern/Bern/Basel als manuelle Recherche):
- **Baden**: 1905 Baden, Konnex, Trafo Hotel, GLANDON Apartments (direkter Wettbewerber), Dein Baden Tagungsräume
- **Zürich**: VISIONAPARTMENTS, The Lyceum, Citizen M, Aparthotels Adagio
- **Luzern**: GLANDON, VISIONAPARTMENTS, B2 Boutique Hotel
- **Bern**: BERNAPARTMENTS, Casa Hotels, VISIONAPARTMENTS
- **Basel**: VISIONAPARTMENTS, Pure Apartments, Aparthotels Adagio

Jeder Eintrag: Name + direkter URL-Link + Kategorie + Notiz mit USP/Positionierung.

**2) Quick-Search-Buttons** mit pre-filled Google-Queries (8 Varianten):
- 🏢 Business Apartments [Markt]
- 🏠 möblierte Wohnung [Markt]
- ☕ Coworking [Markt]
- 🏨 Hotel [Markt] Booking preisvergleich
- 🔑 airbnb [Markt]
- 🏘️ Hausverwaltung [Markt]
- 🌐 site:linkedin.com „travel manager" [Markt] (nur bei Großarbeitgebern > 1000 MA)
- 🏥 Spital [Markt] Patientenbüro Unterkunft (nur bei Spital in Employers)

1 Klick öffnet Google-Suche mit perfekter Query — Adrian muss nicht selbst Query formulieren.

**Verifizierte Anwendung:**
- **Baden**: 5 kuratierte Anbieter + 8 Quick-Search (inkl. Spital wegen Kantonsspital Baden + LinkedIn wegen ABB 6500 MA)
- **Zermatt**: keine kuratierte Liste + 6 Quick-Search (keine Spital/LinkedIn weil keine Großarbeitgeber in EMPLOYERS)

**Roadmap-Hinweis im UI:**
- **Phase B**: OSM-Erweiterung um `tourism=apartment`, `office=coworking`, `tourism=guest_house` → Auto-Liste pro Markt aus OSM-POIs
- **Phase C**: Brave Search API ($3/1000 Queries, 2000 gratis/Mt) → vollautomatische Per-Markt-Recherche analog `fetch_communes.py` mit Health-Tracking

## [0.9.22] — 2026-05-25

### Hinzugefügt — Konkurrenz-Analyse-Modul (Pareto + Channel-Map)
Adrian: „Ich denke das ist wie eine Prozessanalyse. Die gemacht werden muss. Zu Punkt 3 was gibt es für Konkurrenz? Das Tool muss das können. Man muss dann vielleicht auch andere Kanäle nutzen — hier kommt mir wieder mein Green Belt in den Sinn für Six Sigma."

Adrians DMAIC-Framing integriert. Neuer Block im Markt-Detail mit zwei Komponenten:

**1) Pareto-Verteilung der Listings:**
- Top 10% verdienen = avgRevenue × 3.5
- Median (50%) = avgRevenue × 0.85
- Bottom 30% verdienen = avgRevenue × 0.4
- avgRevenue = m.revpar × 365 × STR-Adjust

**STR-Adjust-Faktor** basierend auf Liveness-Risk:
- HIGH-Risk: 35% (Hotel-Occ massiv überoptimistisch für STR)
- MED-Risk: 65%
- LOW-Risk: 85% (Hotel-Occ als guter STR-Proxy)

**2) Channel-Map mit 10 kuratierten Kanälen:**
- **Standard** (Airbnb, Booking.com, Vrbo, Interhome, HomeToGo) — gesättigt = Bottom-50%
- **Eigener Channel** (Direktbuchung-Website) — 100% Marge bei Repeat-Kunden
- **B2B-Direct** (LinkedIn HR-Outreach, Klinik-Patientenbüro, Uni-Housing-Office) — nur bei passenden Großarbeitgebern angezeigt
- **B2B-Platform** (HRG, BCD, Egencia) — nur bei Multinational-Konzernen sichtbar

Channel-Filter dynamisch: zeigt nur relevante Kanäle pro Markt (z.B. Klinik-Kanal nur wenn Spital in EMPLOYERS, Uni-Kanal nur bei Hochschul-Standorten).

**Verifizierte Beispiele:**
- **Baden** (HIGH-Risk Business-Stadt): Top-10% CHF 39k · Median CHF 9k · 9 Channels relevant (inkl. LinkedIn ABB-Outreach + Klinik Kantonsspital + Corporate-Tools)
- **Zermatt** (LOW-Risk Touri-Resort): Top-10% CHF 257k · Median CHF 62k · 6 Channels (Standard + Direktbuchung)
- **Engelberg**: Top-10% CHF 170k · Familie + Resort-Channels

**Konkurrenz-Strategie-Insight im Banner:** „Nicht in die Pareto-Mitte gehen wo 60% der Listings nur Ø verdienen. Top 10% positionieren (Superhost + Multi-Channel + Pro-Setup) oder klare Nische bedienen (Crew/medizinisch/Familie 6+)."

### Hinzugefügt — Glossar „DMAIC" + „Konkurrenz-Analyse"
Neue Glossar-Einträge dokumentieren:
- **DMAIC** als Tool-Framework mit konkretem Baden-Beispiel pro Phase (Define/Measure/Analyze/Improve/Control)
- **Konkurrenz-Analyse** mit Pareto-Formel, STR-Adjust-Faktoren und Strategie-Empfehlung

## [0.9.21] — 2026-05-25

### Hinzugefügt — Markt-Chancen-Scout (Persona-Hotel-Vergleich + Großarbeitgeber)
Adrian: „Frage über alles muss ich solche probleme nun finden oder können wir auch etwas entwickeln das genau das tut? Ein trick den ich hatte um die preise etwas zu kalkulieren war: Ichversetzte mich in die lage eines Familienvaters und suchte nach angeboten. Ich wollte doch meiner Familie etwas bieten. Also schaute ich mir zuerst die Hotels an und mit entsetzen stellte ich fest ich bezahle für ein ganz einfaches hotel für 4 personen den betrag x. Ich wusste gleichzeitig was ich als airbnb anbot und machte ihm einen besseren deal als das Hotel — das funktionierte sehr gut. Das selbe würde auch funktionieren als typ der business mässig zu ABB muss."

Adrians Methode als Algorithmus implementiert. Neuer Block im Markt-Detail oberhalb der Earn-Card.

**Datenstruktur GROSSARBEITGEBER**: hardcoded für 17 wichtigste CH-Standorte mit Firma + Sektor + Mitarbeiterzahl + km zum Zentrum + Notiz. Beispiele:
- Baden: ABB (6'500), Axpo (1'500), GE Power (1'200), Kantonsspital (2'700)
- Kloten: Flughafen ZRH (1'900) + Swiss/LH (9'000) + Swissport (4'000)
- Basel: Roche (12'000), Novartis (11'000), Unispital (8'000)
- Bern: Bundesverwaltung (38'000), Swisscom (7'000), Inselspital (11'000)
- Zug: Glencore, Roche Pharma, Crypto-Valley-Cluster

**4 Personas** mit Hotel-Aufschlag-Modell und Apartment-USP:
- 💼 **Business-Reisender** (Mo-Fr): Hotel ab CHF 110, Apartment-USP Wochenpaket+Küche
- 👨‍👩‍👧‍👦 **Familie 4 Personen**: Hotel × 1.70 (Familienzimmer-Aufpreis ab CHF 200), Apartment 2 SZ+Waschmaschine
- 💑 **Paar Wellness**: Hotel × 1.30 (ab CHF 150), Apartment Romantik+Spa-Korb
- ✈️ **Flugcrew/Logistik**: Hotel ab CHF 90, Apartment Direktverträge mit Airlines

**Pro Persona berechnet**: was kostet ein Hotel realistisch (BFS-ADR × Persona-Multiplier), was kannst du anbieten (-25% Diskont), klares USP gegen Hotel, **konkrete Sichtbarkeit-Channels** (Booking.com Business, Airbnb Familien-Filter, LinkedIn HR-Outreach, Crew-Direktverträge etc.).

**Verifizierte Klassifikation:**
- **Baden** → ABB (6'500 MA) + 3 Personas (Business + Familie + Wellness wegen Thermalbad)
- **Kloten** → Aviation-Cluster (~15'000 MA) + Business + Crew (Crew-Persona triggert nur bei Flughafen-Distanz < 15 km)
- **Engelberg** → Familie + Wellness (Lifte > 5 → Resort-Setup)
- **Bad Ragaz** → Wellness Only (Thermalbad-Pattern)

**Daten-Tier-Transparenz:**
- 🟢 Arbeitgeber-Liste kuratiert aus öffentlichen Firmen-Websites
- 🟡 Hotel-Preise BFS-ADR × Persona-Aufschlag-Modell
- 🔴 Personas Branchen-Heuristik (whenSuitable-Logic)

## [0.9.20] — 2026-05-25

### Hinzugefügt — STR-Liveness-Warner (Hotel-Daten ≠ STR-Daten)
Adrian: „ich habe mir Baden angeschaut da gibt es nicht wirklich ein angebot auf airbnb. Ich habe mir jetzt eine unterkunft angeschaut die hat in einem ganzen Jahr 4 bewertungen der Kalender ist aber offen wie es mir scheint. Ich sehe ehrlich gesagt ein sehr hohes risiko. Jedoch du sagst etwas andres."

**Field-Check zeigte systematischen Bug:** Tool benutzt BFS-Hotellerie-Auslastung (41% Baden) als Proxy für STR-Auslastung. Das funktioniert in Touri-Resorts, ist aber in Business-Märkten systematisch zu optimistisch. Adrians Baden-Listing: 4 Reviews/Jahr → ~5-10% reale STR-Occ, nicht 41%. Differenz Faktor 4-6×.

Neuer roter/gelber Warn-Banner im Markt-Detail oberhalb der Earn-Card. Triggert bei:
- **Listings < 100** → HIGH (Markt zu klein)
- **Listings < 250** → MED
- **City-Profile aber nicht Premium** (Zürich/Genève/Basel/Lausanne/Bern/Luzern) → HIGH (Geschäftsreisende übernachten in Hotels, keine STR-Demand)
- **Hotel-Occ ≥ 40% + City + nicht Premium** → HIGH (Mismatch Hotel-STR-Demand)
- **Wenige OSM tourism_info-POIs** → MED

Banner enthält **konkrete Sanity-Check-Anleitung**:
1. 3-5 vergleichbare Listings auf Airbnb/Booking öffnen
2. Reviews-Anzahl letzte 12 Monate zählen
3. Kalender-Verfügbarkeit prüfen
4. Realistische STR-Occ berechnen: `(Reviews × 1.5 × 3 Nächte) ÷ 365`
5. Diese Realität in Custom-Karte eintragen statt Markt-Schnitt

Verifizierte Klassifikation:
- **Baden** → HIGH (3 Signale: Listings 165, Business-Stadt-Profile, Hotel-STR-Mismatch)
- **Olten** → HIGH (gleicher Pattern)
- **Zermatt / Zürich / Luzern** → keine Warnung (Premium-Touri/Premium-Stadt)

Roadmap: Inside Airbnb-Pipeline würde Reviews-pro-Listing-Statistik liefern → empirische STR-Occ statt Heuristik.

## [0.9.19] — 2026-05-25

### Hinzugefügt — Reality-Check für Custom-Slider gegen BFS-Markt
Adrian: „Worst 60'000 ist crazy high finde ich. Eine gute wohnung in Luzern mach ich einen tagesschnit von 145chf * 365 tage ergibt 53'000chf. Ich würde sagen in Luzern möglich weshalb sollt edas in Baden möglich sein?"

Adrian hatte recht — sein Custom-Input (Baden 4.5Z, ADR 200, Occ 60%) lag bereits **+57% über dem BFS-Markt-Schnitt** für 4.5Z in Baden, bevor irgendein Optimierungs-Hebel aktiviert wurde. Das war im Tool nicht transparent. Jetzt sichtbar:

**Custom-Slider zeigt unter jedem Slider** den Markt-Schnitt aus BFS + Delta-Prozent:
- ADR-Slider: „Markt-Schnitt 4.5Z: CHF 200 · +0% ggü Markt" (grün)
- Occ-Slider: „Markt-Schnitt 4.5Z: 38% · +57% über Markt — sehr optimistisch" (rot)
- Wenn Delta > 30%: Reality-Check-Banner: „⚠ Deine Annahmen liegen deutlich über dem Markt-Schnitt. Top-10% Listings möglich, aber nicht der Default-Fall."

**Optimierungs-Forecast bekommt Markt-Basis-Box** parallel zur Custom-Annahme:
- Links grün: 📊 Markt-Basis (BFS-modelliert) mit Optimierungs-Median
- Rechts: 🎛️ Deine Custom-Annahme mit Delta-Prozent
- Bei > 30% Abweichung: rote Border + Warn-Label

Verifiziert Baden 4.5Z:
- Markt-Basis: ADR 200, Occ 38% (BFS) → **CHF 32'350 brutto/Jahr**
- Adrian's Custom: ADR 200, Occ 60% → **CHF 50'950** (+57%)
- Jetzt sichtbar: das hohe Worst-Case-Stack-Resultat war Folge der optimistischen Basis-Annahme, nicht des Hebel-Modells.

Apfel-mit-Apfel für Adrian's Luzern-Anker:
- Baden 4.5Z Markt: CHF 32k brutto
- Luzern 3.5Z Markt: ~CHF 55k brutto (BFS Luzern Occ ~60% × ADR ~215 × 365)
- Luzern objektiv 70% stärker als Baden — Tool zeigt das jetzt im Markt-Basis-Vergleich

## [0.9.18] — 2026-05-25

### Hinzugefügt — Optimierungs-Forecast mit Range + Konfidenz (🔴 MOCK explizit gelabelt)
Adrian: „wenn ich es mir genauer anschauen möchte. Es könnte noch tiefer gehen. Eine 4 1/2 zimmer wohnung ist 60% ausgebucht kostet 200. Wie würde es aussehen wenn ich Superhost werde?" — gefolgt von Risiko-Filter: „wir raten nicht. Es geht um echte Investitionen anhand des Tools" und Pattern-Klärung: „wenn wir Schätzungen machen sagen wir das und sagen auch wie stark es variieren kann wie genau dass predictiv sein wird."

Neuer Block unter der Earn-Card mit 6 Optimierungs-Hebeln. **Strikt als 🔴 MOCK markiert** (Plausibilitäts-Schätzung, keine empirischen CH-Daten).

Pro Hebel Range statt Punkt-Schätzung:
| Hebel | ADR-Range | Occ-Range | Konfidenz | Median erreichbar |
|---|---|---|---|---|
| ⭐ Superhost-Status | +5–18% | +10–30% | MED | 40% der Hosts |
| 📸 Pro-Fotos | +2–12% | +5–18% | MED | 70% |
| 📈 Dynamic Pricing | +5–22% | +0–10% | MED | 55% |
| 🌟 4.8★+ Rating | +2–10% | +3–15% | LOW | 50% |
| 🌐 Plattform-Diversifizierung | +0–5% | +5–25% | MED | 75% |
| ✏️ Listing-Optimierung | +1–7% | +3–12% | LOW | 80% |

**Stack-Forecast** zeigt 3 Szenarien:
- Worst Case (alle Min-Werte stacked + Diminishing Returns)
- Median (Erwartungswert)
- Best Case (alle Max-Werte stacked)

Plus **Achievability-Prozent**: multiplikativ aus Pro-Hebel-Wahrscheinlichkeiten — verhindert Illusion dass alle Hebel parallel auf Median erreicht werden können.

Verifiziert an Baden 4.5Z, ADR 200, Occ 60% (Adrian's konkretes Beispiel):
- IST: CHF 43'800 Brutto/Jahr
- Stack Superhost + Pro-Fotos:
  - Worst: CHF 60'884 (+39%)
  - Median: CHF 74'292 (+70%)
  - Best: CHF 94'055 (+115%)
  - Wahrscheinlichkeit Median: 28% (40% × 70%)

**Ehrliche Quellen-Angabe pro Hebel**: „Plausibilitäts-Schätzung · Branchen-Konsens" statt erfundene Cornell/AirDNA-Zitate. Bei Klick auf MOD/MOCK-Badges öffnet sich neuer Glossar-Eintrag „Schätz-Modus" mit Tier-System-Erklärung.

Globaler Warn-Banner über dem Modul: „⚠ Schätzung, keine empirische Datenbasis — verwende für Investitions-Entscheidungen nur mit eigenem Sanity-Check."

Roadmap: Inside Airbnb-Pipeline (CH-Städte gratis CSV) würde Superhost-Lift auf empirische Werte heben → 🟡 MOD-Hochstufung möglich.

### Hinzugefügt — Glossar „Schätz-Modus" (Tier-System dokumentiert)
Neuer Eintrag erklärt 🟢 BFS / 🟡 MOD / 🔴 MOCK mit konkreten Beispielen pro Tier. Klickbar via neue „ⓘ Schätz-Modus"-Badges im Optimierungs-Forecast.

## [0.9.17] — 2026-05-25

### Hinzugefügt — Smart Suburb Detector (Auto-Klassifikation aus CH-Gemeinde-Liste)
Adrian: „es geht mir ja da drum das das system smart ist um solche sachen selbständig zu finden. und ja es ist richtig das wir nicht bauen wenn das risiko zu hoch ist."

Hardcoded SUBURBS_OF skaliert nicht. Jetzt liest das Tool die vollständige CH-Gemeinde-Liste und findet Vororte automatisch.

**Backend**: `tools/fetch_communes.py` holt alle ~2'131 CH-Gemeinden mit Koordinaten + Einwohnerzahl + Kanton via Wikidata SPARQL (Q70208 = Schweizer Gemeinde). Schreibt `data/communes.json` und updated `_health.json`. Robustes Error-Handling: bei API-Abriss bleibt letzte erfolgreiche Snapshot intakt, Status auf error → Banner gelb/rot.

**Bootstrap**: `data/communes.json` initial mit 90 wichtigen CH-Gemeinden (Mutterstädte + bekannte Vororte) befüllt für sofortige Funktion. Wird beim ersten echten Refresh-Run durch vollständige Wikidata-Liste ersetzt.

**Frontend**: Neue Funktion `autoSuburbsFor(motherCityName, radiusKm=15, limit=12)`:
- Alle Gemeinden in Luftlinien-Radius
- Ausgeschlossen: Gemeinden mit ≥40% der Mutterstadt-Einwohner (= eigene Stadt)
- Suburban-Score = log(Population) / max(km, 0.5) — bevorzugt nahe + signifikante Gemeinden
- Top-N sortiert nach Score

Verifizierte Auto-Detection:
- **Luzern**: findet Kriens (2.5 km), Emmen (3.2), Horw (3.6), Ebikon (4.3), Adligenswil (4.3) + zusätzlich Risch/Rotkreuz (13.8 km) das nicht in der kuratierten Liste war
- **Zürich**: Wallisellen, Opfikon, Dübendorf, Schlieren, Kloten (alle korrekt im 15-km-Radius)
- **Bern**: Köniz, Ostermundigen, Muri, Belp

**UI**: Neuer Block „🤖 Auto-detektierte Vororte — Smart Suburb Detector" oberhalb des kuratierten SUBURBS_OF-Blocks. Auto-Gemeinden die zusätzlich kuratierten Kontext haben sind grün markiert + „✓ kuratiert mit Kontext"-Label.

**Aktualisierungs-Garantie** (Adrian's Risiko-Filter):
- GitHub Action `refresh-data.yml` ruft `fetch_communes.py` monatlich auf
- `data/_health.json.sources.communes_wikidata` trackt last_success / status / Frequenz
- Bei Wikidata-Abriss: last_success bleibt stehen → Tage-Alter steigt → Banner gelb (>35d) / rot (>65d)
- Frontend fällt elegant zurück: wenn `communes.json` nicht ladbar → Auto-Block versteckt, kuratierte SUBURBS_OF bleibt

## [0.9.16] — 2026-05-25

### Hinzugefügt — Daten-Health-Layer (Adrian's Aktualitäts-Garantie)
Adrian: „wenn etwas monatlich publiziert wird ist das okay aber das muss getrkt werden wenn es dort einen abriss gibt die daten müssen immer autonom gezigen werden ach einem monat um das tool aktuel zu behalten ansonsten ist es nicht gut. wir sollten auch kein risiko eingehen wenn wir das nicht sicher stellen können."

Zentrale `data/_health.json` mit Status pro Datenquelle (BFS HESTA, BFS Origins, OSM POIs, Markt-Koordinaten, Steuersätze, Suburbs). Pro Eintrag: last_success, expected_frequency (monthly/continuous/yearly/static), period_covered, status (ok/warn/error), Quelle-URL, Note.

Frontend `loadHealth()` → `renderHealthBanner()`:
- Header-Pille statt „BFS-Snapshot lädt…": **🟢 Daten frisch · Stand 2026-05-15** / 🟡 Refresh überfällig / 🔴 Daten veraltet
- Klick öffnet Detail-Modal mit Status pro Quelle, Tage-Alter, Frequenz, Schwellwerte
- Bei warn/error: zusätzlicher gelber/roter Banner über der Karte
- Schwellwerte: monthly < 35d OK, < 65d Warn, > 65d Error · continuous < 14d OK · yearly < 400d OK · static immer OK

Roadmap: GitHub Action `refresh-data.yml` schreibt _health.json bei jedem erfolgreichen Refresh-Run. Bei Fehler bleibt last_success stehen → Banner geht automatisch auf gelb/rot.

### Hinzugefügt — Karten-Filter „nach Use-Case"
8 Buttons über der Karte: ✈️🏢🎓🏥🎿🌊♨️👨‍👩‍👧. Multi-Select. Nicht-passende Marker auf 15% Opacity. Kombiniert mit Tier-Filter und Heimat-Filter. Filter-Info-Zeile zeigt aktive Filter: „Use-Case: 🏢 Business-Standort + ✈️ Airport-Hub".

### Hinzugefügt — Notfall-Score in Top-Tabelle
Neuer Sortier-Toggle: „nach RevPAR" (Default) vs „🚨 Notfall-Score" (RevPAR ÷ Fahrtzeit²). Letzteres bevorzugt nahe + gute Märkte und ist nur aktivierbar wenn Heimat-Standort gesetzt. Spalten zeigen zusätzlich 🚗-Fahrtzeit + Score. Title-Header passt sich an.

### Hinzugefügt — Earn-Card Setup-Presets
3 Setup-Varianten (Business/Familie/Wellness) als auto-vorgeschlagene Earn-Card-Werte:
- **Business**: ADR × 1.15, Occ × 1.05, CleanCost × 1.10, TV-Abo CHF 15
- **Familie**: ADR × 1.10, CleanCost × 1.20 (mehr Bettwäsche), TV-Abo CHF 45 (Kinder-Streaming)
- **Wellness**: ADR × 1.20, Occ × 0.95, CleanCost × 1.15 (Bademantel-Wäsche)

Jeder Setup-Tip-Block bekommt einen „🎛️ Preset in Earn-Card übernehmen →"-Button. Klick füllt `_earnCustom` mit den preset-gewichteten Werten relativ zur Markt-Baseline und scrollt zur Earn-Card.

### Hinzugefügt — SUBURBS_OF +4 Städte (Winterthur, St. Gallen, Lugano, Zug)
17 neue Vororte mit Koordinaten + Notes + Regulierungs-Status:
- **Winterthur**: Wülflingen, Töss, Wallisellen, Effretikon
- **St. Gallen**: Gossau, Herisau, Wittenbach, Rorschach
- **Lugano**: Paradiso, Massagno, Manno (Tecnopolo), Mendrisio (FoxTown)
- **Zug**: Baar, Cham, Steinhausen, Rotkreuz (Crypto-Valley / Roche / ABB)

Plus erweiterte `MARKET_COORDS` für Distanz-Berechnung auch bei Vororten.

### Verbessert — Resort-Tag-Klassifikation
Bug: Adelboden, Wengen wurden nicht als Resort getaggt weil OSM-aerialway-Count fehlt oder zu niedrig ist. Fix: Resort-Tag jetzt auch via Family-Whitelist oder profile=winter, mit klarem „OSM-POI-Daten fehlen" Hinweis im Why-Text. Adelboden + Wengen jetzt korrekt 🎿 Resort + 👨‍👩‍👧 Familie.

### Vereinheitlicht — Datenfrische-Indikator
Alte parallele Logik (BFS HESTA period_end → dataFreshness) entfernt. Alle Status-Anzeigen laufen über DATA_HEALTH. period_end aus HESTA wird in DATA_HEALTH.sources.bfs_hesta.period_covered gespiegelt.

## [0.9.15] — 2026-05-25

### Hinzugefügt — Familie + Wellness Use-Case-Tags
Adrian: „wo findet familie statt wo findet wellness statt ganz wichtige frage die zu verbinden sind mit den signalen"

Zwei neue Klassifikatoren in `deriveUseCases`:
- **♨️ Wellness-/Thermal-Markt HIGH** via Name-Pattern (Bad/Bagni/Bains, Leukerbad, Vals, Scuol, Ragaz, Yverdon, Zurzach, Saillon) ODER Tag „Thermalbad". Verifiziert: Bad Ragaz, Leukerbad, Vals, Yverdon, Baden — alle HIGH.
- **👨‍👩‍👧 Familien-Destination HIGH/MED** via Whitelist (22 etablierte Familien-Resorts) ODER (family_score > 70 + aerialway ≥ 5 oder Spielplatz ≥ 4 + lifestyle_score < 80 — nicht Party-Markt). Verifiziert: Saas-Fee, Engelberg, Davos = HIGH. Lenk, Adelboden, Wengen = MED.

Beide bekommen Setup-Tips:
- **Familie**: 4.5Z+, 2 Schlafzimmer, Stockbett, Hochstuhl, Geschirrspüler. Längere Stays 5–7 Nächte, weniger Wechsel, +10–15% ADR mit Skipass-Paket.
- **Wellness**: Thermalbad-Voucher als Welcome, Bademantel + Hausschuhe, Tee-Bar. Zielgruppe 50+. 3–4 Nächte Mi–So, +CHF 30–50/N, hohe Repeat-Rate.

### Hinzugefügt — Suburban Arbitrage: Vororte-Map
Adrian: „du kannst bern, luzern listen aber die sind ja eigentlich out of the game... hier wäre jedoch spannend welche umkreise sind nicht betroffen. ich weiss zum beispiel das horw neben luzern nicht betroffen ist das es ein bahnhof gibt mattenhof ist am bauen … was müsste gegeben sein das du das auch findest"

Neue Datenstruktur `SUBURBS_OF` mit kuratierten Vororten zu 6 Großstadt-Clustern (Luzern, Bern, Zürich, Genève, Basel, Lausanne) — total ~30 Vororte. Pro Vorort: Koordinaten, km zum Zentrum, ÖV-Anbindung, Autobahn-Distanz, Entwicklungs-Notiz, Regulierungs-Status.

Beispiel Luzern → **Horw** (Mattenhof-Entwicklung, Hochschule Luzern, S-Bahn 10 min, Autobahn 1.5 km, keine Cap-Beschränkung), Kriens (Mall of Switzerland), Emmen (Seetalplatz), Ebikon (Mall + Roche), Adligenswil (Schindler).

UI-Block in der Markt-Detail-Card:
- **Wenn aktiver Markt eine Mutterstadt ist** → „🏘️ Suburban Arbitrage — Vororte von [Stadt]" mit Grid aller Vororte (Bauprojekte, ÖV, Regulierung)
- **Wenn aktiver Markt ein Vorort ist** → grüner Banner „[Markt] = Vorort von [Stadt]" mit Direkt-Link zur Mutterstadt
- **Sonst** (Resorts wie Zermatt) → kein Block

Die These dahinter: Stadt = teuer + reguliert. Vorort = ähnliche Demand (Pendler, Konferenzen, Touri-Stop), aber tiefere Kaufpreise, weniger Konkurrenz, oft mildere Regulierung (z.B. Luzern hat 90-Tage-Cap, Horw nicht).

Verifizierte Klassifikationen: Luzern → Suburb-Block mit Horw/Mattenhof. Bern → Köniz/Belp. Kloten → „Vorort von Zürich" mit Crew-Übernachtungs-Hinweis. Zermatt → kein Block (echter Resort-Markt, keine Arbitrage-Logik).

## [0.9.14] — 2026-05-25

### Hinzugefügt — ALOS + Sommer/Winter-Ratio als Demand-Signale
Adrian: „gibt es auch gute beispiele von denen man lernen kann die irgendjemand wird die daten gesammelt haben und wie du es richtig sagst business buchen eher weniger am weekend. Die frage ist hier was sind die richtigen signale"

Das Tool nutzt jetzt zwei zusätzliche BFS-Signale die wir hatten aber ignorierten:

**1) Average Length of Stay (ALOS)** = `bfs.nights_12m ÷ bfs.arrivals_12m` aus Hotel-HESTA. Industrie-Standard-Klassifikation:
- ALOS < 1.8 = **Business** (Crew, Frühflug, 1-Nacht-Stops)
- ALOS 1.8–2.5 = **Citytrip** (Wochenend-Kurztrip)
- ALOS 2.5–4.5 = **Mixed** (Familien-Ferien)
- ALOS > 4.5 = **Resort** (Skiwoche, Sommer-Ferien)

Live-Werte aus Tool: Kloten 1.38 · Bern 1.73 · Zürich 1.83 · Lugano 1.91 · Engelberg 2.11 · Genève 2.16 · Zermatt 2.43 · Verbier 2.71 · Saas-Fee 2.77. Reihenfolge stimmt mit Branchen-Realität überein.

**2) Sommer-Winter-Ratio** = `mean(seasonality[Jun-Aug]) ÷ mean(seasonality[Dez-Feb])`:
- > 1.4 = **sommer-dominiert** (See, Stadt, Wander)
- < 0.7 = **winter-dominiert** (Ski-Resort)
- 0.7–1.4 = **ganzjährig** (Business, Mixed)

Live-Werte: Verbier 0.57 (Winter) · Zermatt 0.89 (ausgewogen wegen Sommer-Bergsteigen) · Kloten 1.31 (ganzjährig) · Bern 1.80 · Bellinzona 2.58 · Lugano 3.06 (Sommer-getrieben).

Beide Signale in `computeSiteSignals(m)` integriert + im UI sichtbar (🛏️ ALOS-Zeile + ☀️/❄️ Sommer/Winter-Zeile in der Use-Case-Card).

### Verbessert — Use-Case-Tag-Logik strenger
Kloten wechselt von Business MED auf HIGH wegen ALOS-Signal (kurze Stays). Resort-Tag dominiert jetzt korrekt: Engelberg/Zermatt zeigen nicht mehr Doppel-Tag (Resort + Citytrip). Citytrip-Tag nur gesetzt wenn weder Business noch Resort klassifiziert.

### Hintergrund — gold-standard Signale der Hospitality-Industrie
| # | Signal | Branche-Standard | Wir nutzen? |
|---|---|---|---|
| 1 | Day-of-Week-Index | Mo–Do vs Fr–So | ❌ BFS nur monatlich |
| 2 | ALOS | <1.8 Business · >2.5 Resort | ✅ NEU in v0.9.14 |
| 3 | Booking Lead Time | <14d Business · >30d Leisure | ❌ kostenpflichtige Daten |
| 4 | Saisonalitäts-Spread | flach=Business, peak=Resort | ✅ in v0.9.13 |
| 5 | Gäste-Origin-Mix | US/UK/Asien=Business · DE/FR/IT=Touri | ✅ in v0.9.13 |
| 6 | Sommer/Winter-Inversion | Stadt/See vs Ski | ✅ NEU in v0.9.14 |
| 7 | Channel-Mix GDS/OTA | Corporate vs Leisure | ❌ keine offene Quelle |
| 8 | Hotel-Bed-Dichte/Einwohner | Tourismus-Intensität | 🟡 BFS hat es, noch nicht integriert |

## [0.9.13] — 2026-05-25

### Hinzugefügt — Standort-Signale & Use-Case-Tags pro Markt
Adrian: „was mich auch beschäftigt ich könnte nähe flughafen kloten wohnungen haben die würde ich dann für buisness einrichten. Was müsste passieren das du solche sachen wie he ich kloten benötigt buisness übernachtung, der standort benötigt x, das brauch ich"

Neuer Banner in der Markt-Detail-Card oberhalb der KPIs: „🎯 Standort-Signale & Use-Cases". Aktiviert eine Use-Case-Klassifikation pro Markt aus existierenden BFS- und OSM-Daten — ohne neue API.

Berechnete Signale (`computeSiteSignals(m)`):
- **Flughafen-Distanz** (Haversine zu ZRH/GVA/BSL/LUG/BRN)
- **Hauptbahnhof-Distanz** (Zürich HB / Bern HB / Basel SBB / Genève / Lausanne / Luzern)
- **Business-Gäste-Mix** = % US + UK + Indien + China + Japan + Korea + Israel + UAE
- **Touri-Gäste-Mix** = % DE + FR + IT + AT + NL + BE
- **Saisonalitäts-Spread** (max/min des BFS-Monatsvektors) + Flatness-Score
- **Markt-Reife** = nights_12m ÷ listings (Hotel-Nächte pro STR-Listing)
- **OSM-Counts**: aerialway, hotels, hospitals, restaurants
- **Research-Hub** Set (ETH/EPFL/Uni-Standorte)

Abgeleitete Tags (`deriveUseCases(m, s)`):
- ✈️ **Airport-Hub HIGH** wenn Flughafen < 15 km
- 🏢 **Business-Standort HIGH/MED** wenn US/UK/Asien-Gäste > 20% UND Saison flach (Ratio < 1.5×)
- 🎓 **Bildungs-/Forschungs-Cluster** für Zürich/Lausanne/Bern/Basel/Genève/St. Gallen/Fribourg/Neuchâtel/Lugano
- 🏥 **Klinik-Cluster** wenn OSM hospital > 0 UND nights_12m > 50k
- 🎿 **Resort-Tourismus** wenn OSM aerialway > 10
- 🌊 **Sommer-/See-Tourismus** wenn profile=summer UND aerialway < 5
- 🏠 **Generischer Markt** als Fallback

Verifizierte Klassifikation:
- **Kloten** → ✈️ Airport HIGH (2.8 km ZRH) + 🏢 Business MED (25% US/UK/Asien, Saison 1.5× flach)
- **Zürich** → ✈️ + 🏢 + 🎓
- **Zermatt / Verbier / Davos / Engelberg** → 🎿 Resort HIGH
- **Lugano** → ✈️ + 🎓 + 🌊
- **Baden** → 🏥 Klinik-Cluster

Business-Setup-Tip-Block erscheint automatisch wenn 🏢 Tag aktiv: „Schreibtisch + WLAN als Pflicht, weniger Deko, kein TV-Schwerpunkt · +15–20% ADR ggü. Touri-Setup, kürzere Stays (1–2 Nächte statt 4), Mo–Do höher als Wochenende."

Plus: 6 fehlende Flughafen-Vorort-Koordinaten in `js/coords.js` ergänzt (Kloten, Opfikon, Rümlang, Wallisellen, Bülach, Dübendorf).

## [0.9.12] — 2026-05-25

### Hinzugefügt — Heimat-Filter: max Fahrtzeit ab Wohnort
Adrian: „Engelberg ist noch ein mögliches einzugsgebiet. das heisst dort habe ich noch die kontrolle. Ich kann ins auto steigen und bin im notfall in einer stunde dort. ich würde das aber nicht für das wallis machen mit 3.-4 stunden fahrt."

Neuer Filter direkt unter der Karte: **🏠 Mein Einzugsgebiet**. Dropdown mit ~20 Schweizer Städten (gruppiert nach Region) + Slider **max Fahrt** von 0.5h bis 4h (Schritt 15min).

Wie es rechnet (Heuristik, transparent gelabeled):
- Haversine-Distanz aus `MARKET_COORDS` (Luftlinie km)
- × 1.4 Strassen-Faktor (CH-Topologie, Pässe)
- ÷ 75 km/h Mix Autobahn + Landstrasse
- Verifizierte Werte ab Zürich: Engelberg 1h 10min (real ~1h 5min), Davos 2h 10min (real 2h 15min), Zermatt 3h 2min (real 3h 30min), Verbier 3h 15min (real 3h 15min)

Verhalten:
- Marker ausserhalb Radius werden auf 15% Opacity gedimmt und sind unklickbar
- Heimat-Pin als schwarzer Punkt mit gestricheltem Ring + Label 🏠 [Name] auf der Karte
- Filter-Info-Zeile: „X/81 Märkte sichtbar · 🏠 Zürich · max 2h"
- Markt-Detail-Subtitle erweitert: „… · 🚗 ~1h 10min ab Zürich"
- Karten-Tooltip beim Hover über Marker zeigt zusätzlich „🚗 ab [Heimat]: 1h 10min"
- Kombiniert mit Tier-Filter (Performance + Distanz gleichzeitig)
- Persistenz via `localStorage.swissstr_home` — Wahl überlebt Reload

Verifizierte Beispiele ab Zürich: 1h = 15 Märkte (Zentralschweiz inkl. Engelberg) · 1h 30min = 29 · 2h = 43 (mit Davos/Andermatt) · 4h = alle 81.

## [0.9.11] — 2026-05-25

### Hinzugefügt — Karten-Transparenz: was steckt hinter den Zahlen?
Adrian: „was ist das sind das daten von hotelübernachtung Airbnb beides. was ist es genau"

Unter der Hauptkarte „Top Schweizer STR-Märkte" neuer Quellen-Block mit 4 Zeilen (Badge + KPI + Quelle):
- 🟢 BFS — **Auslastung** = Hotellerie HESTA (188/197 Märkte verifiziert)
- 🟡 MOD — **ADR · RevPAR** = modelliert pro Markt-Profil, kein Airbnb/Booking-Scraping
- 🟡 MOD — **Listings** = STR-Schätzung (HESTA zählt nur Hotels)
- 🟢 BFS — **Saisonalität · Gäste-Mix** = HESTA Logiernächte Monatsvektor

Plus Footnote: „relative Reihenfolge der Märkte verlässlich · absolute CHF-Werte ±20% Schätzung". Klare Roadmap angedeutet: ADR/RevPAR gehen auf 🟢 sobald BFS Parahotellerie-Preise publiziert oder ein STR-Scraper läuft.

### Hinzugefügt — Karten-Filter Hoch/Mittel/Tief
Adrian: „zweitens könnte man es auch filtern zwischen hoch mittel und tief. wenn mann will"

Neue Filter-Toolbar zwischen Metric-Toggle und Karte: 4 Buttons (Alle · 🔴 Hoch · 🟡 Mittel · ⚪ Tief). Tertile werden dynamisch aus den Werten des **aktiven Metrics** (RevPAR/ADR/Auslastung/Grade) berechnet. Multi-Select möglich — z.B. Hoch+Mittel zeigt nur die oberen 2/3.

Nicht-gewählte Marker werden auf 15% Opacity gedimmt und sind unklickbar (pointer-events off). Metric-Wechsel rechnet die Tertile neu (z.B. von „RevPAR Hoch" auf „Auslastung Hoch" — andere Marker bleiben sichtbar).

Beispiel: 81 Marker total · Filter „Hoch" auf RevPAR → 28 sichtbar (≈ oberes Tertil) · Klick „Alle" → alle 81.

## [0.9.10] — 2026-05-25

### Hinzugefügt — Saisonalitäts-Chart klickbar → KPIs filtern
Adrian: „bei saisonal als beispiel will ich den monat anklicken oder mehrere und es soll sich der output oben entsprechend anpassen."

Monats-Bars im Saisonalitäts-Chart sind jetzt klickbar (Multi-Select). Beim Klick werden RevPAR / ADR / Auslastung oben auf die ausgewählten Monate gefiltert. Nicht-ausgewählte Bars werden gedimmt (25% Opacity), ausgewählte bekommen schwarzen Rahmen. Ein „× Filter zurücksetzen"-Button erscheint sobald mindestens ein Monat selektiert ist; Markt-Wechsel resettet automatisch.

Beispiel Engelberg: Default RevPAR 157 / ADR 245 / Occ 46% → Filter Feb+Jul → RevPAR 184 / ADR 312 / Occ 59% (Hochsaison-Peak). Delta-Zeile zeigt „Filter: Feb·Jul (2/12)" statt YoY-Wert.

Implementierung: `_seasonSelectedMonths` State, `onClick`-Handler in Chart.js options, neue `recomputeKpisForSeason(m)`-Funktion. Saisonalitätsprofil (BFS oder Profil) wird auf gewählte Indizes gemittelt und mit `m.adr` / `occOf(m)` multipliziert.

### Korrigiert — Konfidenz-Glossar: Verbesserungs-Pfad statt Konkurrenz-Vergleich
Adrian: „etwas darfst du nicht vom konkurenzprodukt reden. aber mein hauptpunkt ist du sagst was das problem ist also wenn du das kennst kannst du es grundsätzlich auch beheben. das heisst wenn der user spezifisch wird mit dem was er hat kannst du auch genauer werden richtig? das muss auch so aufgezeigt werden."

Konfidenz-Modal umgeschrieben in `js/glossary.js`:
- AirDNA-Erwähnung entfernt aus `caveat`
- `longDe`: klare Botschaft Markt-Ebene (±30–50%) vs. konkrete Wohnung (±10–15%)
- Neues `improve`-Feld mit 6-Punkte-Liste was der User selbst tun kann um die Spanne zu schrumpfen: ADR aus Listings mitteln, Saisonalität-Filter, exakter Mietzins, Putzkraft anpassen, Plattform-Modus wählen, Wohnungstyp setzen
- Faustregel: „jeder konkrete Input ersetzt eine Modell-Annahme. Je mehr du selbst weißt, desto enger die Spanne."

Renderer in `openGlossary()` um grünen `improve`-Block ergänzt (analog zu `caveat`/`example`).

## [0.9.9] — 2026-05-25

### Korrigiert — Pass-Through-Logik in Earn-Card
Adrian: „checke ob der preis pronacht so stimmt das der gast die putzfrau noch on top bezahlt das ist ein riesen unterschied. […] es gibt ja auch noch die möglichkeit die steuern für airbnb dem gast zu übertrage die dinge müssen zu 100% klar sein auch in der aufstellung klar aufgezeigt sein."

**1) Kurtaxe ist Pass-Through, nicht Kostenposten.** Bisher wurde Kurtaxe (2% von grossNights) aus dem NOI abgezogen — das war falsch. Der Gast zahlt sie separat oben drauf, der Host führt sie 1:1 an die Gemeinde ab → kein Netto-Effekt auf den Cashflow.

Fix in `compute()` und `customCompute()`:
- `noi = grossTotal − platformFee − mgmt − cleanCost − opex` (Kurtaxe NICHT abgezogen)
- Kurtaxe-Wert bleibt im return-Objekt für Anzeige

Beispiel Davos 3.5Z @ ADR 244 / Occ 67%: Cashflow vor Fix 10'206 − 847 = 9'359 → jetzt korrekt 10'206 (+847).

**2) Plattform-Gebühren-Toggle Host-only vs Split.** Neuer Toggle in der Custom-Card:
- **Host-only 14%** (Default, CH-üblich): Plattform-Gebühr komplett vom Host
- **Split 3% + 14%**: 3% Host + 14% Gast oben drauf (Airbnb-Option, in CH selten)

Davos-Beispiel: Cashflow Host-only 37'702 → Split 46'925 (+9'223 weil 11% weniger Plattform-Gebühr beim Host).

**3) MWSt-Hinweis-Banner ab CHF 100k Jahresbrutto.** Eingeblendet sowohl in den 3 Szenario-Karten als auch in der Custom-Card-Berechnung sobald `grossTotal > 100'000`. Hinweis auf 3.8% reduzierten Satz für Beherbergung + Beispiel-Betrag pro Jahr.

**4) Pass-Through visuell markiert.** Neue Sektion „↔ Durchlaufende Posten (nicht im Cashflow)" mit neutralfarbenem Background, ↔-Icon, Hinweis „Gast zahlt extra · Host führt 1:1 an Gemeinde ab". Putzgebühr/Putzkraft jetzt mit Marge-Differenz im Hint (z.B. „Marge 0 CHF" bei guestClean=cleanCost).

Custom-Card-Footer-Hinweis aktualisiert: „STR-Versicherung CHF 600 · Kurtaxe ist ↔ Pass-Through (Gast zahlt, Host führt ab — nicht im Cashflow)" — vorher lautete der Hinweis fälschlich „Kurtaxe 2% — kann der User nicht beeinflussen".

## [0.9.8] — 2026-05-25

### Hinzugefügt — Custom-Karte: einstellbare Kosten-Slider
Adrian: „es gibt dinge die fix sind die kommen so rein wie tax. Putzfrau soll auch einstellbar sein also all die dinge an denen ich etwas machen kann wie tv abo usw."

Custom-Karte um 4 zusätzliche Slider erweitert (Stellschrauben des Hosts):
- **Putzkraft pro Reinigung** (50–200 CHF, default je nach Wohnungstyp)
- **TV / Streaming / Spotify** (0–100 CHF/Mt, default 35) — neu!
- **Verbrauchsmaterial / Jahr** (500–5'000 CHF)
- **Verwaltung %** (0/5/15/25 — Self bis Full PM)

Klare Trennung im UI:
- 🎛️ **Deine Stellschrauben** (Sektion mit den 4 Slidern)
- ● **FIX** (Hinweis unten): Plattform-Gebühr 14% · Kurtaxe 2% · STR-Versicherung 600 — kann nicht geändert werden

Live-Recompute bei jedem Slider-Move. Beispiel verifiziert: TV von 35→100 CHF/Mt = +780 CHF/Jahr Kosten → Cashflow exakt um 780 niedriger.

## [0.9.7] — 2026-05-25

### Verbessert — Hero-Stats von trocken zu Catcher
Adrian: „diese info soll ein catcher sein. sie sollen einem geil darauf machen geld verdienen zu wollen."

Vorher: 4 trockene KPIs (2'413 Hotelbetriebe · 207'186 Betten · 39.1% Auslastung · 36.4M Logiernächte). Klang nach Statistik-Amt, nicht nach Geldverdienen.

Jetzt:
- **Hero-Zahl: „~10.1 Mrd CHF/Jahr Brutto"** — 5xl, rot, dominant
- 💰-Wasserzeichen im Hintergrund der Karte
- **+3.1% YoY** aus echtem Trendsetter-Durchschnitt
- 3 Sub-KPIs in Reihe: 50M Logiernächte · 23.1M Touristen-Ankünfte · 39.1% Auslastung
- Hinweis „Spitze: Zermatt 70.1%" unter Hotel-Auslastung
- **🏆 TOP-CASHFLOW-Karte** (gold-umrandet, klickbar):
  - „Gstaad · CHF 61k / Jahr / Wohnung möglich"
  - „BE · 52.7% Auslastung · RevPAR CHF 319"
  - → öffnet direkt Markt-Detail
- Marktvolumen-Berechnung: Hotel-Logiernächte × Branchen-ADR (220) + Parahotellerie-Schätzung (14M × 150)

Macht direkt Lust auf Markt-Detail-View. Klick auf TOP-CASHFLOW = einklick zum Markt.

## [0.9.6] — 2026-05-25

### Fixes — Karten-Kreisgröße nach gewählter Metrik
Adrian: „wenn ich Auslastung wähle sollte der grösste Kreis dort sein wo die Auslastung am höchsten ist".

- Korrekt — vorher war Kreis-Größe immer `m.listings`, egal welche Metrik gewählt
- Jetzt: bei „Auslastung" sind Zermatt (70%), Grindelwald (66%), Interlaken (64%) die größten Kreise
- Bei „RevPAR" sind Gstaad/Verbier/St. Moritz die größten — etc.
- Legende aktualisiert: „Kreis-Größe = gewählte Metrik (Top = größter Wert)"

### Hinzugefügt — „🎯 Exklusiv für dich"-Empfehlungs-Engine
Adrian: „cool wäre wenn du exklusiv für mich sagen kannst wo ich was haben sollte".

- **Prominenter Gold-Button** im Hero unter dem Suchfeld
- **Profil-Modal** mit 6 Achsen:
  - Setup-Budget (< 8k / 8–15k / 15–30k / 30k+)
  - Risiko-Toleranz (Konservativ / Balanced / Aggressiv)
  - Konzept-Präferenz (Business / Familie / Couple / Wellness / Sport / Mid-Term — multi-select)
  - Region (Stadt / Berge / See — multi-select)
  - Modus (Mieten / Kaufen)
  - Steuer-Sensitivität (Egal / Bevorzugt tief)
- **Scoring-Algorithmus** durchläuft alle 188 BFS-verifizierten Märkte
- **Top-5-Empfehlungen** mit Match-Score und 4 Begründungen pro Markt
- **Klick auf Empfehlung** → öffnet direkt das Markt-Detail
- Beispiel-Profil „Business + Mid-Term + Stadt + Tief-Steuer" → 🥇 Zug · 🥈 Zürich · 🥉 Genève

## [0.9.5] — 2026-05-25

### Hinzugefügt — Konfidenz-Indikator + konsistente Begriffe
Adrian: „man soll auch sagen wie genau das es ist wie du sagst plus minus 30-50% daneben. Was ich noch weiter finde die herleitung wenn sie sin mache müssen her wie auch die kürzungen das muss durchgängig sein oder du schreibst es aus was es ist wenn es sinn macht mit kürzel."

- **Konfidenz-Banner** prominent unter den Szenario-Karten:
  - „Absolute Werte ±30–50% daneben möglich"
  - 🟢 Verlässlich für relative Vergleiche, Sensitivität, Break-Even
  - 🟡 Mittel für Größenordnung
  - 🔴 Schwach für exakten Franken-Wert einer konkreten Wohnung
- **Klick auf „Konfidenz"** öffnet Glossar-Modal mit voller Methodik-Erklärung
- **Begriffe konsistent ausgeschrieben mit Kürzel-Erklärung in Klammern**:
  - „<span class='glossary-term' data-term='mgmt'>Verwaltung</span> 5%" (statt nur „Mgmt")
  - „<span class='glossary-term' data-term='nk'>Nebenkosten</span> (Strom/Wasser/Internet)" (statt nur „NK")
  - „Versicherung (<span class='glossary-term' data-term='str'>STR</span>-spezifisch)" (mit STR-Erklärung)
  - „Netto-Operating-Income (<span class='glossary-term' data-term='noi'>NOI</span>)" (vor Wohnungskosten)
  - „<span class='glossary-term' data-term='kurtaxe'>Kurtaxe</span> ~2% (wird an Gemeinde durchgeleitet)"
- **Glossar erweitert** um 5 neue Einträge: Mgmt, NK, STR, Putzgebühr, Konfidenz
- Alle Glossar-Terms in Earn-Card klickbar — Modal erklärt Definition + Formel + Beispiel

## [0.9.4] — 2026-05-25

### Hinzugefügt — Earn-Card: Custom-Szenario + Jahr/Monat-Toggle
- **4. Karte „🎛️ Eigene Berechnung"** mit zwei Slidern (ADR + Auslastung) zum Experimentieren
- Default-Werte aus „Solid"-Szenario, User kann frei anpassen
- Custom-Karte rechnet live mit allen Kosten + Mietzins durch
- **Jahr/Monat-Toggle** oben rechts neben Mietzins-Input
- Wechselt **alle 4 Karten** synchron zwischen Jahres- und Monats-Darstellung
- Vergleichszeile unter dem Cashflow zeigt jeweils die andere Periode („/Monat" wenn Jahr aktiv, „/Jahr" wenn Monat aktiv)
- Adrians Frage zur Lesart („CHF 7'484/Jahr = CHF 624/Monat?") jetzt direkt sichtbar via Toggle

## [0.9.3] — 2026-05-25

### Verbessert — Earn-Potential mit Wohnungs-Größen-Toggle
Adrian: „je nach Größe variiert das — bei einem Studio etwa 70 mit Bettwäsche und bei 2 1/2 90.– usw."

- **Toggle-Bar** über den Szenario-Karten: 1Z Studio / 2.5Z / 3.5Z / 4.5Z / 5.5Z+
- **Putzkosten** skalieren mit Wohnungsgröße (Adrians Werte): Studio 70 / 2.5Z 90 / 3.5Z 110 / 4.5Z 130 / 5.5Z+ 150 CHF pro Reinigung inkl. Bettwäsche
- **Verbrauchsmaterial** + **Strom/Wasser/Internet** skalieren ebenfalls leicht mit Größe
- **Default-Mietzins** passt sich automatisch an: Studio CHF 450 → Premium-Chalet CHF 1'500+
- **Putzgebühr-Logik**: Gast zahlt = was du an Putzfrau zahlst (Standardpraxis — wird 1:1 weitergeleitet)
- ADR + Auslastung skalieren auch mit Wohnungstyp

Beispiel Baden Studio (1Z) bei CHF 450 Miete: 4.5★ Median → +CHF 1'966 / Jahr.
Beispiel Baden Premium (5.5Z+) bei CHF 1'500 Miete: 4.5★ Median → ganz anderer Wert sichtbar.

## [0.9.2] — 2026-05-25

### Verbessert — Earn-Potential komplett überarbeitet
Adrian: „bei 45 % ausgebucht und 96.– pro Nacht verdiene ich keine 5000 — die Zahl ist so nichtssagend"

Korrekt. Probleme der alten Matrix:
- Endbeträge ohne Aufschlüsselung (woher kommen die CHF 5k?)
- Mietzins/Hypothek ignoriert (NOI fälschlich als „verdienen" verkauft)
- Putzgebühr-Logik unklar (ist die im ADR drin?)
- Zu komplex (20 Zellen ohne Erklärung)

Komplett umgebaut:
- **3 klare Szenarien** (Realistisch / Solid / Superhost) statt 5×4-Matrix
- **Stage-by-Stage-Aufschlüsselung** pro Karte: Mieteinnahmen + Putzgebühren = Brutto → minus Plattform/Mgmt/Putzkraft/Kurtaxe = NOI → minus Mietzins/Hypothek = echter Cashflow
- **Mietzins/Hypothek-Input** oben rechts — User trägt Mt.-Wert ein, alle 3 Karten rechnen live
- **Default-Mietzins** automatisch passend zum Markt (40% des STR-Brutto-Monats)
- **Putzgebühr-Klärung explizit**: Gast zahlt 80 CHF pro Aufenthalt extra (Standard Airbnb-Praxis), du zahlst Putzfrau 90 CHF
- **Monatlicher Cashflow** unter dem Jahres-Betrag (≈ CHF X/Monat) — direkt umrechenbar
- **Ampel-Farbe** auf Cashflow: grün ≥ 5k, schwarz ≥ 0, rot < 0

Baden Beispiel mit CHF 800/Mt Miete:
- 4.0★: −184 CHF/Mt (Verlust — zu teuer gemietet)
- 4.5★: +214 CHF/Mt
- 4.8★ Superhost: +624 CHF/Mt
→ User sieht sofort wo die Schmerzgrenze ist.

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
