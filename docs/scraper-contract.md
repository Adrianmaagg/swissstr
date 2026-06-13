# Scraper Contract / Data Acquisition Standard

Stand: 2026-06-13 · v2 · gilt für `tools/fetch_airbnb.py` (BD) und `tools/fetch_airbnb_free.py` (gratis).

## Grundsatz

> Kein Snapshot ohne Signatur. Kein Vergleich ohne gleiche Parameter. Kein Trust ohne reproduzierbaren Scrape.

Der Evidence Cube kann nur dann Platform-Drift sauber von Parameter-Drift trennen, wenn jeder Scrape-Lauf seine **Signatur** mitspeichert. Ohne Signatur ist ein ADR-Sprung von 163→280 nicht interpretierbar (anderer Markt? anderer Radius? andere Aufenthaltsdauer? echte Plattform-Änderung?).

## A) Pflichtfelder pro Scrape-Lauf

### 1. Query-Kontext
`market` · `canonicalMarketName` · `queryString` · `timestamp` (ISO) · `scraperMode` (bd_discover / bd_fetch / free_search) · `sourceMode` (calendar / reviews / mixed) · `checkIn` · `checkOut` · `stayLength` (Nächte) · `guests` · `bedrooms` · `roomType` · `propertyType` · `currency` · `locale` · `country`

### 2. Geo-Kontext
`marketCenterLat` · `marketCenterLng` · `requestedRadiusKm` · `mapBounds` (sw/ne) · `polygon`/`gemeindegrenze` (falls verfügbar) · `searchThisAreaUsed` (bool) · `geoFilterMode` (radius / bounding_box / polygon / airbnb_default / unknown)

### 3. Result-Kontext
`resultCount` · `listingIds[]` · `listingLatLng[]` · `distanceToMarketCenter[]` · `inMarketShare` · `outsideMarketShare` · `medianDistanceKm` · `maxDistanceKm` · `boundingBoxOfResults` · `geoBleedLevel`

### 4. Preis-Kontext
`priceRaw` · `priceCurrency` · `priceMode` (nightly / stay_total / unknown) · `cleaningFee` · `serviceFee` · `taxes` · `discounts` · `normalizedNightlyPrice` · `adrMedian` · `adrIQR`

### 5. Kalender-Kontext
`availabilityCalendar` · `availableNights` · `unavailableNights` · `calendarWindowDays` · `occMethod` (calendar / reviews / mixed / unknown) · `calendarSnapshotDate` · `calendarFreshness`

### 6. Listing-Kontext (pro Inserat)
`listingId` · `hostId` · `title` · `roomType` · `propertyType` · `isEntireHome` · `bedrooms` · `beds` · `rating` · `reviewsCount` · `superhost` · `coordinates`

### 7. Snapshot-Signatur (`snapshotSignature`)
Stabiler Hash/Objekt pro Lauf aus: `market` · `timestamp` · query-params · geo-params · `resultCount` · `medianDistanceKm` · `inMarketShare` · `adrMedian` · `entireHomeShare` · `calendarShare` · `hash(sorted listingIds)`.

## B) Vergleichbarkeit (`compareScrapeSignatures(prev, cur)`)
Zwei Snapshots sind nur vergleichbar, wenn **Query, Geo-Parameter, StayLength, Currency, PriceMode, RoomType** gleich sind. Output: `{ comparable, comparabilityScore 0–100, driftReasons[], blockingDifferences[] }`. **Unterschiedliche Parameter sind blockierend** (z.B. 7N vs 30N).

## C) Platform-Drift nur bei vergleichbaren Scrapes
1. Erst `compareScrapeSignatures`. 2. Nur wenn `comparable` → Platform-Drift bewerten. 3. Wenn nicht vergleichbar → Platform-Drift = `unbekannt`, Evidence-Warnung „Snapshots nicht vergleichbar", Strategy-Brief „Parameter vereinheitlichen".

## D) Listing-Overlap (`calculateListingOverlap(prev, cur)`)
`{ overlapCount, overlapShare, newListings, missingListings, stableListings }`. **Regel:** tiefer Overlap bei gleichem Markt+Parametern → Platform-Drift/Geo-Bleed-Verdacht ↑, Source Reliability ↓, Brief „Query/Radien prüfen".

## E) Geo-saubere Scraper-Priorität (für Geo-Critical-Märkte)
Marktzentrum festlegen · Radius begrenzen · Resultate nach Distanz filtern · Gemeindegrenze/Polygon wenn möglich · **Query bei Namenskollision präzisieren**:
- `Grenchen, Solothurn, Switzerland`
- `Genève, Switzerland` (NICHT Geneva/USA)
- `Wädenswil, Zürich, Switzerland`

## F) Calendar-Tracking-Datenmodell (vorbereitet, noch keine Engine)
Pro Listing × Snapshot × Check-Datum: `listingId` · `snapshotDate` · `checkDate` · `available` (bool) · `priceForDate` · `minimumStay` · `currency` · `capturedAt`. Über 14–30 Tage sichtbar machen: welche Nächte frei→belegt kippen · dauerhaft blockierte Nächte · dynamische Preisanpassung · professionelle Kalenderpflege.

## G) Discovery MUSS mehrere Zukunfts-Fenster scannen (Vollständigkeit der Wettbewerbsmenge) — VERBINDLICH

