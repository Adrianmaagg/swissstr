"""
Fetch BFS HESTA hotel statistics (table 201) for matched SwissSTR markets.
Pulls: Betten (supply), Logiernächte (nights), Bettenauslastung in % (occupancy),
       Ankünfte (arrivals) — for years 2024, 2025, 2026 — Jahrestotal + monthly.

Output: data/hesta-snapshot.json keyed by SwissSTR market name.
"""
import json
import urllib.request
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-1003020000_201/px-x-1003020000_201.px"

mapping_path = Path("../data/market_to_bfs.json")
mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
matched = mapping["matched"]
print(f"Matched markets: {len(matched)}")

bfs_codes = sorted({entry["bfs_code"] for entry in matched.values()})
print(f"Unique BFS codes: {len(bfs_codes)}")

# Indicator codes are 1-based per PxWeb metadata:
# 1=Betriebe, 2=Zimmer, 3=Betten, 4=Ankünfte, 5=Logiernächte,
# 6=Zimmernächte, 7=Zimmerauslastung in %, 8=Bettenauslastung in %
WANT_INDICATORS = {
    "1": "betriebe",
    "3": "betten",
    "4": "ankuenfte",
    "5": "logiernaechte",
    "8": "bettenauslastung_pct",
}

WANT_YEARS = ["2024", "2025", "2026"]

# Monat codes: "YYYY"=Jahrestotal, "1".."12"=Jan..Dez
WANT_MONTHS = ["YYYY"] + [str(i) for i in range(1, 13)]

payload = {
    "query": [
        {"code": "Jahr", "selection": {"filter": "item", "values": WANT_YEARS}},
        {"code": "Monat", "selection": {"filter": "item", "values": WANT_MONTHS}},
        {"code": "Gemeinde", "selection": {"filter": "item", "values": bfs_codes}},
        {"code": "Indikator", "selection": {"filter": "item", "values": list(WANT_INDICATORS.keys())}},
    ],
    "response": {"format": "json-stat2"},
}

cells = len(WANT_YEARS) * len(WANT_MONTHS) * len(bfs_codes) * len(WANT_INDICATORS)
print(f"Requesting {cells:,} cells from PxWeb...")

req = urllib.request.Request(
    API,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "Accept": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read())

print(f"Got response. Dimensions: {list(data.get('dimension', {}).keys())}")

# Decode JSON-stat 2 structure: dimensions in fixed order, value array flat.
dims = data["dimension"]
dim_order = data["id"]
dim_sizes = data["size"]
values = data["value"]

# Build coordinate -> value map
def coords_to_idx(coords):
    idx = 0
    for i, c in enumerate(coords):
        idx = idx * dim_sizes[i] + c
    return idx

# Build label maps (code -> label) for each dimension
dim_codes = {}
dim_labels = {}
for d in dim_order:
    cat = dims[d]["category"]
    dim_codes[d] = list(cat["index"].keys())  # ordered by index
    dim_labels[d] = cat.get("label", {})

# Reverse-lookup: BFS code -> SwissSTR market name(s)
code_to_markets = {}
for market_name, m in matched.items():
    code_to_markets.setdefault(m["bfs_code"], []).append(market_name)

# Iterate every cell, group by market
snapshot = {}
for market_name in matched:
    snapshot[market_name] = {
        "bfs_name": matched[market_name]["bfs_name"],
        "bfs_code": matched[market_name]["bfs_code"],
        "series": {},  # key: "YYYY-MM" or "YYYY", value: {indicator: number}
    }

# Loop indices for compact iteration
import itertools
for year_i, month_i, gem_i, ind_i in itertools.product(
    range(dim_sizes[0]), range(dim_sizes[1]), range(dim_sizes[2]), range(dim_sizes[3])
):
    flat = coords_to_idx([year_i, month_i, gem_i, ind_i])
    v = values[flat]
    if v is None:
        continue
    year_code = dim_codes[dim_order[0]][year_i]
    month_code = dim_codes[dim_order[1]][month_i]
    gem_code = dim_codes[dim_order[2]][gem_i]
    ind_code = dim_codes[dim_order[3]][ind_i]
    if gem_code not in code_to_markets:
        continue
    period = year_code if month_code == "YYYY" else f"{year_code}-{int(month_code):02d}"
    ind_key = WANT_INDICATORS[ind_code]
    for mkt in code_to_markets[gem_code]:
        snapshot[mkt]["series"].setdefault(period, {})[ind_key] = v

