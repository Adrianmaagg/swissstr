#!/usr/bin/env python3
"""Frischt die KI-Texte EINZELNER Maerkte auf (Direkt-API, sofort, ohne Batch).

Sinnvoll nach einem Scrape, wenn nur wenige Maerkte neue Zahlen haben —
ein Voll-Batch (188) waere Verschwendung. Merged in data/market-texts.json.

Aufruf:  py -3.12 tools/refresh_market_texts.py Emmen Kriens Engelberg [--model sonnet]
"""

import argparse
import json
import sys

from generate_market_texts import (  # laedt auch .env
    DEFAULT_MODEL,
    MODELS,
    OUT_PATH,
    OUTPUT_SCHEMA,
    SYSTEM,
    build_user_prompt,
    load_facts,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="+", help="Markt-Namen exakt wie im Export")
    ap.add_argument("--model", choices=sorted(MODELS.keys()), default=DEFAULT_MODEL)
    args = ap.parse_args()

    import anthropic

    facts = {f["name"]: f for f in load_facts()}
    missing = [n for n in args.names if n not in facts]
    if missing:
        print(f"  ! Nicht im Export (kein BFS-Match?): {', '.join(missing)} — uebersprungen")
    todo = [n for n in args.names if n in facts]
    if not todo:
        sys.exit("Kein Markt zu tun.")

    existing = {}
    if OUT_PATH.exists():
        existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))

    client = anthropic.Anthropic()
    model_id = MODELS[args.model]["id"]
    ok = 0
    for n in todo:
        resp = client.messages.create(
            model=model_id,
            max_tokens=700,
            system=SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            messages=[{"role": "user", "content": build_user_prompt(facts[n])}],
        )
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            existing[n] = json.loads(text)
            ok += 1
            print(f"  + {n} aufgefrischt ({model_id})")
        except json.JSONDecodeError:
            print(f"  ! {n}: JSON-Parse fehlgeschlagen — alter Text bleibt")

    if "_meta" in existing:
        existing["_meta"]["refreshed"] = todo
    OUT_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Geschrieben: {OUT_PATH}  ({ok}/{len(todo)} aufgefrischt)")


if __name__ == "__main__":
    main()
