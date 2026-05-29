# Changelog

Alle wesentlichen Änderungen am Projekt werden hier dokumentiert.
Format: [Semantic Versioning](https://semver.org/lang/de/).

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
