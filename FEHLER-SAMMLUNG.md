# Fehler-Sammlung — Re-Audit 2026-06-22

> Auftrag Adrian: „weiter durchgehen, nicht halten wenn wir Fehler sehen, sondern **sammeln**."
> Diese Runde: Anwender-Walk (start/cockpit) + Daten-Integritäts-Scan über **alle** Märkte.
> **NICHT gefixt** — nur gesammelt. Reihenfolge = Schwere.

---

## 🔴 #1 — Auslastung tool-weit AUFGEBLÄHT (kaskadiert in fast jede Zahl)

**Was:** Die angezeigte `occ` {7,30,90} (`compdata.py:47 occ_by_horizon`) zählt **jeden** nicht-verfügbaren Kalendertag als „belegt" — **ohne zu trennen zwischen gebucht / Eigenblock / nicht-freigegeben.** Deine „gebucht-vs-geblockt"-Heuristik (`classify_calendar`) existiert, greift aber nur (a) ab **45 Tagen** Block und (b) nur fürs **Markt-Aggregat**, NICHT für die pro-Inserat-occ.

**Beleg:**
- occ30 liegt **+22 bis +37 pp über dem Roh-Kalender** in **JEDEM** Markt (Buochs +37, Ennetbürgen +34, Ingenbohl +32, Küssnacht +32, …, Kriens +22).
- **Jedes** Inserat hat einen ≥21-Tage-Dauerblock (Kriens 38/38, Horw 19/20, Ebikon 16/16, Weggis 47/50) — unmöglich für echte STR-Nachfrage bei min_nights 3 → Eigenbelegung / nicht-freigegebene Zukunft.
- **Lukas/Kriens** (dein Hinweis): occ30 **60–77 %** angezeigt, Roh-Kalender nur **28–32 %**, ein 24-Tage-Block.
- **Smoking Gun:** Der Code-Kommentar `fetch_airbnb_free.py:483` nennt genau dieses Inserat „~90 % belegt, dauergebucht" — das Tool **glaubt seiner eigenen Falschzahl.**

**Kaskade (alles Folge-Fehler von #1):** Cockpit-Schlagzeile (Kriens „Auslastung 30T 67 %"), Top-Verdiener-est (Stephanies 110'103 aus 13 Inseraten), **70 „Stille Perlen"** = falsche Positive (Schwelle ≥70 % occ läuft auf der aufgeblähten occ → Inserate mit ~40 % Roh erscheinen als 100 %-Perle), das Wettbewerbs-Raster, Akquise-Spielraum, start-Netto/Mt (bis 29'714), Kohorten-Schlagzeile.

**Wo fixen (später):** `compdata.py occ_by_horizon` + `fetch_airbnb_free.py classify_calendar`. Tages-Roh-Kalender ist in den Snapshots aufgehoben (`compdata.py:115`, `booked`-Liste) → vermutlich offline nachrechenbar.

---

## 🔴 #2 — Zwei STR-Engines widersprechen sich bei der Auslastung (kundensichtbar)

**Wichtig (verifiziert nach Adrians Frage „ist Atlas Hotel?"): NEIN — der Atlas zeigt die STR-Modell-Occ, nicht Hotel.** atlas.html rankt 188 STR-Märkte; die angezeigte Belegung ist `occ_band`/`occ_cube_pct` (STR-Modell). Die Hotel-Occ ist ein separates, daneben beschriftetes Feld (`hotel_occ_pct`, Kriens 61 %) — NICHT die hier verglichene Zahl. Also ist das ein echter **STR-vs-STR**-Widerspruch:

| Markt | **Atlas** STR-Occ (alte Engine, Review-Proxy + Band) | **Cockpit** STR-Occ (neue Kalender-Engine, occ30) |
|---|---|---|
| Kriens | **36–38 %** | **72 %** |
| Weggis | **42 %** | **77 %** |

Zwei STR-Engines, derselbe Markt, ~2× auseinander. Brisant: der Atlas labelt den **Kalender selbst als Obergrenze** und kommt auf 38 % — die Cockpit-Kalender-Engine kommt auf 72 %. Das bestätigt #1 (Cockpit-occ aufgebläht) UND zeigt, dass die alte (Atlas) und neue (Cockpit) STR-Engine nicht zusammenpassen. Gehört vereinheitlicht (eine STR-Occ-Wahrheit als Band).

---

## 🟡 #3 — Markt-Median-Preis mischt Zimmer + ganze Wohnungen

Cockpit Kriens „**Median Preis CHF 156**" enthält **14 Privatzimmer** (59–170 CHF), die den Median runterziehen. Median der **ganzen Wohnungen** = **242**. Betrifft auch die **Atlas-ADR** (157 ≈ derselbe verwässerte Wert). Für ein R2R-Tool (= nur ganze Wohnungen) **systematisch untertrieben** — und verzerrt jede Preis-/Spielraum-Vergleichsrechnung, die diesen Median nutzt.

---

## 🟡 #4 — Gleichnamige Operatoren nicht unterscheidbar (dein „Lukas Kriens")

- **Zwei verschiedene „Lukas" in Kriens** (24 Bew. / 144 Bew., verschiedene Host-IDs) — beim Anschauen nicht trennbar, genau deine Verwechslung.
- **20 Fälle** „gleicher Vorname + gleicher Markt" (Lukas/Kriens, Beat/Arth, Doris/Horw, Samuel/Baden, …), **81 Vornamen** mit mehreren Operatoren insgesamt.
- Kein eindeutiger Operator-Identifikator im Display (nur Vorname) → Verwechslungsgefahr bei jedem Namens-Zwilling.

---

## ✅ Geprüft und SAUBER (keine Regression)

- `lead_share > 100 %` / `n_operators > total`: **0 Fälle** (mein K11-Fix hält).
- `occ`-Werte außerhalb 0–100: **0 von 11'296**.
- Preis-Ausreißer-Cap (Spirit etc.): greift weiter.

---

## Offen — noch nicht durchgegangen (nächste Sammel-Runde)
netzwerk (Detail/Playbook/Karte) · akquise (Dossier-Rechnung/Verdict) · investor (data.js-RevPAR ggü. Engine — alte #1) · hotel · regulierung · datenqualitaet · positionierung · briefing (Bewegung/Pickup-Kurve).
