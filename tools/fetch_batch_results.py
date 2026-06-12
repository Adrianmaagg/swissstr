#!/usr/bin/env python3
"""Holt die Ergebnisse eines FERTIGEN Batches ab und schreibt data/market-texts.json.

Nutzen, wenn der Poller in generate_market_texts.py abgebrochen ist — Ergebnisse
liegen 29 Tage bei Anthropic, das Abholen kostet nichts.

Aufruf:  py -3.12 tools/fetch_batch_results.py msgbatch_xxx
"""

import json
import sys

from generate_market_texts import OUT_PATH, load_facts, safe_id  # lädt auch .env


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("msgbatch_"):
        sys.exit("Aufruf: fetch_batch_results.py <msgbatch_id>")
    batch_id = sys.argv[1]

    import anthropic

    client = anthropic.Anthropic()
    batch = client.messages.batches.retrieve(batch_id)
    if batch.processing_status != "ended":
        sys.exit(f"Batch ist noch '{batch.processing_status}' — später erneut.")

    facts = load_facts()
    id_to_name = {safe_id(f["name"], i): f["name"] for i, f in enumerate(facts)}

    out, errors = {}, 0
    for result in client.messages.batches.results(batch_id):
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

    model_id = getattr(batch, "model", None) or "claude-sonnet-4-6"
    meta = {
        "_meta": {
            "model": model_id,
            "batch_id": batch_id,
            "source": "Anthropic Batches API — KI-Text aus Engine-Werten, keine neuen Zahlen",
            "tier": "MOD",
            "n_markets": len(out),
            "errors": errors,
        }
    }
    OUT_PATH.write_text(json.dumps({**meta, **out}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Geschrieben: {OUT_PATH}  ({len(out)} Maerkte, {errors} Fehler)")


if __name__ == "__main__":
    main()
