# Cockpit-Snapshots — die unwiederbringliche Zeitreihe

Hier liegt der **wertvollste Datenbestand des Projekts**: pro Tag, pro Gemeinde, pro Inserat
der öffentliche Airbnb-Verfügbarkeits-Kalender, wie er an genau diesem Tag aussah.

## Warum committet (nicht gitignored wie `data/raw/`)

| | `data/raw/` (Roh-Scrapes) | `data/snapshots/` (hier) |
|---|---|---|
| Regenerierbar? | **Ja** — neu scrapen geht jederzeit | **Nein** — ein vergangener Tag ist für immer weg |
| Wert | Zwischenprodukt | **historische Wahrheit** |
| Folge | gitignored, lokal wegwerfbar | **committet, off-machine in GitHub, versioniert** |

Der Kalender vom 13. Juni lässt sich am 20. Juni **nie mehr** holen. Darum wird dieser Ordner
bewusst ins Repo committet — das ist die Versicherung, dass die Daten bestehen bleiben.

## Struktur

```
data/snapshots/<gemeinde>/<YYYY-MM-DD>.json
```

Append-only: jeder Tageslauf legt **eine neue Datei** an, nichts wird überschrieben. Pro Datei:

```json
{
  "market": "Kriens", "date": "2026-06-13",
  "center": { "lat": 47.034, "lon": 8.279 },
  "n": 26,
  "listings": [
    { "id": "...", "price_chf": 212, "n_days": 183,
      "window": ["2026-06-01", "2026-11-30"],
      "booked": ["2026-06-01", "2026-06-02", "..."] }   // an diesem Tag nicht-verfügbare Daten
  ]
}
```

`booked` = das Gold. Aus `booked` lässt sich jede Auslastung rekonstruieren — und der **Diff
zweier Tage** zeigt die echten Buchungen.

## Wozu (die ganze Idee)

- **Pickup-Kurve:** ein Datum, das von „frei" auf „weg" springt = eine reale Buchung. Über Tage
  beobachtet sehen wir, *wie schnell* sich ein Datum füllt, je näher es rückt → trennt
  „Vorlaufzeit" von „Nebensaison" (heute nicht trennbar).
- **r = Airbnb ÷ Hotel über Zeit:** die gemessene STR-Saison gegen das BFS-Hotel-Rückgrat.
- **Gebucht vs. host-geblockt:** ein Block, der monatelang unverändert steht, ist Eigennutzung;
  ein Tag, der kurz vor Ankunft kippt, ist eine Buchung.

## Durabilität

- **Committet + gepusht** = liegt off-machine in GitHub, versioniert. Der tägliche Lauf
  committet + pusht den neuen Snapshot automatisch (siehe `tools/` Daily-Runner).
- Grösse ist unkritisch: ~30 KB/Tag/Gemeinde → ~11 MB/Jahr/Gemeinde.
- **Retention-Policy:** Roh-Snapshots bleiben dauerhaft (klein + unwiederbringlich). Erst falls
  das Repo je sehr gross wird, alte Snapshots zu Monats-Aggregaten eindampfen — nie löschen.

## Was haben wir? (Coverage prüfen)

```
py -3.12 tools/snapshot_status.py
```

Zeigt pro Gemeinde: erster/letzter Tag, Anzahl Tage, **Lücken** (verpasste Tage), belegte
Kalendertage gesamt.
