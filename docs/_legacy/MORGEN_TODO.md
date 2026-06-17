# Morgen früh — 3 Klicks, max 2 Minuten

Dies ist eine private Notiz. Nach Erledigung löschen (`rm MORGEN_TODO.md`).

## 1. swissstr-Repo auf privat stellen (30 Sek)

Browser → https://github.com/Adrianmaagg/swissstr/settings
→ ganz unten **Danger Zone**
→ **Change repository visibility** → **Make private**
→ Bestätigen mit `Adrianmaagg/swissstr`

**Sofortige Folge:** `https://adrianmaagg.github.io/swissstr/` → 404 (GitHub
Pages funktioniert nicht mit private free-tier).

## 2. Cloudflare-Berechtigung erweitern (1 Min)

Cloudflare-Dashboard → Pages → swissstr → Settings
→ **GitHub-Integration → Manage GitHub permissions**
→ landet bei GitHub → **Only select repositories** → `swissstr` aktivieren
→ zurück bei Cloudflare → falls letzter Build failed: **Retry deployment**

## 3. (Optional) Live-Site mit Cloudflare Access schützen (3 Min)

Nur wenn auch `swissstr.pages.dev` für Außenstehende unsichtbar sein soll:

Cloudflare → **Zero Trust** (linke Seitenleiste, oben)
→ wenn nötig Account aktivieren (gratis bis 50 User)
→ **Access → Applications → Add an application → Self-hosted**
→ Domain: `swissstr.pages.dev`
→ Policy: **Allow** → Rule **Emails** → `adrian.maag@hotmail.com`
→ Speichern

Ab dann: Aufruf swissstr.pages.dev → Email mit Magic-Link → klicken → drin.

## Verifikation

Nach Schritt 1+2:
- https://github.com/Adrianmaagg/swissstr → öffentlich erreichbar? Sollte NEIN sein
- Logout-Test: in Inkognito-Tab öffnen → "Page not found" = korrekt

## Lokal vorbereitet während du geschlafen hast

- `CLAUDE.md`: Privacy-Default für künftige Repos dokumentiert (private = default)
- Diese Notiz: `MORGEN_TODO.md` (nicht committet)

Keine Code-Änderungen, kein git-Push gemacht. Du entscheidest morgen.
