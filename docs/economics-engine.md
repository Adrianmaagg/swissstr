# Zentrale Rechen-Engine — `js/economics.js`

**Status:** verbindlich ab v0.9.149 · **Modul:** `js/economics.js` (Browser-Global `STREcon`)

## Warum (das Problem, das das löst)

start.html, cockpit.html und index.html rechneten dieselben Geld-Grössen je mit
**eigener lokaler Formel**. Resultat: dieselbe Wohnung ergab je nach Seite andere
Zahlen — Adrian sah „dauernd Unterschiede" (z. B. Brutto-Run-Rate auf der Startseite
vs. Netto im Cockpit, ohne dass die Seite den Zusammenhang zeigt).

Konkreter Auslöser (Baden, Juni 2026): Start zeigte Philipp mit „viel mehr", das
Cockpit mit „~1'000/Jahr" — weil Start **Brutto** aus einem **7-Tage-Fenster** ×30
hochrechnete, das Cockpit **Netto** nach Miete über ein **entsaisonalisiertes Jahr**.
Beide Zahlen einzeln korrekt, aber nirgends verbunden und in zwei getrennten Formeln.

## Regel (hart, nicht regredieren)

> **Jede Markt-/Geld-Mathe läuft über `STREcon`. Keine zweite lokale Formel.**
> Wer eine neue Kennzahl braucht, ergänzt sie hier — nicht in einer einzelnen Seite.

Das ist die konkrete Umsetzung der Projekt-Regel „neue Markt-Mathe IMMER über die
zentrale Engine" (bisher nur für `marketEconomics` in index.html gelebt, jetzt
seitenübergreifend für die Deal-/Geld-Ebene).

## API (rein, kein DOM, kein State)

| Funktion | Liefert |
|---|---|
| `WINDOWS`, `DEFAULT_WINDOW` (`'30'`) | kanonische Belegungs-Fenster (Tage) |
| `DEFAULT_COSTS` | kanonische R2R-Deal-Annahmen (CHF), Fallback wenn kein Cockpit-Override |
| `occAt(listing, H)` | Belegung% am Fenster H |
| `grossMonthly(price, occ)` / `grossAnnual(...)` | 🟡 Brutto-Run-Rate = Preis × Belegung% × 30 / × 365 |
| `gastPerNight(price, costs)` | was der Gast/Nacht zahlt (+ Airbnb-Gebühr + Kurtaxe) |
| `hostPerNight(price, costs)` | was beim Host/Nacht ankommt (− Host-Gebühr − Kurtaxe) — **vor** eigenen Kosten |
| `nightsFor(occ, days)`, `staysFor(nights, stayLen)`, `monthOcc(anchor, idx, cap)` | gerundete Primitive |
| `netMonthly({price, occPct, costs, days})` | volles Geld-Fluss-Objekt: `{revNight, nights, stays, einnahmen, fix, variabel, netto, nettoNacht}` |
| `seasonalIndex(bfs)` | Saison-Form aus BFS-Monatsdaten, auf Jahresschnitt 1.0 normiert |
| `annualForecast({price, anchorOcc, index, months, costs, occCap})` | Monat-für-Monat: `{rows, tInc, tFix, tVar, tNet, tNights, avgOcc}` |
| `annualNet(...)` | nur der Netto-Gesamtwert (Konservativ-Floor) |
| `CANTON_CODE` | Kanton-Name (de/fr/it) → 2-Buchstaben-Code (Join auf `data/mietpreise.json`) |
| `roomsFromBedrooms(bedrooms)` | 🟡 Schlafzi → CH-Zimmerzahl (Schlafzi + 1.5; 3 → 4.5 Zi) |
| `bfsRent(roomsTable, rooms)` / `bfsRentGross(...)` | BFS-Marktmiete netto / brutto (inkl. NK, `BFS_NK_UPLIFT=1.13`) für eine Zimmerzahl, interpoliert |
| `breakevenRent({price, occPct, costs, targetNet})` | 🟡 R2R: bis zu welcher Miete (inkl. NK) trägt das STR — „STR trägt bis CHF X" |
| `rentHeadroomPct(breakeven, marketRent)` | R2R-Spielraum % über Marktmiete (gleiche Basis = beide inkl. NK) |