# Sort series chronologically
for mkt in snapshot:
    snapshot[mkt]["series"] = dict(sorted(snapshot[mkt]["series"].items()))

# Compute summary metrics per market for quick consumption by the frontend
def summary_for(series):
    """Return latest-12-month aggregates: avg occupancy %, total nights, total beds (avg), arrivals."""
    monthly = {k: v for k, v in series.items() if "-" in k}
    if not monthly:
        return None
    latest = sorted(monthly.keys())[-12:]
    occ_vals = [monthly[k].get("bettenauslastung_pct") for k in latest if monthly[k].get("bettenauslastung_pct") is not None]
    nights_total = sum(monthly[k].get("logiernaechte", 0) or 0 for k in latest)
    arrivals_total = sum(monthly[k].get("ankuenfte", 0) or 0 for k in latest)
    betten_vals = [monthly[k].get("betten") for k in latest if monthly[k].get("betten") is not None]
    betriebe_vals = [monthly[k].get("betriebe") for k in latest if monthly[k].get("betriebe") is not None]
    return {
        "period_start": latest[0],
        "period_end": latest[-1],
        "avg_occupancy_pct": round(sum(occ_vals) / len(occ_vals), 1) if occ_vals else None,
        "total_nights_12m": nights_total or None,
        "total_arrivals_12m": arrivals_total or None,
        "avg_beds": round(sum(betten_vals) / len(betten_vals)) if betten_vals else None,
        "avg_betriebe": round(sum(betriebe_vals) / len(betriebe_vals)) if betriebe_vals else None,
    }

for mkt, entry in snapshot.items():
    entry["summary_12m"] = summary_for(entry["series"])

# Build seasonality vector (Jan..Dec) from latest complete year if possible
def seasonality_vector(series):
    monthly = {k: v for k, v in series.items() if "-" in k and v.get("logiernaechte") is not None}
    if not monthly:
        return None
    by_year = {}
    for k, v in monthly.items():
        y, m = k.split("-")
        by_year.setdefault(y, {})[int(m)] = v["logiernaechte"]
    # pick the latest year with at least 12 months
    for y in sorted(by_year.keys(), reverse=True):
        if len(by_year[y]) >= 12:
            months = [by_year[y].get(i, 0) for i in range(1, 13)]
            total = sum(months) or 1
            return {"year": y, "monthly_share": [round(m / total * 12, 3) for m in months]}
    return None

for mkt, entry in snapshot.items():
    entry["seasonality"] = seasonality_vector(entry["series"])

# Add unmatched markets so the frontend knows their status
for mkt, reason in mapping.get("unmatched", {}).items():
    snapshot[mkt] = {"bfs_name": None, "bfs_code": None, "series": {}, "summary_12m": None, "seasonality": None, "no_bfs_reason": reason}

meta_out = {
    "source": "BFS STAT-TAB px-x-1003020000_201 (HESTA Hotellerie)",
    "source_url": "https://www.pxweb.bfs.admin.ch/pxweb/de/px-x-1003020000_101/-/px-x-1003020000_101.px/",
    "indicators": WANT_INDICATORS,
    "years": WANT_YEARS,
    "fetched_at": data.get("updated") or data.get("extension", {}).get("px", {}).get("updated", "unknown"),
    "covered_markets": sum(1 for m in snapshot.values() if m.get("bfs_code")),
    "total_markets": len(snapshot),
    "note": "HESTA enthält nur Hotellerie, keine Parahotellerie/Ferienwohnungen. Verwendet als verifizierter Proxy für STR-Nachfrage und Saisonalität.",
}

out = {"_meta": meta_out, "markets": snapshot}
Path("../data/hesta-snapshot.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
print(f"\nSaved data/hesta-snapshot.json")
print(f"Coverage: {meta_out['covered_markets']}/{meta_out['total_markets']} markets with BFS data")

# Quick sanity: print 3 sample summaries
print("\n=== Sample summaries ===")
for mkt in ["Zermatt", "Verbier", "Zürich"]:
    if mkt in snapshot and snapshot[mkt].get("summary_12m"):
        s = snapshot[mkt]["summary_12m"]
        print(f"{mkt:15} ({snapshot[mkt]['bfs_name']:20}) — Occ {s['avg_occupancy_pct']}%, Nights {s['total_nights_12m']:,}, Beds {s['avg_beds']}, Betriebe {s['avg_betriebe']}")
