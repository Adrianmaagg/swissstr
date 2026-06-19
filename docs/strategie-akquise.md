# Strategie — Konkurrenz, Fokus, Eigentümer-Akquise (2026-06-19)

> Aus dem Architekt-Lauf (Daten: operator-network.json, competitor-profiles.json/33 Dossiers,
> insideairbnb-calibration.json). Adrians Fragen: Konkurrenz verstehen · Masse vs. 80/20 · wie an
> die Besitzer. Status: **Strategie-Grundlage, von Adrian noch zu bestätigen.**

## Prämissen-Check (was an der Fragestellung wackelt)
1. **Die „Garantiemiete-Lücke" ist NICHT leer — nur dünn besetzt, von den gefährlichsten.** 30 von 33 Dossiers stecken im Provisions-/Mandats-Lager; im Festmiete/Garantie/Zwischennutzungs-Feld sitzen schon **Interim Homes** (Garantiemiete mid-term ZH), **Sharedlock** (Zwischennutzung, **schon in Adligenswil/Horw — SHPs Heimrevier**, 1'061 Bew.), Swissstay, Smartroom, Limehome (Master-Lease 20 J.). Kein Greenfield — dünne Nische mit lokalen Platzhirschen.
2. **Konkurrenz dichter als die eigenen Zahlen** (InsideAirbnb: Zürich wir 0 % vs real 61 % Profi). „Riesig" stimmt — relevant ist nicht *wie viele*, sondern *wer im Garantie-Lager sitzt und wo nicht*.
3. **Masse vs. Fokus ist für einen Einsteiger keine echte Wahl** — Masse braucht Operations-Skala + Kapitalpuffer (Garantie = SHP trägt Leerstand selbst). Pareto hier = **ein Objekt-Profil × eine Mikro-Region**, nicht „20 % der Eigentümer".

## Empfehlung in einem Satz pro Frage
1. **Konkurrenz:** Provisions-Mandat überfüllt (30/33), Garantie-/Zwischennutzungs-Lager dünn aber von Interim Homes + Sharedlock besetzt; **Limehome ist strukturell zu gross, um ein Einzelobjekt zu wollen = SHPs Lücke**, die direkten Gegner sind Sharedlock + die ~60 lokalen Multi-Unit-Hosts, nicht die Berg-Agenturen.
2. **Fokus: radikal.** Ein Archetyp — **3.5–4.5 Zi, gehoben, anonyme Überbauung, Agglo OHNE 90-Nächte-Cap, ÖV nach LU/Zug/ZH, mid-term-fähig** — × **eine Heimrevier-Gemeinde** (Ebikon/Horw/Adligenswil/Kriens). Weil 77 % der lokalen Hosts bei 1 Objekt bleiben (STR skaliert nicht von selbst) und Garantie über viele Objekte ohne Puffer = ein schlechter Winter killt die Firma.
3. **Akquise:** **Verwaltungen (Rahmen, B2B-Hebel) + Leerstand/Zwischennutzung (risikoärmster erster Deal, Sharedlock-Modell) + der müde Selbstvermieter (Typ 2)** statt kalter Mietinserat-Masse — mit dem **Daten-belegten Garantiemiete-Pitch** als dem einen Hebel, der die fehlende Reputation ersetzt.

## Zwei Eigentümer-Typen, zwei Kanäle (Schlüssel-Befund)
- **Typ 1** = vermietet gerade neu (heutiges Akquise-Ziel: Mietinserat → Eigentümer). Kennt das Modell nicht, muss überzeugt werden.
- **Typ 2** = der getarnte Selbstvermieter, betreibt seine 1 Wohnung schon auf Airbnb, **müde** (234 Solo-Hosts/77 % im Graph). **Der bessere Kontakt** — lebt das Modell, SHP bietet Garantie + null Aufwand + kennt die echten Zahlen.

**Kanäle nach Hebel:** Netz (1 warmer Deal zuerst) → Leerstand/Zwischennutzung → Verwaltungen (1 Beziehung = mehrere Objekte über Zeit) → selektive Mietinserate. **Nicht** kalte Masse zuerst (mühsamster Kanal, schlechteste Conversion).

## Der erste Pitch (Daten ersetzen Reputation)
- **Gegen den Mieter:** „Garantiemiete 10–15 % über Markt, jeden Monat, unabhängig von Belegung · kein Ausfall/Leerstand · 2–3× / Woche profi-gereinigt = besser gepflegt · Versicherung bis 500k."
- **Gegen Limehome/Konzerne:** „Lokal, ein Gesicht, persönlich — Limehome will ganze Etagen, ich nehme genau Ihre eine Wohnung."
- **Der Edge:** „Ich habe [Gemeinde] für diesen Wohnungstyp durchgerechnet: Median X / Auslastung Y → Z. **Hier ist mein Rechenweg** — deshalb ist die Miete nachhaltig, nicht schöngerechnet." (= das Cockpit + Tier-Daten; kein Konkurrent legt das offen.)

## Die 3 grössten Risiken
1. **Garantie-Risiko trägt SHP allein + Markt dichter als gedacht** → liegt die echte occ näher am InsideAirbnb-Proxy (12–22 %) als am Free-Scrape (31 %), wird die Übermiete verlustbringend. *Mitigation:* mid-term-Fallback, erster Deal als kurze Zwischennutzung statt 3-Jahres-Garantie. **Garantie = Verkaufsargument UND grösstes Existenzrisiko, dasselbe.**
2. **Die Lücke ist besetzt** — Sharedlock sitzt im empfohlenen Heimrevier. SHP startet GEGEN sie. *Vor dem Pitch prüfen*, ob genug nicht-abgegraste Überbauungen da sind, nicht annehmen.
3. **Der Daten-Edge ist nur so gut wie die Daten** — die Profi-Blindheit (0 % vs 61 %) kann den Pitch entwerten, wenn der Eigentümer eigenes Marktwissen hat. *Mitigation:* InsideAirbnb-Kalibrierung verdrahten, im Pitch die **Auslastungs-Untergrenze** zeigen, nicht Best-Case (konservativ = auch Verkaufsargument).

## Nächster konkreter Schritt (einer)
Im Heimrevier-Kandidaten **Ebikon oder Horw** die grossen Überbauungen gegen die schon aktiven Operatoren (Sharedlock & Co. aus `operator-network.json` `market_coverage`) abgleichen → **die 5 Überbauungen finden, wo noch KEIN Profi sitzt** → dort gezielt Verwaltung + Leerstand ansprechen. Verbindet alle drei Antworten in einer konkreten Liste statt breitem Streuen.

## Lücke in der bestehenden Methode
`docs/akquise-dossier.md` zielt auf Typ-1-Mietinserate. **Fehlt als eigene Pitch-Pfade:** Verwaltungs-Rahmen · Zwischennutzung · Typ-2-Selbstvermieter.
