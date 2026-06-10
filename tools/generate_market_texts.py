#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_market_texts.py — KI-Begruendungs-Texte fuer SwissSTR (offline-Batch)

ROLLE (Daten-First-Grenze, CLAUDE.md):
  Der LLM RECHNET NICHTS. Er erzaehlt nur die Werte, die `marketEconomics`
  und `detectAnomalies`/`whyEdge` in der SPA bereits berechnet haben. Jede Zahl
  im Text muss 1:1 aus den Input-Fakten stammen — keine erfundene Kennzahl,
  keine geschaetzte Prognose. So bleibt die EINE Engine die einzige Rechen-Quelle
  (P1) und der Cube die Rechenwahrheit.

PIPELINE (3 Stufen):
  1) SPA:    window.exportMarketFacts()  ->  Download data/market-facts.json
             (Fakten kommen aus der echten Engine, nicht aus Python nachgerechnet)
  2) HIER:   python tools/generate_market_texts.py  ->  data/market-texts.json
             (Anthropic Batches API, 50% guenstiger, claude-opus-4-8)
  3) SPA:    laedt market-texts.json, zeigt KI-Text in Edge-Ranking/Perlen +
             Such-Strategien — mit ehrlichem "KI-Text aus Engine-Werten"-Label.

KOSTEN / SPEND:
  Der echte Lauf ruft die kostenpflichtige Batches API auf. Pro CLAUDE.md ist
  echte Geldausgabe eine Entscheidung von Adrian — DESHALB:
    * `--dry-run`  baut die Payloads + schaetzt Tokens/Kosten, OHNE API-Call.
    * ohne Flag    erstellt + pollt den Batch (kostet ~50% des Normalpreises).
  Braucht ANTHROPIC_API_KEY im Env (analog BRIGHTDATA_API_KEY).

ABHAENGIGKEIT:  pip install anthropic   (Python 3.8+)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

MODEL = "claude-opus-4-8"
MAX_TOKENS = 700

ROOT = Path(__file__).resolve().parent.parent
FACTS_PATH = ROOT / "data" / "market-facts.json"
OUT_PATH = ROOT / "data" / "market-texts.json"

# Antwort-Schema: zwei knappe de-CH-Texte je Markt, sonst nichts.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "pearl_reason": {
            "type": "string",
            "description": "1-2 Saetze: warum dieser Markt eine R2R-Perle ist (oder warum nicht). Nur aus den Fakten.",
        },
        "strategy_hint": {
            "type": "string",
            "description": "1 Satz: konkrete Such-/Miet-Strategie fuer diesen Markt. Nur aus den Fakten.",
        },
    },
    "required": ["pearl_reason", "strategy_hint"],
    "additionalProperties": False,
}

SYSTEM = """Du bist der Text-Veredler fuer SwissSTR, ein Tool das Schweizer Short-Term-Rental-Maerkte bewertet.

DEINE EINZIGE AUFGABE: aus den vorgegebenen, bereits berechneten Fakten zwei knappe deutsche Texte formulieren. Du bist KEIN Rechner.

HARTE REGELN:
- Verwende AUSSCHLIESSLICH Zahlen, die in den Fakten stehen. Erfinde NIE eine Kennzahl, einen Prozentwert, einen CHF-Betrag oder eine Prognose.
- Fehlt eine Zahl (null), erwaehne sie nicht — tu nicht so als waere sie da.
- Schweizer Stil: CHF mit Apostroph-Tausendern (CHF 12'500), de-CH.
- Knapp, konkret, keine Floskeln, keine Marketing-Sprache, kein "spannend"/"attraktiv" ohne Beleg.
- Ehrlich: wenn die Fakten gegen den Markt sprechen (Cap, ruecklaeufige Nachfrage, Optimismus-Gap), sag es klar.
- pearl_reason: warum diese Perle (oder warum eben nicht) — die Treiber benennen.
- strategy_hint: ein konkreter naechster Schritt (welche Wohnungsgroesse / welcher Hebel), aus den Fakten abgeleitet."""


def build_user_prompt(fact: dict) -> str:
    return (
        "Fakten zu diesem Markt (alle bereits von der Engine berechnet — du rechnest nichts):\n\n"
        + json.dumps(fact, ensure_ascii=False, indent=2)
        + "\n\nFormuliere pearl_reason und strategy_hint nur aus diesen Fakten."
    )


