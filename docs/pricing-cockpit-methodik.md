# Deal-Cockpit / Pricing-Methodik (Adrians Underwriting-Workflow)

Stand 2026-06-12 · Quelle: Adrians manuelle Methode, in mehreren Sessions diktiert.
Dies ist die Spezifikation für die Markt-Tiefenbohrung NACH dem Screening — „soll ich
hier anmieten, und zu welchem Preis?". Ergänzt das 188-Märkte-Screening, ersetzt es nicht.

Alles unten ist GRATIS aus dem öffentlichen Kalender + Suchdaten machbar (kein Bright Data).

---

## 1. Auslastung über Angebots-Knappheit (Adrians Schritt 1+2)

Statt Belegung pro Inserat aus Reviews zu schätzen: **Angebots-Knappheit** zum Zielmonat.

- Nenner = Gesamtzahl Inserate, die es gibt (Maximum, das je gesehen wurde).
- Zähler = wie viele davon im Zielmonat noch frei sind.
- Auslastung = 1 − frei/gesamt, je Tag/Monat.

Mit den per-Inserat-Kalendern (v0.9.108) für JEDEN Tag des Zielmonats rechenbar,
ohne manuelles Klicken. Bestätigt empirisch (Kriens-Plateau Juli–Nov ~35 %).

## 2. Drei Kalender-Kategorien (NICHT zwei!)

Der Snapshot zeigt „nicht verfügbar" — das hat DREI Ursachen, die getrennt werden müssen:

| Kategorie | Muster im Kalender | Behandlung |
|---|---|---|
| **gebucht** | verstreute kurze Sperren, Horizont weit offen | zählt als Auslastung (echtes Signal) |
| **host-geblockt / privat** | ein dominanter Langblock (≥45 d & ≥70 % aller Sperrtage) mitten im offenen Horizont | RAUS aus Auslastung (v0.9.108 `cal_managed`) |
| **noch nicht geöffnet** | alles offen bis Monat X, danach gleichmäßig zu (3-Monats-Horizont-Host, steuert so den Preis) | RAUS aus dem Nenner — nicht gebucht, nur nicht im Verkauf |

Die dritte (Adrian) ist in `_grid.py` erkannt: letzter freier Tag < Zielmonatsanfang
→ „not_released". Engelberg Oktober: 7 Inserate korrekt geflaggt.

## 3. Vorlaufzeit-Entzerrung über BFS-Saison (Adrians Predictive-Idee)

Der Kalender ist VORWÄRTSGERICHTET → naher Monat voll (kurzfristige Buchungen drin),
ferner Monat leer (Buchungen noch nicht eingegangen) — Timing, nicht Nachfrage.
Empirisch bestätigt: Kriens Juni 86 % → Juli–Nov flach ~35 %; Engelberg monoton fallend.

- **Flacher Markt (Stadt):** das Plateau der fernen Monate IST die wahre Auslastung.
- **Saisonaler Markt (Resort):** Vorlaufzeit + echte Saison vermischt → trennbar nur mit
  externer Saisonkurve = **BFS-Logiernächte Monat-für-Monat** (haben wir).

Modell: wahre Jahres-Auslastung ≈ nahe-Fenster-Auslastung ÷ BFS-Saisonindex(aktueller Monat);
restliche Monate über die BFS-Form projizieren → **Ski-Peak-Prognose schon im Juni**.
🟡 Annahme: Hotel-Saisonform ≈ STR-Saisonform — verteidigbar bei Resorts, schwächer bei Mischmärkten.
Plus BFS-YoY = stärker/schwächer als Vorjahr.

## 4. Wettbewerbs-Raster: Bewertungsklasse × Kapazität (Adrians Schritt 3, Kundensicht)

Preis ist KEIN Strich, sondern ein Raster — der Kunde sucht „beste noch verfügbare
Unterkunft fürs Geld, das er hat", und vergleicht innerhalb seiner Klasse.

- **Bewertungsbänder:** <4.5 · 4.5–4.69 · 4.7–4.89 · 4.9+ (ein 4.9-Host duelliert nur mit 4.9ern).
- **Kapazität:** Betten → Personen (~2/Bett): 1Zi/2P, 2Zi/4P (2 Paare ODER Familie) …
- Je Zelle: **wie viele noch frei** (Knappheit = Preismacht), **Preis-Boden**, **Median**, **typ. Mindestnächte**.
- Reviews-Anzahl als Glaubwürdigkeit der Bewertung mitführen.

Beispiel Engelberg Okt: 4.9+ / 2Zi/4P → 3 frei, Boden CHF 199, Median 286, minN 3.
Daraus: wo siedelt SICH der Nutzer an, um voll zu werden, ohne zu verschenken.

## 5. Mindestnächte als Vergleichsdimension (Adrian)

Hosts erlauben 1 / 2 / 3+ Nächte. Steht im Kalender (`minNights` pro Tag). Ein 1-Nacht-Inserat
konkurriert anders als ein 3-Nächte-Minimum — gehört als Spalte ins Raster.

