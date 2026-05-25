"""
Match SwissSTR markets[] names to BFS HESTA Gemeinde names.
Prints matched + unmatched. Manual mapping table written for the unmatched.
"""
import json
import re
import urllib.request
import sys
import io

# Force utf-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PXWEB_META = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-1003020000_201/px-x-1003020000_201.px"

print("Fetching BFS HESTA metadata...")
with urllib.request.urlopen(PXWEB_META) as r:
    meta = json.loads(r.read())

gem_var = next(v for v in meta["variables"] if v["code"] == "Gemeinde")
bfs = dict(zip(gem_var["valueTexts"], gem_var["values"]))
print(f"BFS Gemeinden in HESTA: {len(bfs)}")

with open("../index.html", encoding="utf-8") as f:
    html = f.read()
markets = re.findall(r'name:\s*"([^"]+)"', html)
print(f"SwissSTR markets: {len(markets)}")

# Strategy: exact match, then case-insensitive, then substring (both directions),
# then known manual overrides for Ortsteile -> Gemeinde mergers.
# Manual mapping: SwissSTR market name -> BFS Gemeinde name
# Reasons documented for each non-trivial mapping.
MANUAL = {
    "Verbier": "Val de Bagnes",            # Ortsteil seit 2021 in Fusion
    "Wengen": "Lauterbrunnen",             # Ortsteil
    "Mürren": "Lauterbrunnen",             # Ortsteil
    "Gstaad": "Saanen",                    # Ortsteil
    "Lenzerheide": "Vaz/Obervaz",          # Ortsteil
    "Celerina": "Celerina/Schlarigna",     # offizieller Doppelname
    "Brunnen": "Ingenbohl",                # Ortsteil
    "Brig": "Brig-Glis",                   # offizieller Name seit Fusion
}

# Markets without HESTA coverage (Ortsteile ohne eigene Hotellerie-Erhebung,
# kleine Gemeinden unter Erhebungsschwelle, oder Stadt nicht als Gemeinde gelistet)
NO_BFS = {
    "Glarus",       # nur Glarus Nord/Süd in Liste, Stadt Glarus selbst fehlt
    "Riederalp",    # Ortsteil von Bitsch
    "Bettmeralp",   # Ortsteil von Bitsch
    "Stein am Rhein",
    "Frutigen",
    "Disentis",
    "Sörenberg",    # Ortsteil von Flühli
    "Romanshorn",
    "Altdorf",
}

matched = {}
unmatched = []
fuzzy = []

for m in markets:
    if m in NO_BFS:
        unmatched.append((m, "explicit:no_hesta_coverage"))
        continue
    if m in MANUAL and MANUAL[m] in bfs:
        matched[m] = (MANUAL[m], bfs[MANUAL[m]])
        continue
    if m in bfs:
        matched[m] = (m, bfs[m])
        continue
    hit = next((k for k in bfs if k.lower() == m.lower()), None)
    if hit:
        matched[m] = (hit, bfs[hit])
        continue
    hits = [k for k in bfs if m.lower() in k.lower() or k.lower() in m.lower()]
    if len(hits) == 1:
        matched[m] = (hits[0], bfs[hits[0]])
        fuzzy.append(f"{m} -> {hits[0]}")
        continue
    if len(hits) > 1:
        unmatched.append((m, f"ambiguous:{hits}"))
        continue
    unmatched.append((m, "no_match"))

print(f"\n=== MATCHED: {len(matched)}/{len(markets)} ===")
print(f"\n=== FUZZY ({len(fuzzy)}) ===")
for f in fuzzy: print(" ", f)
print(f"\n=== UNMATCHED ({len(unmatched)}) ===")
for u in unmatched: print(" ", u)

out = {
    "_meta": {
        "source": "BFS HESTA px-x-1003020000_201",
        "fetched": meta.get("updated", "unknown"),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
    },
    "matched": {m: {"bfs_name": v[0], "bfs_code": v[1]} for m, v in matched.items()},
    "unmatched": {m: reason for m, reason in unmatched},
}
with open("../data/market_to_bfs.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\nMapping saved: data/market_to_bfs.json")