def safe_id(name: str, idx: int) -> str:
    # custom_id: nur a-z0-9_- erlaubt, max 64. Name kann Umlaute/Leerzeichen haben -> Index als Anker.
    slug = "".join(c if c.isalnum() else "-" for c in name.lower())[:48]
    return f"m{idx:03d}-{slug}"


def load_facts() -> list:
    if not FACTS_PATH.exists():
        sys.exit(
            f"FEHLT: {FACTS_PATH}\n"
            "Zuerst in der SPA `window.exportMarketFacts()` in der Browser-Konsole laufen lassen\n"
            "(oder den Dev-Button 'Fakten exportieren') und die heruntergeladene Datei nach data/ legen."
        )
    facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(facts, list) or not facts:
        sys.exit(f"{FACTS_PATH} ist leer oder kein Array.")
    return facts


def estimate(facts: list) -> None:
    # Grobe Schaetzung ohne API-Call (Daten-First: als Schaetzung mit Quelle gekennzeichnet).
    # ~ Zeichen/4 = Tokens (de-Heuristik, leicht konservativ). Nur Groessenordnung.
    sys_tok = len(SYSTEM) // 4
    in_tok = sum((sys_tok + len(build_user_prompt(f)) // 4) for f in facts)
    out_tok = len(facts) * 220  # ~ 2 kurze Saetze
    # Opus 4.8: Input $5 / Output $25 pro 1M. Batches = 50%.
    cost = (in_tok / 1e6 * 5 + out_tok / 1e6 * 25) * 0.5
    print(f"  Maerkte:            {len(facts)}")
    print(f"  ~Input-Tokens:      {in_tok:,}".replace(",", "'"))
    print(f"  ~Output-Tokens:     {out_tok:,}".replace(",", "'"))
    print(f"  ~Kosten (Batches):  ~${cost:.2f}  (Schaetzung, Heuristik Zeichen/4)")


def run_batch(facts: list) -> None:
    try:
        import anthropic
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request
    except ImportError:
        sys.exit("anthropic SDK fehlt:  pip install anthropic")

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        sys.exit("ANTHROPIC_API_KEY nicht gesetzt. Im Env setzen, dann erneut laufen.")

    client = anthropic.Anthropic()

    requests = [
        Request(
            custom_id=safe_id(f["name"], i),
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM,
                output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
                messages=[{"role": "user", "content": build_user_prompt(f)}],
            ),
        )
        for i, f in enumerate(facts)
    ]
    id_to_name = {safe_id(f["name"], i): f["name"] for i, f in enumerate(facts)}

    print(f"Erstelle Batch mit {len(requests)} Anfragen ({MODEL}) …")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch-ID: {batch.id} — Status: {batch.processing_status}")

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        print(f"  … {batch.processing_status} (in Arbeit: {batch.request_counts.processing})")
        time.sleep(30)

    out, errors = {}, 0
    for result in client.messages.batches.results(batch.id):
        name = id_to_name.get(result.custom_id, result.custom_id)
        if result.result.type == "succeeded":
            text = next((b.text for b in result.result.message.content if b.type == "text"), "")
            try:
                out[name] = json.loads(text)
            except json.JSONDecodeError:
                errors += 1
                print(f"  ! {name}: JSON-Parse fehlgeschlagen")
        else:
            errors += 1
            print(f"  ! {name}: {result.result.type}")

    meta = {
        "_meta": {
            "model": MODEL,
            "source": "Anthropic Batches API — KI-Text aus Engine-Werten, keine neuen Zahlen",
            "tier": "MOD",
            "n_markets": len(out),
            "errors": errors,
        }
    }
    OUT_PATH.write_text(
        json.dumps({**meta, **out}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nGeschrieben: {OUT_PATH}  ({len(out)} Maerkte, {errors} Fehler)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Payloads bauen + Kosten schaetzen, KEIN API-Call, keine Geldausgabe.",
    )
    args = ap.parse_args()

    facts = load_facts()
    if args.dry_run:
        print("DRY-RUN — kein API-Call, keine Kosten:")
        estimate(facts)
        # Beispiel-Payload fuer den ersten Markt zeigen (Kontrolle).
        print("\nBeispiel-Prompt (Markt 1):\n" + "-" * 40)
        print(build_user_prompt(facts[0])[:600])
        return
    estimate(facts)
    run_batch(facts)


if __name__ == "__main__":
    main()
