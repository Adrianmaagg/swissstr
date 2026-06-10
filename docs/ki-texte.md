# KI-Begründungs-Texte — Pipeline (Claude API)

Schärft die Perlen-/Such-Strategie-Begründungen (OFFENE_AUFGABEN P2.2 + P2.3) mit
einem LLM — **ohne** die Daten-First-Grenze zu brechen.

## Die Grenze (nicht regredieren)

Der LLM **rechnet nichts**. Er formuliert nur die Werte, die `marketEconomics` und
`detectAnomalies`/`whyEdge` in der SPA bereits berechnet haben, zu einem scharfen
Satz um. Jede Zahl im KI-Text muss 1:1 aus den Engine-Fakten stammen. Damit bleibt
die EINE Engine die einzige Rechen-Quelle (P1) und der Cube die Rechenwahrheit.

KI-Texte sind im UI als **`✨ KI · 🟡 MOD`** markiert (Tooltip: „KI-Text aus
Engine-Werten, keine neuen Zahlen").

## 3 Stufen

1. **Export (SPA → Fakten).** In der Browser-Konsole `exportMarketFacts()` aufrufen
   → lädt `market-facts.json` (188 BFS-Märkte, alle Werte aus der echten Engine).
   Die Datei nach `data/market-facts.json` legen. **Vor jedem Lauf neu exportieren**,
   damit die Fakten zum aktuellen Engine-Stand passen.

2. **Generieren (Claude API).**
   ```
   python tools/generate_market_texts.py --dry-run   # Payloads + Kostenschätzung, KEIN Spend
   python tools/generate_market_texts.py             # echter Batches-Lauf (kostet ~$0.70)
   ```
   Braucht `ANTHROPIC_API_KEY` im Env (analog `BRIGHTDATA_API_KEY`). Nutzt die
   **Batches API** (50% günstiger), `claude-opus-4-8`, strukturierte Ausgabe je Markt
   (`pearl_reason`, `strategy_hint`). Schreibt `data/market-texts.json`.

3. **Anzeige (SPA).** `index.html` lädt `data/market-texts.json` automatisch (graceful:
   fehlt sie, fällt das Edge-Ranking auf die deterministische `whyEdge()`-Begründung
   zurück). Vorhandene KI-Texte ersetzen den Perlen-Satz mit `✨ KI`-Label.

## Warum offline-Batch statt Live-Call

Kein Browser-Live-Call: würde den API-Key auf GitHub Pages öffentlich machen. Das
Muster ist identisch zu allen anderen Daten-Quellen (`tools/fetch_*.py` → `data/*.json`).
Bei 188 Märkten ist Batch günstiger und schnell (<1h).
