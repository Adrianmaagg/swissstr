# SwissSTR Intelligence

> Short-Term-Rental Analytics & Investor-Tool für die Schweiz. Inspiriert von AirDNA, aber mit echter CH-Tiefe.

🇨🇭 **Live:** [adrianmaagg.github.io/swissstr](https://adrianmaagg.github.io/swissstr/)

## Was es macht

Schweizer Investoren brauchen lokale Daten + Regulierung + ROI in **einem** Tool. AirDNA hat keine CH-Tiefe, das BFS hat Daten aber keine UX. SwissSTR füllt die Lücke:

- **Marktübersicht** mit 81 Schweizer Orten, Karte und Top-Performance-Tabelle
- **Scout** — 6 algorithmische Investment-Strategien (Cashflow-König, Hidden Gem, Familien-Gap, …) mit transparenter Datenherkunft
- **Markt-Detail** pro Ort mit Saisonalität, Gäste-Mix, Konkurrenz-Analyse
- **Investor-Calc** mit ROI-Wasserfall und Sensitivitäts-Matrix
- **Regulierung** — kantonale Tages-Cap-Matrix, Kurtaxe, Zweitwohnungs-Cap, Risiko-Score
- **Datenquellen** — alle Methodiken offengelegt

## Daten-Tiers

Jeder Wert hat einen Badge, damit Investoren wissen was Proof und was Schätzung ist:

| Badge | Bedeutung | Quelle |
|---|---|---|
| 🟢 **BFS** | Verifiziert aus amtlicher Quelle | [BFS STAT-TAB](https://www.pxweb.bfs.admin.ch/) — HESTA Hotellerie |
| 🟡 **MOD** | Modelliert aus echten Inputs | Berechnung dokumentiert |
| 🔴 **MOCK** | Schätzung | Roadmap-Verifikation benannt |

**72 von 81 Märkten** sind BFS-verifiziert (Auslastung, Logiernächte, Saisonalität, Gäste-Mix).

## Architektur

- **Single-File HTML SPA** (`index.html`) — kein Build, kein Framework
- **Vanilla JavaScript** mit Chart.js + Tailwind via CDN
- **GitHub Pages** Auto-Deploy bei jedem Push auf `main`
- **Daten-Snapshots** in `data/*.json`, refresht via Python-Skripte in `tools/`

```
swissstr/
├── index.html              # Komplette Single-File App
├── data/
│   ├── hesta-snapshot.json    # BFS HESTA Tabelle 201 (Angebot/Nachfrage)
│   ├── origins-snapshot.json  # BFS HESTA Tabelle 101 (Herkunftsland)
│   └── market_to_bfs.json     # Mapping Markt-Name ↔ BFS-Gemeinde
├── tools/
│   ├── match_bfs.py        # SwissSTR-Märkte ↔ BFS-Gemeinden mappen
│   ├── fetch_hesta.py      # HESTA-Daten pullen
│   └── fetch_origins.py    # Herkunftsland-Daten pullen
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Daten aktualisieren

Python 3.8+, keine Dependencies:

```bash
cd tools/
python match_bfs.py       # Re-matcht meine Märkte auf BFS-Gemeinden
python fetch_hesta.py     # Pullt HESTA Tabelle 201 (~14k Cells)
python fetch_origins.py   # Pullt HESTA Tabelle 101 (~10k Cells)
```

Die JSON-Snapshots werden committed — das Frontend lädt sie statisch über `fetch()`.

## Roadmap

- [x] Scout-View mit 6 Strategien
- [x] BFS HESTA-Integration für 72/81 Märkte
- [x] Proof-Tier-System (🟢/🟡/🔴 Badges)
- [x] Saisonalitäts-Chart mit echten BFS-Daten
- [x] Gäste-Herkunftsmix
- [ ] **Echte CH-Karte** mit Kantonsgrenzen (TopoJSON statt SVG-Blob)
- [ ] **i18n** DE/FR/IT/EN (Buttons sind aktuell Deko)
- [ ] **500+ Märkte** durch automatisches Mapping aus BFS-Gemeindeliste
- [ ] **PDF-Export** mit jsPDF + html2canvas
- [ ] **Wüest Partner Lizenz** für echte m²-Kaufpreise (BFS hat keinen API-Index)

## Stack

| | |
|---|---|
| Frontend | Vanilla JS, Chart.js 4.4, Tailwind CSS (CDN) |
| Daten | BFS STAT-TAB PxWeb API (json-stat2) |
| Build | Kein — statisches HTML |
| Hosting | GitHub Pages |

## Lizenz

MIT — siehe [LICENSE](LICENSE).