## 6. Velocity über wiederholte Snapshots (Adrians Schritt 4 = v0.9.101-Gold)

„Wie viele Angebote gehen in den nächsten 2,3,4,5 Tagen weg" = echte Buchungsgeschwindigkeit,
GEMESSEN statt Proxy. Adrian unabhängig auf die v0.9.101-Snapshot-Velocity gekommen.
Braucht: denselben Markt an aufeinanderfolgenden Tagen scrapen, Inserate-IDs verfolgen
(Scraper-Contract speichert listing_ids je Lauf → Grundlage liegt), available→unavailable-
Übergänge je Inserat zählen. Frequenz entscheidet (täglich > vierzehntägig).

---

## ✅ GEBAUT: Wettbewerbs-Raster im Cockpit (Schritt 3 / §4 realisiert)

Stand 2026-06-19. Adrians Schritt-3-Kreuztabelle (§4) ist im Cockpit live (`cockpit.html` →
`js/cockpit.view.js` `renderRaster`), aus den bereits erfassten Daten — **kein neuer Scrape**.

**Warum:** Die 1D-Charts oben (Auslastung nach Bewertung, nach Kapazität, …) zeigen jede Dimension
*einzeln*. Der Gast entscheidet aber in einer *Zelle*: „beste verfügbare Unterkunft für meine
Personenzahl, in meiner Bewertungs-Klasse, fürs Geld". Erst die **Kreuztabelle** macht Preispunkt
*und* Lücke gleichzeitig sichtbar.

**Regel (verbindlich):**
- **Achsen** = Kapazität (Personen) × Bewertungs-Band, **gleiche Buckets** wie die 1D-Charts
  (`capBucket` / `ratingBand`) → keine zweite Wahrheit für dieselbe Einteilung.
- **Basis** = ganze Wohnungen **in der Gemeinde** (Punkt-in-Polygon), **NICHT** profi-gefiltert —
  es ist die *Kundensicht* (der Gast sieht alle). Bewusst entkoppelt von den 1D-Filtern (die sind die
  Achsen). Klar so beschriftet (Lehre aus der 3-Kohorten-Divergenz: jede Zahl trägt ihre Kohorte).
- **Pro Zelle:** Median-Nachtpreis (Going Rate), Median-Belegung im gewählten Horizont (Knappheit =
  Preismacht), Anzahl Angebote (Supply), Preis-Boden (Min). Belegung 🟡 (Kalender-Obergrenze), Preis 🟡.
- **Preismacht ⚑** = Median-Belegung ≥ Markt-Median (mind. 55 %) bei ≤ 3 Angeboten. **Lücke ⚑** =
  0 Angebote in einer Klasse, deren Grösse anderswo gut gebucht ist (Reihen-Belegung ≥ Schwelle).
- **Drill = eine Wahrheit:** Klick auf eine Zelle zeigt **genau** deren Angebote in Tabelle/Karte/
  Geld-Fluss (setzt cap + rating + Typ=Wohnung, Profi-Filter aus) — Zell-Count = Tabellen-Zeilen,
  keine divergente Zahl. Erneuter Klick = zurück zum Default.

**Abnahme (browser-verifiziert 2026-06-19, v0.9.221):** Vitznau (Resort) + Kriens (urban): Raster
rendert, 0 Konsolenfehler, reagiert auf den Horizont-Umschalter (Zell-Belegung ändert sich mit H),
Klick auf „4P / 4.8–5.0" (6 Angebote) → KPI „Inserate" = 6 **und** 6 Tabellenzeilen (deckungsgleich),
zweiter Klick stellt den Default (16, Profi an) wieder her. Preismacht-/Lücken-Zellen korrekt markiert
(z. B. Kriens 2P/4.65–4.79 = 97 % bei 1 Angebot = Preismacht).

**Noch offen (ehrlich):** **Mindestnächte** je Zelle (§5 — echte Vergleichs-Dimension) fehlen, weil
der Free-Kalender-Abruf heute nur `available` behält (nicht `minNights`/Tagespreis). „5+P" bündelt
Grossobjekte/Chalets. Beides als Grenze im UI ausgewiesen; Mindestnächte = nächste Scraper-Anreicherung.

---

## Bau-Reihenfolge (offen)

1. **Scraper-Anreicherung [TEILWEISE]:** per-Monat-Auslastungskurve ✅ (occ je Horizont),
   Horizont/letzter-freier-Tag + **`minNights`** + Tagespreis (Kalender `localPriceFormatted`) je
   Inserat noch **offen** (Free-Kalender behält heute nur `available`) — nötig für die Mindestnächte-
   Spalte im Raster (§5) und die „not_released"-Kategorie (§2, dritte Kategorie). `count=12` für Ski-Peak.
