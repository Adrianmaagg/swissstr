# SwissSTR Intelligence

> Daten-First Short-Term-Rental Analytics für die Schweiz — gebaut für **Rent-to-Rent** (Wohnung mieten, als STR weitervermieten). Jede Zahl trägt, wie belastbar sie ist.

🇨🇭 **Live:** [swissstr.pages.dev/start.html](https://swissstr.pages.dev/start.html) (Cloudflare Pages, zugangsbeschränkt) · lokal: `swissstr.cmd` → http://127.0.0.1:8766/start.html

> **📍 Aktueller Projektstand: siehe [STATUS.md](STATUS.md)** — die eine verbindliche Wahrheit über Architektur, Live-Seiten, Engines, Datenlage und geltende Regeln. Bei Widerspruch gilt STATUS.md, nicht dieses README.

## Was es macht

Beantwortet drei Fragen für den STR-Betreiber: **Wo lohnt es sich? Wie belastbar sind die Zahlen? Welchen Eigentümer spreche ich an?**

Der Arbeitsfluss (Live-Rückgrat):

- **start.html** — Cockpit-Karte: wer verdient je Gemeinde am meisten
- **cockpit.html** — Markt-Tiefe: Wettbewerb, Geldrechnung, Belastbarkeits-Note
- **netzwerk.html** — die grossen Betreiber und ihr Playbook (wie machen sie es)
- **akquise.html** — Deal-Dossier + Eigentümer-Anschreiben

Plus Werkzeuge: `hotel.html` (BFS-Hotellerie-Baseline), `regulierung.html` (kantonale Caps/Kurtaxe), `briefing.html` (Tages-Signale), `datenqualitaet.html` (Vertrauens-Schicht), `investor.html` (Kauf-ROI-Rechner).

## Daten-Tiers

Jeder Wert trägt einen Badge, damit klar ist was Proof und was Schätzung ist:

| Badge | Bedeutung | Quelle |
|---|---|---|
| 🟢 **BFS** | Verifiziert aus amtlicher Quelle | [BFS STAT-TAB](https://www.pxweb.bfs.admin.ch/) — HESTA Hotellerie |
| 🟡 **MOD** | Modelliert aus echten Inputs | Berechnung dokumentiert |
| 🔴 **MOCK** | Schätzung | mit Range + Konfidenz + benannter Quelle |

**188 Märkte** sind BFS-verifiziert (Auslastung, Logiernächte, Saisonalität, Gäste-Mix). Tägliche Airbnb-Tiefe für ~28 Fokus-Märkte (Cloud-Scrape).

## Architektur

- **Browser-only, kein Build** — mehrere eigenständige HTML-Seiten, Vanilla JS, Chart.js + Tailwind via CDN
- **Zentrale Geld-Engine** `js/economics.js` (`STREcon`) — einzige Quelle für Brutto/Netto/Belegung/Breakeven
- **Daten-Snapshots** in `data/*.json`, refresht via Python in `tools/` und `.github/workflows/daily-scrape.yml`
- **Deploy** GitHub Pages + Cloudflare Pages bei Push auf `main`

> Hinweis: `index.html` ist die **Legacy-Vollversion** (alte Engine) und wird nicht mehr weitergebaut — der Einstieg ist `start.html`. Details in [STATUS.md](STATUS.md).

## Lokal starten

```bash
swissstr.cmd     # startet einen statischen Server → http://127.0.0.1:8766/start.html
```

## Daten aktualisieren

Python 3.8+. Die JSON-Snapshots werden committed; das Frontend lädt sie statisch über `fetch()`. Pipeline-Details und Methodik in [`docs/`](docs/) (`scraper-contract.md`, `pricing-cockpit-methodik.md`, `economics-engine.md`, `auslastung-methodik.md`).

## Lizenz

MIT — siehe [LICENSE](LICENSE).
