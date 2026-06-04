# SwissSTR + SwissHomePartner — Offene Aufgaben (Continuation-Prompt)

> Copy-paste alles ab `--- BEGIN ---` in einen neuen Chat. Erledigt heute: v0.9.26 → v0.9.42.
> Diese Liste ist die vollständige Wiedervorlage aller heutigen Aufgaben — inkl. der Punkte,
> die im schnellen Hin-und-Her durchgerutscht sind.

--- BEGIN ---

# KONTEXT

Zwei Projekte von Adrian (Schweizer, kein Dev, iPhone-first, 7 J. Airbnb-Superhost):
- **SwissSTR** (`C:\Users\adria\Claude\swissstr`, github Adrianmaagg/swissstr, live adrianmaagg.github.io/swissstr) — Analyse-Tool „was lohnt sich". Single-File `index.html`. CLAUDE.md beachten (durchziehen, commit+push main, de-CH, Daten-Tier 🟢BFS/🟡MOD/🔴MOCK, Browser-Verify via Preview, Commit `vX.Y.Z — …`).
- **SwissHomePartner / heimstatt** (`C:\Users\adria\Claude\heimstatt`, github Adrianmaagg/heimstatt privat) — Akquise/„Doing"-Tool.

**Roter Faden aller offenen Punkte:** Zahlen müssen *konsistent, hergeleitet (Proof), ehrlich getiert und in klarer Einheit* sein. Nichts Fake-„echt", keine Blackbox-Zahl, keine scheindynamischen Karten. Lieber optimieren als löschen.

