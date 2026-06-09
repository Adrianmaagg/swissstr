# Scraper Contract / Data Acquisition Standard

Stand: 2026-06-09 · v1 · gilt für `tools/fetch_airbnb.py` (BD) und `tools/fetch_airbnb_free.py` (gratis).

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

## Status: vorhanden vs. fehlt (heute)
**Vorhanden** (pro Listing, aktueller Snapshot): `listingId`-Analog (id), `lat`/`long`, `room_type`, `is_entire`, `bedrooms`, `guests`, `rating`, `reviews_count`, `host_id` (nur BD), `occ_method`, `occ_calendar_pct`, `occ_reviews_pct`, `price_usd` (teilw.), `free_7d`/`free_30d` (BD). **Aggregat-Zeitreihe** (`airbnb-trends.json` series): date/occ/adr_chf/adr_n/supply/pro_share.

**Fehlt (Contract umsetzen):** gespeicherte **Scrape-Signatur je Lauf** (query/geo/stayLength/currency/priceMode/listingIds) · per-Listing-**Kalender-Historie** (für Booking-Velocity) · `priceMode`-Kennzeichnung (nightly vs stay-total) · `requestedRadiusKm`/`mapBounds`/`geoFilterMode` · normalisierte Fees/Discounts.

## Nächste Schritte (Pipeline)
1. `fetch_airbnb*.py`: pro Lauf `snapshotSignature` + Geo-/Query-Params in `airbnb-trends.json` (bzw. `history/airbnb/*.jsonl`) schreiben.
2. Geo-Filter (Distanz-Cutoff ≤ requestedRadiusKm) + präzise Query für Geo-Critical-Märkte.
3. Kalender-Snapshots (available/price je checkDate) über 14–30 Tage für die Tracking-Märkte.
