#!/usr/bin/env python3
"""
fetch_competitors.py — automatische STR-Konkurrenz-Recherche pro Markt via Brave Search API.

Pro Markt: 3 Queries (Business Apartments, möbliert wohnen, Coworking) → parsed Top-Results
→ schreibt data/competitors.json + updated _health.json.

Setup:
  1. Brave-Account erstellen: https://brave.com/search/api/
  2. API Token in Environment-Variable BRAVE_SEARCH_TOKEN setzen
  3. Lokal: python tools/fetch_competitors.py
  4. GitHub Actions: Token als Repo-Secret BRAVE_SEARCH_TOKEN setzen

Pricing:
  - Free Tier: 2'000 Queries/Monat → reicht für 197 Märkte × 3 Queries = 591/Monat
  - Base Tier: $3 / 1'000 Queries (falls Skalierung)

Risiko-Profil (Adrian's Filter):
  - Brave API ist stabil (Anbieter seit 2021, Suchmaschine seit 2023)
  - Rate-Limit: 1 query/sec im Free-Tier
  - Bei API-Abriss: letzte competitors.json bleibt im Repo, _health.json zeigt error
  - Schema-Stabilität: web.results[].{title,url,description} ist Standard-Format
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BRAVE_TOKEN = os.environ.get("BRAVE_SEARCH_TOKEN")
ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data"))
OUT_FILE = os.path.join(DATA_DIR, "competitors.json")
HEALTH_FILE = os.path.join(DATA_DIR, "_health.json")
MARKETS_FILE = os.path.join(DATA_DIR, "hesta-snapshot.json")  # Markt-Liste aus HESTA

# 3 Queries pro Markt — fokussiert auf direkte STR-Konkurrenz
QUERY_TEMPLATES = [
    {"slug": "business_apt", "tmpl": "Business Apartments {market}", "category": "Möbliert STR / Aparthotel"},
    {"slug": "moebliert", "tmpl": "möblierte Wohnung {market}", "category": "Möbliert mid-term"},
    {"slug": "coworking", "tmpl": "Coworking {market}", "category": "Coworking / Hybrid"},
]

# Domains die rausgefiltert werden (Aggregatoren, Listings-Portale die selber nicht Konkurrenz sind)
EXCLUDE_DOMAINS = {
    "wikipedia.org", "wikidata.org", "tripadvisor.com", "tripadvisor.ch",
    "google.com", "google.ch", "facebook.com", "instagram.com",
    "linkedin.com", "youtube.com", "tiktok.com",
    "homegate.ch", "immoscout24.ch", "comparis.ch", "newhome.ch",  # Listing-Plattformen
    "yelp.com", "yelp.ch",
}

def search_brave(query, retries=2):
    """Brave Search API call. Returns parsed results or raises."""
    if not BRAVE_TOKEN:
        raise RuntimeError("BRAVE_SEARCH_TOKEN env var nicht gesetzt. Siehe Docstring.")
    params = urllib.parse.urlencode({
        "q": query,
        "count": 10,
        "country": "ch",
        "search_lang": "de",
        "result_filter": "web",
    })
    url = f"{ENDPOINT}?{params}"
    req = urllib.request.Request(url, headers={
        "X-Subscription-Token": BRAVE_TOKEN,
        "Accept": "application/json",
        "User-Agent": "SwissSTR-Intelligence/0.9 (+https://github.com/Adrianmaagg/swissstr)",
    })
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                raise

def domain_of(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""

def parse_results(raw, category):
    """Brave-Response → flat competitor records."""
    out = []
    web = raw.get("web", {})
    for item in web.get("results", [])[:8]:
        url = item.get("url", "")
        domain = domain_of(url)
        if not url or domain in EXCLUDE_DOMAINS:
            continue
        # Skip if domain looks like aggregator/news
        if any(skip in domain for skip in ["news", "blog", "magazin"]):
            continue
        out.append({
            "name": item.get("title", "").strip()[:120],
            "url": url,
            "domain": domain,
            "category": category,
            "snippet": (item.get("description", "") or "").strip()[:200],
        })
    return out

def dedup_by_domain(records):
    """Wenn gleiche Domain mehrfach (durch verschiedene Queries): behalte ersten Match."""
    seen, kept = set(), []
    for r in records:
        if r["domain"] in seen:
            continue
        seen.add(r["domain"])
        kept.append(r)
    return kept

def load_market_names():
    """Markt-Liste aus hesta-snapshot.json."""
    with open(MARKETS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return sorted(data.get("markets", {}).keys())

def fetch_for_market(name):
    """3 Queries für einen Markt, dedup nach Domain."""
    all_results = []
    for qt in QUERY_TEMPLATES:
        q = qt["tmpl"].format(market=name)
        try:
            raw = search_brave(q)
            all_results.extend(parse_results(raw, qt["category"]))
        except Exception as e:
            print(f"  WARN: query '{q}' failed: {e}", file=sys.stderr)
        time.sleep(1.1)  # Brave Free-Tier: 1 query/sec
    return dedup_by_domain(all_results)[:8]  # max 8 pro Markt

def write_outputs(competitors):
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "_meta": {
            "source": "Brave Search API (3 Queries pro Markt: Business Apartments, möbliert wohnen, Coworking)",
            "source_url": ENDPOINT,
            "license": "Brave Search ToS · Results: jeweilige Anbieter",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "covered_markets": len([k for k, v in competitors.items() if v]),
            "total_markets": len(competitors),
            "queries_per_market": 3,
            "note": "Automatisch detektierte STR-Konkurrenten pro Markt. Wird vom Frontend mit hardcoded COMPETITOR_LISTS (Bootstrap mit Notes) gemerged.",
        },
        "competitors": competitors,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Wrote competitors for {payload['_meta']['covered_markets']}/{payload['_meta']['total_markets']} markets to {OUT_FILE}")

def update_health(status, error=None, queries_used=None):
    if not os.path.exists(HEALTH_FILE):
        print("WARN: _health.json missing, skipping health update")
        return
    with open(HEALTH_FILE, "r", encoding="utf-8") as f:
        health = json.load(f)
    health.setdefault("sources", {})
    entry = health["sources"].setdefault("competitors_brave", {
        "name": "STR-Konkurrenten pro Markt (Brave Search API)",
        "url": ENDPOINT,
        "snapshot_file": "data/competitors.json",
        "expected_frequency": "monthly",
        "note": "Brave Search API mit Free-Tier 2'000 Queries/Mt → reicht für 197 Märkte × 3 Queries = 591/Mt. Bei API-Abriss bleibt letzte Snapshot intakt + Frontend zeigt nur hardcoded Bootstrap-Liste.",
    })
    now = datetime.now(timezone.utc).isoformat()
    entry["last_attempt"] = now
    if status == "ok":
        entry["last_success"] = now
        entry["status"] = "ok"
        entry.pop("error", None)
        if queries_used:
            entry["queries_last_run"] = queries_used
    else:
        entry["status"] = "error"
        if error:
            entry["error"] = error
    health["generated_at"] = now
    with open(HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump(health, f, ensure_ascii=False, indent=2)

def main():
    if not BRAVE_TOKEN:
        print("ERROR: BRAVE_SEARCH_TOKEN env var nicht gesetzt.", file=sys.stderr)
        print("Setup: https://brave.com/search/api/ → Token kopieren → export BRAVE_SEARCH_TOKEN=...", file=sys.stderr)
        update_health("error", "BRAVE_SEARCH_TOKEN not set")
        return 1

    try:
        markets = load_market_names()
        # Limit: nur Märkte mit relevanter Listings-Anzahl (vermeidet Verschwendung von Queries)
        # In Vollausbau: alle 197 Märkte. Aktuell: erste 50 als Beispiel.
        limit = int(os.environ.get("COMPETITORS_LIMIT", "60"))
        markets_to_fetch = markets[:limit]
        print(f"Fetching competitors for {len(markets_to_fetch)} markets (Brave Search API)...")

        competitors = {}
        queries_used = 0
        t0 = time.time()
        for idx, name in enumerate(markets_to_fetch, 1):
            print(f"[{idx}/{len(markets_to_fetch)}] {name}")
            try:
                competitors[name] = fetch_for_market(name)
                queries_used += 3
            except Exception as e:
                print(f"  FAILED for {name}: {e}", file=sys.stderr)
                competitors[name] = []

        write_outputs(competitors)
        update_health("ok", queries_used=queries_used)
        elapsed = time.time() - t0
        print(f"OK — {queries_used} queries in {elapsed:.0f}s for {len(competitors)} markets")
        return 0

    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        update_health("error", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
