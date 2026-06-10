# Auslastungs-Methodik — warum wir eine Spanne zeigen, keinen Punktwert

> Quelle: Deep-Research 2026-06-10 (5 Such-Winkel, 17 Quellen, 21 Claims adversarial
> verifiziert / 4 gekillt). Kernbefunde unten mit Primärquellen.

## Der harte Befund: echte Belegung ist strukturell nicht beobachtbar

Es gibt **keine** Methode, aus öffentlichen Airbnb-Daten die echte Belegung direkt
zu messen. Seit Airbnbs Website-Umbau **2014** verschmelzen „gebucht" und
„host-blockiert / Eigenbelegung" in eine **einzige** „nicht verfügbar"-Kategorie.
Booked-vs-Blocked kann daher nur **inferiert**, nie gemessen werden (3-0 verifiziert):

- Housing Studies 2023: *„the site merged booked days into the unavailable category … it is still not possible to distinguish true bookings from days properties are otherwise unavailable."* (tandfonline 10.1080/02673037.2023.2176829)
- Inside Airbnb: *„The Airbnb calendar for a listing does not differentiate between a booked night vs an unavailable night."*
- PLOS ONE 2024: *„we cannot distinguish actual bookings … This likely results in some overestimation of occupancies."*

Es gibt **keine Ground Truth** — Airbnb veröffentlicht echte Belegung nirgends.
Jede Auslastungszahl ist bestenfalls eine Range mit ehrlichem Konfidenz-Tag.

Das unterscheidet das Kalender-Problem fundamental vom Geo-Bleed: Geo-Bleed war ein
*Defekt* (an der Quelle reparierbar → Map-Bounds). Belegung ist *prinzipiell
unbeobachtbar*. Die ehrliche Lösung ist nicht „die Wahrheit finden", sondern „die
Wahrheit einklammern".

## Unsere Lösung: zwei gegenläufig verzerrte Schätzer als Spanne

Die beiden praktikablen Methoden verzerren in **entgegengesetzte** Richtungen — das
macht sie als gegenseitige Ober-/Untergrenze nutzbar:

| Schätzer | Verzerrung | Rolle |
|---|---|---|
| **Kalender-Verfügbarkeit** (occ_calendar_pct) | **Überschätzt** — Host-Blocks zählen als gebucht | **Obergrenze** |
| **Review-Proxy** (occ_reviews_pct) | **Unterschätzt** — nicht jeder bewertet + Min-Nächte-Floor | **Untergrenze** |

→ `occupancyBand(m)` liefert `{lower, upper, mid, widthPp}`. Die echte Belegung liegt
im Band; die **Breite IST die Unsicherheit**. Schmales Band (beide Methoden einig) =
glaubwürdig; breites Band = Booked-vs-Blocked-Ambiguität schlägt durch. Das speist
`calculateCalendarIntegrity` (Band-Übereinstimmung statt roher Kalender-Quote).

**Beispiele (live):** Zug 28–47% (Δ19pp), Aarau 31–48%, Gstaad 24–44%. Zürich
(Free-Scrape, kein Kalender) nur Untergrenze 32% — „gebucht-vs-blockiert offen".

## Ehrlichkeits-Deckel (analog „nie decision_grade")

Ein **einzelner** Kalender-Snapshot ist nur eine Obergrenze, kein scharfes Signal →
`calculateCalendarIntegrity` deckelt ihn auf **max 78** (nie „stark" ≥80). Das alte
Label „Kalender (scharf)" war eine Überzeichnung und wurde zu **„Kalender-Verfügbarkeit
(Obergrenze)"** korrigiert (gleiche Klasse Lüge wie der host-blinde Profi-0%, v0.9.99).

## Was „scharf" wäre — die strukturelle Quell-Lösung (v-next)

Echte Belegung approximiert man nur über **Snapshot-Velocity**: denselben 365-Tage-
Vorschaukalender **wiederholt über Zeit** ziehen und available→unavailable-Übergänge
zählen (PLOS ONE 2024). Anforderungen:

- **Scrape-Frequenz ist entscheidend:** täglich fängt Stornos/Kurzaufenthalte;
  vierzehntägig verfehlt >50% der stornierten Tage (PLOS ONE Table 4, COVID-Fenster).
- **Per-Listing-Kalender-Historie** speichern (fehlt heute — siehe `scraper-contract.md`
  §6). Langfristig blockierte Tage (weit in der Zukunft) ≈ Host-Block, kurzfristige
  Übergänge ≈ Buchung → so trennt man die zwei näherungsweise.
- Selbst dann bleibt es Inferenz → **max „testbar", nie decision_grade**, immer gegen
  die Review-Untergrenze + BFS gespiegelt.

Kommerzielle Anbieter (AirDNA) lösen es per proprietärem ML über „16 Buchungssignale" —
aber selbstberichtet, **nicht unabhängig auditiert** (berichtete 15–30% Fehler), und
ist bei uns kostenseitig raus.

## Recht (Kontext, keine Beratung)

Logged-off Scraping öffentlicher Airbnb-Daten verstößt nicht gegen den CFAA
(hiQ v. LinkedIn 9th Cir.; Meta v. Bright Data, N.D. Cal., 23.01.2024 — ToS binden nur
eingeloggte User). **ABER:** „kein CFAA-Verstoß" ≠ „rechtlich sicher" — Vertrags-/ToS-
und Tort-Haftung bleiben separat (hiQ verlor genau darauf $500K). Bright Data als Vendor
trägt die operative Scrape-Posture; die Methodik hier ist quellenneutral.
