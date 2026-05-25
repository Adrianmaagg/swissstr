"""
Merge tools/_new_markets.json into js/data.js — appends to markets[] before the closing ];
Preserves existing markets unchanged, just adds new entries.
"""
import json, sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

new_markets = json.loads(Path("_new_markets.json").read_text(encoding="utf-8"))
data_js_path = Path("../js/data.js")
data_js = data_js_path.read_text(encoding="utf-8")

# Format each new market as a JS object on a single line, matching existing style
def fmt(m):
    return ('  { name: {name!r}, canton: {canton!r}, listings: {listings}, '
            'adr: {adr}, occ: {occ}, revpar: {revpar}, grade: {grade!r}, '
            'profile: {profile!r}, peak: {peak!r}, tags: {tags}, cat: {cat!r} },'
           ).format(
        name=m['name'], canton=m['canton'], listings=m['listings'],
        adr=m['adr'], occ=m['occ'], revpar=m['revpar'], grade=m['grade'],
        profile=m['profile'], peak=m['peak'],
        tags=json.dumps(m['tags'], ensure_ascii=False),
        cat=m['cat'],
    ).replace("'", '"').replace('"name":', 'name:')  # JS-style keys
# That's ugly, let's just build it manually
def fmt2(m):
    tags = '[' + ', '.join(json.dumps(t, ensure_ascii=False) for t in m['tags']) + ']'
    return (f'  {{ name: {json.dumps(m["name"], ensure_ascii=False)}, '
            f'canton: "{m["canton"]}", listings: {m["listings"]}, '
            f'adr: {m["adr"]}, occ: {m["occ"]}, revpar: {m["revpar"]}, '
            f'grade: "{m["grade"]}", profile: "{m["profile"]}", '
            f'peak: "{m["peak"]}", tags: {tags}, cat: "{m["cat"]}" }},')

new_lines = ['',
             '  // ====== ADDITIONAL BFS-COVERAGE MARKETS (auto-generated from BFS HESTA Gemeinde list) ======',
             '  // Diese Märkte sind in der BFS HESTA-Statistik gelistet aber waren ursprünglich nicht im',
             '  // markets[]-Array. ADR/occ/revpar sind Heuristiken — die echten Werte werden zur Laufzeit',
             '  // via loadHesta() aus data/hesta-snapshot.json überschrieben sobald gematched.',
            ] + [fmt2(m) for m in new_markets]

# Find the closing ']' of markets array and insert before it
# The closing pattern is exactly `\n];` at top-level after all market entries
pattern = re.compile(r'^\];', re.MULTILINE)
match = pattern.search(data_js)
if not match:
    print("ERROR: Couldn't find closing '];' for markets array")
    sys.exit(1)

insert_pos = match.start()
new_content = data_js[:insert_pos] + '\n'.join(new_lines) + '\n' + data_js[insert_pos:]

data_js_path.write_text(new_content, encoding="utf-8")
print(f"Inserted {len(new_markets)} new markets into js/data.js")
print(f"New file size: {len(new_content)} bytes (was {len(data_js)})")

# Verify by counting
total_markets = len(re.findall(r'name:\s*"[^"]+"', new_content))
print(f"Total markets now: {total_markets}")
