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

## Bau-Reihenfolge (offen)

1. **Scraper-Anreicherung:** per-Monat-Auslastungskurve + `minNights` + Tagespreis (Kalender
   `localPriceFormatted`) + Horizont/letzter-freier-Tag je Inserat SPEICHERN (wird aktuell
   verworfen). `count=12` für Ski-Peak. Ratings für Sweep-Inserate nachreichern.
2. **Deal-Cockpit-View** (ein Markt + Zielmonat): Knappheits-Auslastung, BFS-entzerrte
   Jahres-/Peak-Prognose, Wettbewerbs-Raster mit empfohlenem Preispunkt.
3. **Velocity-Kadenz:** tägliche Mini-Scrapes der Watchlist-Märkte → Buchungs-Pace.

Prototyp `_grid.py` (throwaway) hat Raster + 3-Kategorien-Logik + Tagespreis bereits bewiesen.
