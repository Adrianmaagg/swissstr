"""
Fetch BFS HESTA guest origins (table 101) for matched SwissSTR markets.
Output: data/origins-snapshot.json — top-N countries per market by Logiernächte 12m.

Used by the market-detail "Gäste-Mix" strip.
"""
import json, urllib.request, sys, io, itertools
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-1003020000_101/px-x-1003020000_101.px"

mapping = json.loads(Path("../data/market_to_bfs.json").read_text(encoding="utf-8"))
matched = mapping["matched"]
bfs_codes = sorted({e["bfs_code"] for e in matched.values()})

# Indikator codes for table 101: 1=Ankünfte, 2=Logiernächte
# Months: "YYYY" = annual total, else "1".."12"
# Years: pull last two complete years for trend
WANT_YEARS = ["2024", "2025"]
WANT_INDICATOR = "2"  # Logiernächte

# First fetch metadata to know all origin codes
with urllib.request.urlopen(API) as r:
    meta = json.loads(r.read())
herkunft = next(v for v in meta["variables"] if v["code"] == "Herkunftsland")
origin_codes = herkunft["values"]
origin_labels = dict(zip(herkunft["values"], herkunft["valueTexts"]))
print(f"Origins available: {len(origin_codes)} (incl. Total)")

# Pull just Jahrestotal for both years (smaller payload). 71 * 73 * 2 = ~10k cells.
payload = {
    "query": [
        {"code": "Jahr", "selection": {"filter": "item", "values": WANT_YEARS}},
        {"code": "Monat", "selection": {"filter": "item", "values": ["YYYY"]}},
        {"code": "Gemeinde", "selection": {"filter": "item", "values": bfs_codes}},
        {"code": "Herkunftsland", "selection": {"filter": "item", "values": origin_codes}},
        {"code": "Indikator", "selection": {"filter": "item", "values": [WANT_INDICATOR]}},
    ],
    "response": {"format": "json-stat2"},
}

print(f"Requesting {len(WANT_YEARS) * 1 * len(bfs_codes) * len(origin_codes):,} cells...")
req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                              headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=90) as r:
    data = json.loads(r.read())

dim_order = data["id"]
dim_sizes = data["size"]
values = data["value"]
dims = data["dimension"]
dim_codes = {d: list(dims[d]["category"]["index"].keys()) for d in dim_order}

def coords_to_idx(coords):
    idx = 0
    for i, c in enumerate(coords):
        idx = idx * dim_sizes[i] + c
    return idx

code_to_markets = {}
for market_name, m in matched.items():
    code_to_markets.setdefault(m["bfs_code"], []).append(market_name)

# Aggregate: per market, per year, dict {origin_code: nights}
raw = {m: {} for m in matched}
for year_i, month_i, gem_i, ork_i, ind_i in itertools.product(
    range(dim_sizes[0]), range(dim_sizes[1]), range(dim_sizes[2]), range(dim_sizes[3]), range(dim_sizes[4])
):
    flat = coords_to_idx([year_i, month_i, gem_i, ork_i, ind_i])
    v = values[flat]
    if v is None: continue
    yr = dim_codes[dim_order[0]][year_i]
    gem_code = dim_codes[dim_order[2]][gem_i]
    org = dim_codes[dim_order[3]][ork_i]
    if gem_code not in code_to_markets: continue
    for mkt in code_to_markets[gem_code]:
        raw[mkt].setdefault(yr, {})[org] = v

# For each market: pick latest year with data, extract Total + top countries
out = {}
for mkt, by_year in raw.items():
    if not by_year: continue
    # Pick the most recent year with non-empty data
    latest = None
    for y in sorted(by_year.keys(), reverse=True):
        if by_year[y]: latest = y; break
    if not latest: continue
    yd = by_year[latest]
    total = yd.get(origin_codes[0])  # First origin is "Herkunftsland - Total"
    if not total: continue
    # Country breakdown — skip "Total" entry, sort by nights desc
    countries = []
    for ocode, nights in yd.items():
        if ocode == origin_codes[0]: continue
        label = origin_labels[ocode]
        if not nights or label.startswith("Total"): continue
        countries.append({"code": ocode, "label": label, "nights": nights, "share": round(nights / total * 100, 1)})
    countries.sort(key=lambda x: -x["nights"])
    top = countries[:6]
    other_pct = round(100 - sum(c["share"] for c in top), 1)
    out[mkt] = {
        "year": latest,
        "total_nights": total,
        "top_origins": top,
        "other_pct": max(0, other_pct),
    }

snapshot = {
    "_meta": {
        "source": "BFS STAT-TAB px-x-1003020000_101 (HESTA Hotellerie nach Herkunftsland)",
        "source_url": "https://www.pxweb.bfs.admin.ch/pxweb/de/px-x-1003020000_101/",
        "indicator": "Logiernächte",
        "covered_markets": len(out),
    },
    "markets": out,
}
Path("../data/origins-snapshot.json").write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"Saved data/origins-snapshot.json — {len(out)} markets")

# Sanity
for mkt in ["Zermatt", "Lugano", "Zürich"]:
    if mkt in out:
        print(f"\n{mkt} ({out[mkt]['year']}) — top origins:")
        for c in out[mkt]["top_origins"][:5]:
            print(f"  {c['share']:5.1f}%  {c['label']}")