## R2R-Akquise-Spielraum (v0.9.150-rent)

Aus der Inserat-Zimmerzahl die Wohnungsgrösse ableiten → BFS-Marktmiete (`data/mietpreise.json`,
Nettomiete je Kanton×Zimmer, BFS `je-d-09.03.03.01`, jährlich) → wieviel Miete trägt das STR.
**Der „+20-30%" ist ein ERGEBNIS, kein Input:** `breakevenRent` löst `netMonthly` nach der Miete
auf (= Einnahmen − variabel − Internet − Wasser/Strom), `rentHeadroomPct` setzt das gegen die
BFS-Bruttomiete. Cockpit zeigt den Streifen im Geld-Fluss, wenn ein Inserat gewählt ist und `bedrooms`
trägt. **Tier 🟡:** BFS = Kantonsschnitt (Mikrolage/Resort weicht ab); Zimmer-Heuristik + NK-Aufschlag
sind Annahmen, sichtbar gelabelt. Für die Akquise die Jahresschnitt-Belegung (~30T) nehmen, nicht das
Sommer-Kurzfenster — sonst wird die tragbare Miete überschätzt.

## Geteilter Kosten-Speicher

Die Deal-Annahmen leben in **`localStorage['cockpit_price']`** (vom Cockpit
geschrieben). Beide Seiten mergen sie über `DEFAULT_COSTS`:
`costs = {...STREcon.DEFAULT_COSTS, ...JSON.parse(localStorage.cockpit_price||'{}')}`.
→ Stellt Adrian im Cockpit Miete/Reinigung/Belegung ein, rechnet die Startseite mit
**denselben** Annahmen. Kein Cockpit-Besuch nötig → Defaults.

## Wer nutzt was

- **start.html** — `occAt`, `grossMonthly/Annual` (Spitzenverdiener + ≥40k-Kohorte, Brutto),
  **neu** `netMonthly` (zeigt „was bleibt netto" je Spitzenverdiener, mit Cockpit-Annahmen).
- **cockpit.html** — `gastPerNight`, `hostPerNight`, `grossMonthly` (Umsatz-Chart),
  `netMonthly` (Geld-Fluss), `seasonalIndex` + `annualForecast` (Jahres-Prognose).
- **index.html** — Tier-/NOI-Engine (`marketEconomics`/`strUnitEconomics`, %-Kostenmodell für
  den Markt-Schnitt) bleibt eigenständig; sie beantwortet eine andere Frage (Markt-NOI eines
  repräsentativen Operators, nicht ein konkreter R2R-Deal). Überlappende Primitive
  (Brutto, Host-pro-Nacht) dürfen später auf `STREcon` umgestellt werden.

## Abnahme (was „stimmt" heisst)

1. **Verhaltensgleich:** Cockpit zeigt nach der Umstellung **dieselben** Zahlen wie vorher
   (Geld-Fluss, Jahres-Prognose). Referenz Baden/Philipp @50%: host/N 176, 15 N, Netto/Mt 250.
2. **Reconciliation:** Wählt man auf start.html und im Cockpit dasselbe Inserat + dieselbe
   Belegung, ist die **Netto/Mt-Zahl identisch** (gleiche Engine, gleicher Kosten-Speicher).
3. **Eine Formel:** `grep` nach `price_chf*.*occ.*30` o. ä. findet die Run-Rate **nur** im Modul,
   nicht mehr in start/cockpit. Gleiches für `*(1-...hostFee...)`.
4. **node --check js/economics.js** grün; Browser-Verify beider Seiten ohne Konsolenfehler.