**Warum (zentrale Fehlerquelle):** Die Airbnb-Suche zeigt NUR Inserate, die für die angefragten Check-in/Check-out-Daten FREI sind. Ein einziges Suchfenster findet darum nur die dann verfügbaren Inserate — und übersieht systematisch die **stärksten**: beliebte, oft ausgebuchte Inserate (Guest Favorites, hohe Review-Zahl) sind im Nah-Fenster bereits gebucht und damit unsichtbar. Folge: der Datensatz ist **verzerrt zugunsten immer-freier (oft schwächerer/neuerer) Inserate**, der Wettbewerb wird falsch eingeschätzt, Auslastung/Preis-Median sind biased.

> **Belegter Fall (2026-06-13):** „Sunny apartment near Lucerne" (Ebikon, Host Monique, 151 Bewertungen, Guest Favorite, 5.0, 10 J Hosting) fehlte komplett in unserem Ebikon-Scrape — weil das einzige Suchfenster (heute +42…+49 Tage) eine Woche traf, in der sie ausgebucht war. Genau die Art Inserat, die wir am meisten sehen wollen, war unsichtbar.

**Adrians Verfahren (der Standard, ab jetzt verbindlich):** In die Zukunft gehen und über **mehrere Fenster** schauen, wer alles da ist — nicht einen Punkt. (Adrian: „erst ~3 Monate ab heute, dann z.B. den ganzen November".)

**Regel:** Discovery scannt MEHRERE Zukunfts-Fenster und **vereinigt** die gefundenen `listingId`s. Default-Fenster (Check-in-Offset ab heute; **kurzer Probe-Aufenthalt 2–3 Nächte** für maximale Verfügbarkeits-Oberfläche — ein 7-Nächte-Block passt seltener als 2–3 Nächte, zeigt also weniger Inserate):
- **~21 Tage** (Nah / Last-Minute-only-Inserate)
- **~45 Tage**
- **~90 Tage** (= „3 Monate ab heute")
- **~150 Tage** (= „etwa November")

Pro Fenster die Geo-saubere Suche (Abschnitt E) laufen lassen, Resultate per `listingId` unionen (Review-/PDP-Felder mergen, wenn in einem Fenster reicher). Erst auf der VEREINIGTEN Menge folgen Kalender + Geo + Preis.

**Trennung Discovery ↔ Messung (wichtig):** Die Mehr-Fenster-Suche dient NUR der Vollständigkeit (*wer existiert*). Die **Belegung** kommt weiterhin aus dem per-Listing-Kalender (Abschnitt F, fensterunabhängig); die **Preis-Vergleichbarkeit** weiter aus EINEM Referenz-Fenster (Abschnitt B) — nicht aus dem Discovery-Mix.

**Abnahme-Kriterium (prüfbar, nicht optional):** Eine manuelle Top-Performer-Stichprobe des Marktes (auf Airbnb: Guest Favorites / 100+ Bewertungen) MUSS in der Discovery-Union auftauchen. Fehlt ein solches Inserat → Discovery unvollständig → Fenster erweitern. Der Scrape-Lauf protokolliert `discoveryWindows[]` (die genutzten Offsets) in der Snapshot-Signatur, damit nachvollziehbar ist, welche Fenster abgedeckt wurden.

## Status: vorhanden vs. fehlt (heute)
**Vorhanden** (pro Listing, aktueller Snapshot): `listingId`-Analog (id), `lat`/`long`, `room_type`, `is_entire`, `bedrooms`, `guests`, `rating`, `reviews_count`, `host_id` (nur BD), `occ_method`, `occ_calendar_pct`, `occ_reviews_pct`, `price_usd` (teilw.), `free_7d`/`free_30d` (BD). **Aggregat-Zeitreihe** (`airbnb-trends.json` series): date/occ/adr_chf/adr_n/supply/pro_share.

**Fehlt (Contract umsetzen):** gespeicherte **Scrape-Signatur je Lauf** (query/geo/stayLength/currency/priceMode/listingIds) · per-Listing-**Kalender-Historie** (für Booking-Velocity) · `priceMode`-Kennzeichnung (nightly vs stay-total) · `requestedRadiusKm`/`mapBounds`/`geoFilterMode` · normalisierte Fees/Discounts.

## Nächste Schritte (Pipeline)
1. **[OFFEN, Priorität] Abschnitt G umsetzen:** `fetch_airbnb_free.py run()` — die einzelne `ci`/`co` (heute hart `+42/+49`) durch eine **Schleife über die Discovery-Fenster** ersetzen, `listingId`s unionen, dann erst Kalender/Geo/Preis. `discoveryWindows[]` in die Signatur schreiben. Abnahme: Ebikon re-scrapen → Moniques Inserat (rooms-ID via Airbnb) MUSS auftauchen.
2. `fetch_airbnb*.py`: pro Lauf `snapshotSignature` + Geo-/Query-Params in `airbnb-trends.json` (bzw. `history/airbnb/*.jsonl`) schreiben.
3. Geo-Filter (Distanz-Cutoff ≤ requestedRadiusKm) + präzise Query für Geo-Critical-Märkte.
4. Kalender-Snapshots (available/price je checkDate) über 14–30 Tage für die Tracking-Märkte.