Browser-Verify: Preview-Config liegt in `swissstr/.claude/launch.json` (Name `swissstr`, Port 8765). Falls der Preview-Server die Parent-`.claude/launch.json` liest (nur „dmaic"), temporär einen `swissstr-verify`-Eintrag (`--directory C:/Users/adria/Claude/swissstr`, Port 8766) ergänzen und danach revertieren.

---

# ⭐ PRIORITÄT 1 — DIE WURZEL: Rechen-Engine konsolidieren (SwissSTR)

**Problem:** Dieselbe Kennzahl wird an 5+ Stellen unterschiedlich gerechnet → widersprüchliche Zahlen. Konkret (alles Zermatt): Konkurrenz-Analyse Top-10% = **196'799**, Revenue-Verteilung (KPI-Modal) Top-10% = **169k+**; Median 47'794 vs 67k. Das ist der „die Zahlen stimmen nicht / muss überprüft werden"-Kern.

**Aufgabe:** EINE zentrale Funktion `marketEconomics(m, größe)` (eine Quelle, ein Annahmen-Satz):
- ADR, Auslastung (BFS wo vorhanden), Brutto-Umsatz, **Netto-Cashflow inkl. Aufenthaltsdauer + Reinigungs-Wechsel**, Werte in **Tag / Monat / Jahr**, Tiers **Top-10% / Median / Bottom-30%** mit sichtbaren Multiplikatoren.
- Alle Views ziehen daraus + zeigen **denselben Proof**: Earn-Card, Konkurrenz-Analyse (`computeMarketCompetition`), Revenue-Verteilung (KPI-Modal), `cfEst` (Such-Strategien), `genProperty` (Scout-Karten), „Bester Cashflow-Markt", „Markt im Fokus", Edge-Score-Arbitrage.
- Danach: keine Widersprüche mehr, Einheiten überall konsistent, jede Zahl nachvollziehbar.
- Voll verifizieren (mehrere Märkte: Zermatt/Winterthur/Zug), keine Konsolenfehler.

**Mitprüfen:** Verdacht Eigenkapital vs. Preis — Scout-Beispielkarte sagt im Text „CHF 955k **Eigenkapital**", das Preis-Tag zeigt aber denselben Wert (`genProperty`: equity = price×0.25). Klären/fixen.

**Auch hierher gehört (war separater Wunsch):** Aufenthaltsdauer/Reinigung + Jahr/Monat-Einheit konsistent **überall** (Earn-Card hat's via Slider v0.9.32; Investor-Calc + Modal noch nicht). Über die Engine lösen.

---

# PRIORITÄT 2 — Layout / UX (SwissSTR)

1. **KPI-/Saisonalität-/Revenue-Verteilungs-Block direkt unter „Wer übernachtet hier" (Markt-Chancen-Scout)** platzieren. (Scout wurde v0.9.38 über die Warn-Panels gezogen; dieser Charts-Block soll direkt darunter.) — *Verifizieren ob schon so; sonst umsortieren.*
2. **Edge-Ranking: Perlen stärker begründen/vermarkten.** „Das sind die Perlen, aber schwach begründet für den Platz." Pro Top-Markt eine klare, konkrete Warum-Begründung (nicht nur die Treiber-Zahlen).
3. **Such-Strategien: Begründungs-Argumente konkreter** („deine Argumente schwach"). Die `reason`-Texte schärfen, weniger Floskel.

---

# PRIORITÄT 3 — Bug (SwissSTR)

4. **Modal „RevPAR — Saisonalität, Verteilung & Bewertung" (KPI-Drill, 2. Bild): Filter teilweise nicht klickbar.** Interaktion im Modal reparieren (Klick-Targets / z-index / Event-Binding prüfen).

---

# PRIORITÄT 4 — Klartext / kleinere Fixes (SwissSTR)

5. **Google-Quick-Search-Buttons** (Konkurrenz-Recherche) klar als „öffnet Google-Suche" kennzeichnen.
6. **Volle Gemeinde-Liste** für Wohnort-Autocomplete: `tools/fetch_communes.py` laufen lassen, sobald Wikidata wieder antwortet (war 429/Outage). Aktuell Bootstrap (93 Gemeinden, Baar drin). Monats-Action holt es sonst nach.

---

# PRIORITÄT 5 — Strategisch / Future (SwissSTR)

7. **AirDNA / echte STR-Daten** evaluieren als Quelle für ADR/Occ (löst die 🔴-MOCK-Decke, die alle Profit-Zahlen unsicher macht). Hinweis: in CLAUDE.md aktuell als Do-Not-Do gelistet — bewusste Entscheidung von Adrian nötig (Kosten/Unabhängigkeit). SOTA-Tools (AirDNA Rentalizer, Airbtics) decken CH-Städte ab und sind genauer als das Modell.
8. **Channel-Map interaktiv** — anwählbar, welche Gäste über welche Plattform zu welchem % buchen; eigenes Angebot aufschalten. Gehört zu „Recherche Konkurrenz / Angebote einsehen". Eigene Baustelle.
9. **Phase 5 Forward-Log** — Edge-Hypothesen mit Ablaufdatum gegen eintreffende Realität prüfen (Kalibrierung über Zeit). Backtest existiert (51% Momentum-Hit, ehrlich schwach).

---

# SwissHomePartner / heimstatt — OFFEN

Architektur-Entscheid (Adrian): **„Cockpit + Engine"** — Engine (Python, 121 Tests grün) bleibt headless; das Interface muss iPhone-first sein. Reihenfolge: Finden → Bewerten → Anschreiben. Senden bleibt manuell (Auto-Send OFF).

10. **Finden (teilweise erledigt):** Suchagent-Mail-Parser via IMAP gebaut + an echter newhome-Mail kalibriert (v1.1.1). OFFEN: an echter **Homegate/ImmoScout-Wohn-Suchabo-Mail** kalibrieren (Adrian legt Wohn-Abos in Greenlist-Gemeinden an, leitet 1 Mail weiter).
11. **Cockpit (iPhone-Web)** bauen: pro Inserat „Lohnt-Ampel + Zahlen + Wer inseriert + fertiger Anschreib-Text zum Kopieren + Inserat öffnen". Kontakt: Verwaltung via Zefix direkt; Privat via Portal-Formular (Text kopieren). 
12. **Bewertungs-Kriterien:** SwissSTR-Marktdaten als JSON-Feed in den heimstatt-Scorer (statt 23 Gemeinden hardcoded). Reingewinn-Schwelle: Adrian justiert aus echten Zahlen (Default-Anzeige Reingewinn, Schwelle später).
13. **.env + Live-IMAP** (Outlook App-Password) durchexerzieren.
14. **Anschreiben-Qualität / Composer** schärfen.
15. **Inbound-Website (Tool 3)** — Vermieter melden sich bei dir (SOTA-Endspiel, vgl. Zi-Find US). Skaliert besser als Kalt-Pitch.

---

# ARBEITSWEISE

- Pro Aufgabe: kleinster sinnvoller Schnitt, Browser-Verify (keine Konsolenfehler, Werte plausibel), commit + push main, knappe Statusmeldung.
- Bei Zahlen IMMER: Herleitung sichtbar + Tier + Einheit. Keine Fake-„VERIFIED"/„HEUTE"/„Wöchentlich" ohne echte Logik.
- Priorität 1 (Konsolidierung) zuerst — sie löst mehrere andere Punkte strukturell.

--- END ---
