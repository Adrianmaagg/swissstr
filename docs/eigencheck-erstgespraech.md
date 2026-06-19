# Eigencheck & Erstgespräch — Arbeitsplatz-Paket

> Stand 2026-06-19, autonom erstellt (Adrian ging schlafen, Auftrag: „auf Herz und Nieren testen als Anwender/Partner/Vermieter, Airbnb-Zahlen gegenprüfen, als grosses Paket — nicht korrigieren, TODOs aufnehmen; und stell mir Inventar + Erstgespräch-Präsentation auf, damit ich rausgehen kann"). **Dies erfasst — es wird hier NICHTS am Code geändert.** Quellen für die Befunde: Code-Review dieser Session (`js/cockpit.view.js`, `compdata.py`, `fetch_airbnb_free.py`, Docs) + STATUS.md + Projekt-Memory.

---

# TEIL A — Was Du JETZT mitnehmen kannst (die Präsentation)

## A1. Inventar — Deine Munition (was schon da ist)

**Daten (echt, gratis):**
- ~28 Märkte tief gescraped (Belegung je Horizont, Tagespreis, Kalender, Pickup) — Stand 2026-06-19.
- 188 BFS-verifizierte Märkte (HESTA-Hotellerie), BFS-Mietpreise je Kanton×Zimmer.
- Operator-Netzwerk: 645 Betreiber, Co-Host-Graph, X-Ray-Gesamtportfolios (z.B. Secra 1207 Inserate).
- 33 tief recherchierte CH-Konkurrenz-Dossiers (Modell/Vertrag/Konditionen).

**Analysen (diese Session geschärft):**
- **Wettbewerbs-Raster** (Preis × Klasse, Kundensicht) — pro Markt sichtbar, wo Preismacht/Lücke ist.
- **R2R-Mietspanne**: Agglo konservativ +44–75 % über Marktmiete (Emmen +75, Horw +70, Kriens +63, Ebikon +44).
- **Risiko/Portfolio**: 1 R2R-Objekt = 6,3 % Verlust-Jahr; Portfolio diversifiziert das weg → R2R ist Portfolio-oder-nichts.
- **Positionierung**: Snowbird-Management (Luxus, asset-light, Vitznau) als verlust-fester LAUNCH + R2R-Arbitrage (Agglo) als SCALE = decorrelated Barbell.

**Tool-Seiten (Arbeitsplatz):** start · cockpit · netzwerk · briefing · akquise · datenqualitaet · hotel · regulierung · investor · positionierung.

**Akquise-Maschine:** pro-Eigentümer Dossier + Brief-Generator (akquise.html) — die Waffe, um einem Eigentümer mit Daten zu beweisen, was er liegen lässt.

## A2. Erstgespräch mit einem EIGENTÜMER/VERMIETER — Ablauf

**Kern-Pitch (datenbelegt, das ist Dein Edge):**
> „Ihr Objekt [Adresse] bringt aktuell [X / steht leer]. Vergleichbare Objekte 200 m weiter machen [Y]. Hier der Kalender, die Comps, die Velocity. Ich übernehme alles — diskret, lokal, Schweizer — und garantiere Ihnen [Betrag]."

**Ablauf (5 Schritte):**
1. **Beweis statt Versprechen** — Cockpit/Raster des Markts zeigen (echte Belegung/Preise der Klasse).
2. **Sein Objekt konkret** — Dossier aus akquise.html (was sein Typ/Grösse trägt).
3. **Das Angebot** — je nach Eigentümer-Typ:
   - *Luxus-Zweitwohnung (Pensionär/Eigennutzer):* **Snowbird-Management** — „ich hüte und vermiete Ihre Leerwochen, Sie zahlen nichts, kein Risiko, Rev-Share/Management-%".
   - *Investor/Vermieter:* **R2R mit Garantiemiete** — Festmiete über Marktmiete, Sie haben null Leerstand/Aufwand.
4. **Swissness betonen** — Vertrauen, Diskretion, lokal, Compliance (Kurtaxe/Zweitwohnungsgesetz kennst Du).
5. **Der Ask** — konkreter nächster Schritt (Besichtigung / Mustervertrag zusenden).

**⚠ BEVOR Du rausgehst — Substanz-Check (sonst nicht glaubwürdig, aus Projekt-Memory):**
- [ ] **Mustervertrag** R2R / Management bereit (rechtlich, SHP = Mieter nicht Verwaltung — Bausubstanz bleibt beim Eigentümer).
- [ ] **Versicherung** geklärt (Haftung Untervermietung).
- [ ] **Referenz** (mind. 1 Objekt/Fall, den Du zeigen kannst — oder ehrlich „Erstprojekt").
- [ ] **Brand/Auftritt** (SwissHomePartner — Visitenkarte/1-Pager).
- [ ] **WhatsApp/Kontaktkanal** professionell.
> Diese 5 sind der Unterschied zwischen „interessantes Gespräch" und „unterschriebenem Deal". Mindestens Mustervertrag + Versicherung + 1-Pager solltest Du dabei haben.

## A3. Erstgespräch BUSINESS-PARTNER / NETZWERK — kurz
- Pitch = lokaler Moat: „Ich bringe Daten + KI-Ops + lokale Hände; gemeinsam die unter-genutzten Objekte holen, die die Grossen (Limehome) nicht profitabel bedienen."
- Partner = Hände vor Ort (Putzen/Übergabe) + heimliche Deal-Quelle (lebt bei SHP/Marke, nicht im Tool).

---

# TEIL B — Eigencheck (auf Herz und Nieren) → TODO-Paket
*(erfasst, NICHT korrigiert)*

## B1. Als ANWENDER (Du im Tool)
- [ ] **Wettbewerbs-Raster (neu, v0.9.221):** im Cockpit selbst durchklicken — Zellen-Drill, Preismacht/Lücke prüfen, ob die Empfehlungs-Zeile Sinn macht. „min N" erscheint erst nach dem nächsten Cloud-Scrape (minNights-Code v0.9.222 ist drin, Bestandsdaten haben es noch nicht).
- [ ] **Cockpit-Dichte:** viele Karten — prüfen, ob die Reihenfolge (Pickup→Karte→Charts→Raster→Kurve→Geld→Prognose→Tabelle) für Dich der richtige Lesefluss ist.
- [ ] **Frische-Ampel:** Märkte mit Stand ~9 Tage prüfen — vor einem echten Deal frisch nachziehen.

## B2. Als PARTNER (jemand, der mit Dir arbeiten würde)
- [ ] **Es gibt KEINE partner-/netzwerk-orientierte Einstiegsseite** — netzwerk.html ist Analyse (grosse Spieler durchleuchten), nicht „so arbeiten wir zusammen". → Build C1.
- [ ] Partner sieht heute nicht: Rollen, was er beiträgt, was er bekommt. Fehlt komplett.

## B3. Als VERMIETER (eigentümer-facing) — die grösste Lücke
- [ ] **Das ganze Tool ist BETREIBER-facing (Deine Sicht), nicht eigentümer-facing.** Ein Vermieter, dem Du es zeigst, sieht Konkurrenz-Namen, Operator-X-Ray, interne Strategie — das willst Du ihm NICHT zeigen.
- [ ] Es fehlt die **eine saubere Eigentümer-Ansicht**: „Ihr Objekt → das bringt es → das garantiere ich → so läuft's". Heute müsstest Du das mündlich/aus dem Dossier zusammenstückeln. → Build C1.
- [ ] positionierung.html nennt Konkurrenten namentlich → **bewusst intern, nie einem Eigentümer zeigen** (steht so in STATUS, hier als Warnung wiederholt).

## B4. AIRBNB-ABGLEICH (Zahlen gegenprüfen) — Methode + offene Checks
> Konnte ich autonom nicht voll durchklicken (Runway/Block-Schutz). Hier die **Methode**, die Du (oder die nächste Session) abarbeitet — P0:
- [ ] **Belegung:** 3–5 Inserate aus dem Cockpit nehmen, URL auf Airbnb öffnen, Kalender ansehen. Tool-occ ist eine **Obergrenze** (gebucht ODER host-geblockt) → erwarte Tool-occ ≥ Realität. Wenn Tool deutlich höher als sichtbar plausibel → flaggen.
- [ ] **Preis:** Tool-Preis (USD×0.8) gegen den live angezeigten CHF-Nachtpreis halten (±Saison-Fenster beachten).
- [ ] **Bewertungen/Velocity:** Tool-Reviewzahl gegen Airbnb-Profil; „echte Perle" = ≥2 neue Bew. im letzten Monat (Velocity, nicht Lebenszeit).
- [ ] **Profi-Konkurrenz-Blindstelle (bekannt!):** Free-Scrape sieht Host-Daten kaum → Tool zeigt Profi-Anteil als **Untergrenze** (0 % vs. real ~61 % laut InsideAirbnb-Kalibrierung). Beim Eigencheck im Kopf behalten: die echte Konkurrenz ist dichter als das Tool zeigt.
- [ ] **occ@30 = Sommer-Nahfenster** (heute Juni) → als Jahreswert zu hoch; für Deals Jahresschnitt/konservativ rechnen.

**✅ Durchgeführt (Spot-Check Ebikon, 2026-06-19):** Tool-occ@30 (gespeichert) vs. LIVE Airbnb-Kalender, gerade gezogen:
- Fabio (id 1655632677390527223): Tool **47 %** = live **47 %** → OK
- Cornelia (id 1273596016923933966): Tool **67 %** = live **67 %** → OK

→ **Pipeline-Integrität bestätigt:** das Tool spiegelt Airbnb treu (exakter Match am selben Tag). **Aber (ehrlich):** das validiert nur, dass der Kalender korrekt erfasst ist — NICHT, ob die belegten Tage *gebucht* oder *host-geblockt* sind (strukturell unbeobachtbar). occ bleibt eine **Obergrenze**. Voller B4-Durchlauf (mehr Objekte, Preis + Reviews, Zielmärkte Emmen) bleibt P0 für die nächste Session.

## B5. Priorisierte TODO-Liste
**P0 (vor dem ersten echten Deal):**
1. Substanz-Check A2 (Mustervertrag, Versicherung, 1-Pager).
2. Airbnb-Abgleich B4 an 3–5 Objekten des Zielmarkts (Ebikon/Emmen).
3. Eigentümer-facing Ansicht (Build C1) — sonst kannst Du das Tool nicht herzeigen.

**P1 (Arbeitsplatz vervollständigen):**
4. Service-Apartments-Seite (C2).
5. Verträge/AGB-Seite (C3).
6. Wettbewerbs-Raster dogfood + minNights nach nächstem Scrape prüfen.

**P2 (später):**
7. Korrelierte Portfolio-/Mix-Rechnung (wie viele R2R über wie viele Märkte + wie viel Snowbird, P(Verlust)<2 %).
8. Public-Websites abspalten (C4).

---

# TEIL C — Build-Backlog (gehört in den Arbeitsplatz)
*(Deine Vision erfasst — gebaut wird in der nächsten Session)*

## C1. Seite Businesspartner / Vermieter + Netzwerk
- **Eigentümer-Modus:** saubere, eigentümer-sichere Ansicht (KEINE Konkurrenz-Namen): „Ihr Objekt → Ertrag → Garantie/Management → Ablauf → Vertrauen (Swissness)". Speist sich aus akquise-Dossier + Raster.
- **Partner-Modus:** Rollen, Beitrag, Was-er-bekommt, lokaler Moat.
- Navy/Gold, gleicher Header wie der Arbeitsplatz.

## C2. Seite „Unsere Service-Apartments"
- Die SHP-Angebotsseite (Gast = Hauptnutzer; vgl. bestehende `heimstatt/gast.html`-Logik, Navy/Gold).
- In den Arbeitsplatz integrieren (alles an einem Ort), später public abspaltbar.

## C3. Seite Verträge + AGB (eine Seite)
- Alle Verträge (R2R-Miete, Management/Snowbird, Eigentümer-Mandat) + AGB an einem Ort, abrufbar.
- Quelle: `heimstatt/docs/vertraege/` (existiert teils) — zusammenführen + verlinken.

## C4. Vision (Adrian) — später public
- Aus dem internen Arbeitsplatz werden 2–3 public Websites abgespalten: (a) Netzwerk/Business-Kunden, (b) Eigentümer/Vermieter, (c) Mieter/Gäste. Heute alles intern an einem Ort = Arbeitsplatz; Architektur so halten, dass Abspaltung später leicht ist.

---

## Hinweis nächste Session
Erster Task = **C1 (Eigentümer-/Partner-Seite)**, dann C2/C3. Davor B4 (Airbnb-Abgleich) als Realitäts-Check. Code unverändert in dieser Runde — reines Erfassen.