2. **Deal-Cockpit-View [GEBAUT]:** Knappheits-Auslastung ✅ + BFS-entzerrte Jahres-/Peak-Prognose ✅
   (Cockpit-Forecast) + **Wettbewerbs-Raster ✅** (Kundensicht, Preis × Klasse, Lücke/Preismacht —
   siehe „✅ GEBAUT" oben). Offen: empfohlener Preispunkt explizit + Mindestnächte-Spalte (hängt an 1).
3. **Velocity-Kadenz ✅:** tägliche Snapshots → Buchungs-Pace (Pickup-Kachel im Cockpit, gemessen).

Prototyp `_grid.py` (throwaway) hat Raster + 3-Kategorien-Logik + Tagespreis bereits bewiesen.

---

# v0.2 — Adrians Strategie-Rahmen (2026-06-12): Referenz-Profis, Gast-Segmente, Akquise

Erweiterung diktiert nach Live-Abgleich auf Airbnb. Kernidee: nicht den Markt im
Aggregat lesen, sondern die **professionellen Betreiber identifizieren und studieren** —
sie zeigen, was das Geschäft kann. Wichtiger Befund beim Bau: aktuell ist das EINZIGE echte
Profi-Signal die Bewertungs-ANZAHL (reviews_per_month ist Fake = Anzahl/24; Superhost,
Tenure, Host-Portfolio werden NICHT erfasst → brauchen Tiefen-Scrape der Inserat-Seite).

## A. Referenz-Profi-Set je Region (die Benchmark-Basis)
Pro Region 2–3 Top-Betreiber je Grössenklasse finden: 2–3 Studio, 2–3 mit 2 Zi, 2–3 mit 3 Zi,
die es professionell machen. Profi-Kriterien (alle aus Tiefen-Scrape):
- **Tenure** aus den Review-Daten (3–10 Jahre = gesetztes Geschäft; >11 J evtl. Alt-Privat).
- **Stetige Review-Velocity** — ein Profi jagt aktiv Reviews; wer das nicht tut, ist keiner.
- **Superhost / „Guest favorite"-Badge.**
- **Host-Portfolio** (führt er mehrere Wohnungen?).
Diese 6–9 Referenzen sind die Studienobjekte.

## B. Auslastung der Referenzen über die Zeit verfolgen (Velocity)
Wie ausgelastet sind sie diesen/nächsten/übernächsten Monat? 1×/Tag oder alle 2–3 Tage scrapen,
Entwicklung beobachten = echte Buchungs-Pace (= v0.9.101-Snapshot-Velocity, Schritt 6 oben).

## C. Superhost-/Favorit-Zensus (Konkurrenz-Grösse)
Wie viele Superhosts gibt es total in der Region? Alle zusammen → Auslastung im Bezug auf
Superhost/Favorit-Status. Plus Geo-Proof: sind diese Superhosts WIRKLICH in Kriens (Karte),
nicht in Littau — adressiert den Geo-Bleed des 8-km-Radius (Kriens-Suche zog Littau-Inserate).

## D. Gast-Segmente (eine Ebene tiefer — die Nischen-Jagd)
Unterscheiden: Familie · Business/Nomade · Touristen · Paare/Gruppen/Einzel. Erkennbar an
Ausstattung (Tiefen-Scrape Amenities) + Geografie:
- **FAMILIE:** Hotels sind für Familien sehr teuer → Airbnb finanzierbarer. Vermutung: mageres
  Angebot, wenige spezialisiert = **Nische**. Signal: Babybett/Kinderbett/Hochstuhl, ≥2 Schlafz.+Bäder.
  Evtl. auch auf dem Land gut. Frage: wer macht es dort richtig?
- **BUSINESS/NOMADE:** Wohnung mit schnellem Internet, 2 Monitoren, Arbeitsplatz. Geografie:
  Zug, Rotkreuz, Kloten, Zürich — wo grosse Firmen/Forschungszentren sind. Wer macht es richtig?
- **TOURIST:** ÖV-Anbindung ins Zentrum (wie schnell?) ist relevant → führt Richtung Akquise.

## E. Akquise-Kriterien (Adrians Sourcing-Sicht)
Beispiel: 4-Zi-Wohnung in Emmen = attraktiv fürs Airbnb-Business. Gesucht: ein **Block**
(Anonymität), **nahe Bahnhof** (schnell ins Zentrum), **Einkaufsmöglichkeiten** in der Nähe.

## F. Immer die Konkurrenz VERLINKEN
Adrian prüft am Ende eh auf Airbnb gegen → jede Ausgabe mit den echten Inserat-URLs
(`https://www.airbnb.com/rooms/{id}`), damit er direkt klicken und verifizieren kann.

## Scrape-Ausrichtung (was der Tiefen-Scrape je Inserat liefern muss)
Inserat-Seite (PDP, öffentlich, gleicher Key) statt nur Suchseite: superhost · guest_favorite ·
Review-Daten (→ Tenure + echte Velocity) · host_id + host_listing_count (Portfolio) ·
Amenities (→ Gast-Segment-Tags: Babybett→Familie, Arbeitsplatz/2-Monitor/schnelles-WLAN→Business) ·
exakte Koordinaten (Geo-Proof Karte) · Distanz-zum-Bahnhof (Touristen/ÖV). Geo-Radius enger ziehen
(Littau ≠ Kriens). Erst „Profi-Radar" (A+C+F) bauen, dann Segmente (D), dann Akquise-Layer (E).
